from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from auth import get_current_user, get_user_by_token
from database import SessionLocal, get_db
import models
import schemas

router = APIRouter(prefix="/chats", tags=["chats"])
ws_router = APIRouter(prefix="/ws/chats", tags=["chats-ws"])


class DirectChatConnectionManager:
    def __init__(self):
        self.active: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        clients = self.active.get(user_id)
        if not clients:
            return
        clients.discard(websocket)
        if not clients:
            self.active.pop(user_id, None)

    async def broadcast_to_user(self, user_id: int, payload: dict, exclude: WebSocket | None = None):
        dead: list[WebSocket] = []
        for websocket in list(self.active.get(user_id, set())):
            if exclude is not None and websocket is exclude:
                continue
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(user_id, websocket)


chat_manager = DirectChatConnectionManager()


def _chat_query(db: Session):
    return db.query(models.DirectChat).options(
        selectinload(models.DirectChat.first_user),
        selectinload(models.DirectChat.second_user),
        selectinload(models.DirectChat.participants).selectinload(models.DirectChatParticipant.user),
    )


def _message_query(db: Session):
    return db.query(models.DirectMessage).options(selectinload(models.DirectMessage.sender))


def _pair_ids(current_user_id: int, target_user_id: int) -> tuple[int, int]:
    if current_user_id == target_user_id:
        raise HTTPException(status_code=400, detail="Нельзя создать личный чат с самим собой")
    return tuple(sorted((current_user_id, target_user_id)))


def _get_chat_for_user_or_404(chat_id: int, user_id: int, db: Session) -> models.DirectChat:
    chat = (
        _chat_query(db)
        .join(models.DirectChatParticipant, models.DirectChatParticipant.chat_id == models.DirectChat.id)
        .filter(models.DirectChat.id == chat_id, models.DirectChatParticipant.user_id == user_id)
        .first()
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat


def _get_chat_by_id_or_404(chat_id: int, db: Session) -> models.DirectChat:
    chat = _chat_query(db).filter(models.DirectChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat


def _get_message_or_404(message_id: int, db: Session) -> models.DirectMessage:
    message = _message_query(db).filter(models.DirectMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    return message


def _get_participants(chat_id: int, db: Session) -> list[models.DirectChatParticipant]:
    return (
        db.query(models.DirectChatParticipant)
        .options(selectinload(models.DirectChatParticipant.user))
        .filter(models.DirectChatParticipant.chat_id == chat_id)
        .all()
    )


def _participant_for_user(chat_id: int, user_id: int, db: Session) -> models.DirectChatParticipant:
    participant = (
        db.query(models.DirectChatParticipant)
        .filter(
            models.DirectChatParticipant.chat_id == chat_id,
            models.DirectChatParticipant.user_id == user_id,
        )
        .first()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return participant


def _peer_user(chat: models.DirectChat, user_id: int) -> models.User:
    if chat.first_user_id == user_id:
        return chat.second_user
    if chat.second_user_id == user_id:
        return chat.first_user
    raise HTTPException(status_code=404, detail="Чат не найден")


def _message_payload(message: models.DirectMessage) -> dict:
    return jsonable_encoder(schemas.DirectMessageOut.model_validate(message, from_attributes=True))


def _chat_payload(chat: models.DirectChat, user_id: int, db: Session) -> dict:
    participant = _participant_for_user(chat.id, user_id, db)
    last_message = (
        _message_query(db)
        .filter(models.DirectMessage.chat_id == chat.id)
        .order_by(models.DirectMessage.created_at.desc(), models.DirectMessage.id.desc())
        .first()
    )

    unread_query = (
        db.query(func.count(models.DirectMessage.id))
        .filter(models.DirectMessage.chat_id == chat.id)
        .filter(models.DirectMessage.sender_id != user_id)
    )
    if participant.last_read_at:
        unread_query = unread_query.filter(models.DirectMessage.created_at > participant.last_read_at)

    payload = schemas.DirectChatOut(
        id=chat.id,
        first_user_id=chat.first_user_id,
        second_user_id=chat.second_user_id,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        peer=schemas.UserOut.model_validate(_peer_user(chat, user_id), from_attributes=True),
        last_message=(
            schemas.DirectMessageOut.model_validate(last_message, from_attributes=True)
            if last_message
            else None
        ),
        unread_count=unread_query.scalar() or 0,
    )
    return jsonable_encoder(payload)


def _create_message(chat_id: int, sender_id: int, body: str, db: Session) -> models.DirectMessage:
    chat = _get_chat_for_user_or_404(chat_id, sender_id, db)
    text = body.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Сообщение не должно быть пустым")

    now = datetime.utcnow()
    chat.updated_at = now
    _participant_for_user(chat.id, sender_id, db).last_read_at = now

    message = models.DirectMessage(chat_id=chat.id, sender_id=sender_id, body=text, created_at=now)
    db.add(message)
    db.commit()
    return _get_message_or_404(message.id, db)


def _mark_chat_read(chat_id: int, user_id: int, db: Session) -> models.DirectChat:
    chat = _get_chat_for_user_or_404(chat_id, user_id, db)
    _participant_for_user(chat.id, user_id, db).last_read_at = datetime.utcnow()
    db.commit()
    return _get_chat_for_user_or_404(chat_id, user_id, db)


async def _broadcast_message_created(chat_id: int, message: models.DirectMessage, db: Session):
    chat = _get_chat_by_id_or_404(chat_id, db)
    message_data = _message_payload(message)
    for participant in _get_participants(chat.id, db):
        await chat_manager.broadcast_to_user(participant.user_id, {
            "type": "message.created",
            "chat_id": chat.id,
            "message": message_data,
            "chat": _chat_payload(chat, participant.user_id, db),
        })


async def _broadcast_chat_updated(chat_id: int, user_id: int, db: Session):
    chat = _get_chat_for_user_or_404(chat_id, user_id, db)
    await chat_manager.broadcast_to_user(user_id, {
        "type": "chat.updated",
        "chat_id": chat.id,
        "chat": _chat_payload(chat, user_id, db),
    })


@router.get("/", response_model=list[schemas.DirectChatOut])
def list_chats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    last_message_at = (
        db.query(func.max(models.DirectMessage.created_at))
        .filter(models.DirectMessage.chat_id == models.DirectChat.id)
        .correlate(models.DirectChat)
        .scalar_subquery()
    )
    chats = (
        _chat_query(db)
        .join(models.DirectChatParticipant, models.DirectChatParticipant.chat_id == models.DirectChat.id)
        .filter(models.DirectChatParticipant.user_id == current_user.id)
        .order_by(func.coalesce(last_message_at, models.DirectChat.updated_at).desc())
        .all()
    )
    return [_chat_payload(chat, current_user.id, db) for chat in chats]


@router.post("/", response_model=schemas.DirectChatOut, status_code=201)
def create_or_get_chat(
    payload: schemas.DirectChatCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user = db.query(models.User).filter(models.User.id == payload.target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    first_id, second_id = _pair_ids(current_user.id, target_user.id)
    chat = (
        _chat_query(db)
        .filter(models.DirectChat.first_user_id == first_id, models.DirectChat.second_user_id == second_id)
        .first()
    )
    if chat:
        return _chat_payload(chat, current_user.id, db)

    now = datetime.utcnow()
    chat = models.DirectChat(
        first_user_id=first_id,
        second_user_id=second_id,
        created_at=now,
        updated_at=now,
    )
    db.add(chat)
    db.flush()
    db.add_all([
        models.DirectChatParticipant(chat_id=chat.id, user_id=first_id, last_read_at=now),
        models.DirectChatParticipant(chat_id=chat.id, user_id=second_id, last_read_at=now),
    ])
    db.commit()

    saved = _get_chat_for_user_or_404(chat.id, current_user.id, db)
    return _chat_payload(saved, current_user.id, db)


@router.get("/{chat_id}", response_model=schemas.DirectChatOut)
def get_chat(
    chat_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = _get_chat_for_user_or_404(chat_id, current_user.id, db)
    return _chat_payload(chat, current_user.id, db)


@router.get("/{chat_id}/messages", response_model=list[schemas.DirectMessageOut])
def list_messages(
    chat_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_chat_for_user_or_404(chat_id, current_user.id, db)
    return (
        _message_query(db)
        .filter(models.DirectMessage.chat_id == chat_id)
        .order_by(models.DirectMessage.created_at.asc(), models.DirectMessage.id.asc())
        .all()
    )


@router.post("/{chat_id}/messages", response_model=schemas.DirectMessageOut, status_code=201)
async def create_message(
    chat_id: int,
    payload: schemas.DirectMessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = _create_message(chat_id, current_user.id, payload.body, db)
    await _broadcast_message_created(chat_id, message, db)
    return message


@router.post("/{chat_id}/read", response_model=schemas.DirectChatOut)
async def mark_chat_read(
    chat_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = _mark_chat_read(chat_id, current_user.id, db)
    await _broadcast_chat_updated(chat.id, current_user.id, db)
    return _chat_payload(chat, current_user.id, db)


@ws_router.websocket("/")
async def direct_chats_socket(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    db = SessionLocal()
    user = None

    try:
        user = get_user_by_token(token, db)
        if not user:
            await websocket.close(code=4401, reason="auth_required")
            return

        await chat_manager.connect(user.id, websocket)
        await websocket.send_json({"type": "connection.ready", "user_id": user.id})

        while True:
            payload = await websocket.receive_json()
            event_type = (payload.get("type") or "").strip()

            try:
                chat_id = int(payload.get("chat_id") or 0)
                if event_type == "typing":
                    chat = _get_chat_for_user_or_404(chat_id, user.id, db)
                    for participant in _get_participants(chat.id, db):
                        if participant.user_id == user.id:
                            continue
                        await chat_manager.broadcast_to_user(participant.user_id, {
                            "type": "typing",
                            "chat_id": chat.id,
                            "user_id": user.id,
                            "user_name": user.name,
                            "is_typing": bool(payload.get("is_typing")),
                        })
                    continue

                if event_type == "read":
                    chat = _mark_chat_read(chat_id, user.id, db)
                    await _broadcast_chat_updated(chat.id, user.id, db)
                    continue

                if event_type == "message":
                    message = _create_message(chat_id, user.id, str(payload.get("body") or ""), db)
                    await _broadcast_message_created(chat_id, message, db)
                    continue

                await websocket.send_json({"type": "error", "detail": "Unsupported event type"})
            except (HTTPException, ValueError) as exc:
                detail = exc.detail if isinstance(exc, HTTPException) else "Некорректное событие"
                await websocket.send_json({"type": "error", "detail": detail})

    except WebSocketDisconnect:
        pass
    finally:
        if user:
            chat_manager.disconnect(user.id, websocket)
        db.close()
