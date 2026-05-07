import os
import uuid
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from auth import ensure_project_owner, get_current_user, get_project_for_user_or_404, get_user_by_token
from ai_embeddings import delete_context_chunks
from database import SessionLocal, get_db
from file_utils import read_file_text_raw
import models
import schemas

router = APIRouter(prefix="/projects", tags=["projects"])
ws_router = APIRouter(prefix="/ws/projects", tags=["projects-ws"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "project_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024

MIME_ICONS: dict[str, tuple[str, str]] = {
    "application/pdf": ("📄", "#fee2e2"),
    "application/msword": ("📝", "#dbeafe"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ("📝", "#dbeafe"),
    "application/vnd.ms-powerpoint": ("📊", "#fef9c3"),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ("📊", "#fef9c3"),
    "application/vnd.ms-excel": ("📈", "#d1fae5"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ("📈", "#d1fae5"),
    "text/plain": ("📃", "#f0fdf4"),
    "image/png": ("🖼️", "#d1fae5"),
    "image/jpeg": ("🖼️", "#d1fae5"),
    "image/gif": ("🖼️", "#d1fae5"),
    "video/mp4": ("🎬", "#ede9fe"),
    "audio/mpeg": ("🎵", "#fce7f3"),
    "application/zip": ("📦", "#e0e7ff"),
}


class ProjectChatConnectionManager:
    def __init__(self):
        self.active: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, project_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active[project_id].add(websocket)

    def disconnect(self, project_id: int, websocket: WebSocket):
        clients = self.active.get(project_id)
        if not clients:
            return
        clients.discard(websocket)
        if not clients:
            self.active.pop(project_id, None)

    async def broadcast(self, project_id: int, payload: dict, exclude: WebSocket | None = None):
        dead: list[WebSocket] = []
        for websocket in list(self.active.get(project_id, set())):
            if exclude is not None and websocket is exclude:
                continue
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(project_id, websocket)

    def connection_count(self, project_id: int) -> int:
        return len(self.active.get(project_id, set()))


chat_manager = ProjectChatConnectionManager()


def _project_detail_query(db: Session):
    return db.query(models.Project).options(
        selectinload(models.Project.owner),
        selectinload(models.Project.members).selectinload(models.ProjectMember.user),
        selectinload(models.Project.tasks).selectinload(models.ProjectTask.assignee),
        selectinload(models.Project.tasks).selectinload(models.ProjectTask.creator),
        selectinload(models.Project.tasks).selectinload(models.ProjectTask.comments).selectinload(models.ProjectTaskComment.author),
        selectinload(models.Project.files).selectinload(models.ProjectFile.uploader),
    )


def _task_query(db: Session):
    return db.query(models.ProjectTask).options(
        selectinload(models.ProjectTask.assignee),
        selectinload(models.ProjectTask.creator),
        selectinload(models.ProjectTask.comments).selectinload(models.ProjectTaskComment.author),
    )


def _message_query(db: Session):
    return db.query(models.ProjectMessage).options(selectinload(models.ProjectMessage.author))


def _project_for_member_or_404(project_id: int, user_id: int, db: Session) -> models.Project:
    project = (
        _project_detail_query(db)
        .join(models.ProjectMember, models.ProjectMember.project_id == models.Project.id)
        .filter(models.Project.id == project_id, models.ProjectMember.user_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project


def _ensure_member_belongs_to_project(project_id: int, user_id: int, db: Session):
    membership = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.project_id == project_id, models.ProjectMember.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=400, detail="Пользователь не состоит в проекте")
    return membership


def _validate_assignee(project_id: int, assignee_id: int | None, db: Session):
    if assignee_id is None:
        return
    _ensure_member_belongs_to_project(project_id, assignee_id, db)


def _get_task_or_404(project_id: int, task_id: int, db: Session) -> models.ProjectTask:
    task = _task_query(db).filter(
        models.ProjectTask.id == task_id,
        models.ProjectTask.project_id == project_id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


def _get_message_or_404(project_id: int, message_id: int, db: Session) -> models.ProjectMessage:
    message = _message_query(db).filter(
        models.ProjectMessage.id == message_id,
        models.ProjectMessage.project_id == project_id,
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    return message


def _apply_task_status(task: models.ProjectTask, status: str | None):
    if status is None:
        return
    task.status = status
    if status == "done":
        task.completed_at = task.completed_at or datetime.utcnow()
    else:
        task.completed_at = None
    task.updated_at = datetime.utcnow()


def _serialize_message(message: models.ProjectMessage) -> dict:
    return jsonable_encoder(schemas.ProjectMessageOut.model_validate(message, from_attributes=True))


@router.get("/", response_model=list[schemas.ProjectOut])
def list_projects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        _project_detail_query(db)
        .join(models.ProjectMember, models.ProjectMember.project_id == models.Project.id)
        .filter(models.ProjectMember.user_id == current_user.id)
        .order_by(models.Project.created_at.desc())
        .all()
    )


@router.post("/", response_model=schemas.ProjectOut, status_code=201)
def create_project(
    payload: schemas.ProjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = models.Project(owner_id=current_user.id, **payload.model_dump())
    db.add(project)
    db.flush()

    db.add(models.ProjectMember(project_id=project.id, user_id=current_user.id, role="owner"))
    db.commit()
    return _project_for_member_or_404(project.id, current_user.id, db)


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _project_for_member_or_404(project_id, current_user.id, db)


@router.patch("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    payload: schemas.ProjectUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_project_owner(project_id, current_user.id, db)
    project = get_project_for_user_or_404(project_id, current_user.id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    db.commit()
    return _project_for_member_or_404(project_id, current_user.id, db)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_project_owner(project_id, current_user.id, db)
    project = _project_for_member_or_404(project_id, current_user.id, db)
    for item in project.files:
        if item.file_path and os.path.exists(item.file_path):
            os.remove(item.file_path)
    delete_context_chunks(db, parent_type="project", parent_id=project.id)
    db.delete(project)
    db.commit()


@router.post("/{project_id}/members", response_model=schemas.ProjectOut)
def add_member(
    project_id: int,
    payload: schemas.ProjectMemberAddRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_project_owner(project_id, current_user.id, db)
    _project_for_member_or_404(project_id, current_user.id, db)

    target_user = None
    if payload.user_id is not None:
        target_user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    elif payload.email:
        target_user = (
            db.query(models.User)
            .filter(func.lower(models.User.email) == payload.email.strip().lower())
            .first()
        )
    else:
        raise HTTPException(status_code=400, detail="Укажите пользователя по id или email")

    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    existing = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.project_id == project_id, models.ProjectMember.user_id == target_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже добавлен в проект")

    db.add(models.ProjectMember(project_id=project_id, user_id=target_user.id, role="member"))
    db.commit()
    return _project_for_member_or_404(project_id, current_user.id, db)


@router.delete("/{project_id}/members/{member_id}", response_model=schemas.ProjectOut)
def remove_member(
    project_id: int,
    member_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_project_owner(project_id, current_user.id, db)
    membership = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.id == member_id, models.ProjectMember.project_id == project_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Участник не найден")
    if membership.role == "owner":
        raise HTTPException(status_code=400, detail="Нельзя удалить владельца проекта")

    db.query(models.ProjectTask).filter(
        models.ProjectTask.project_id == project_id,
        models.ProjectTask.assignee_id == membership.user_id,
    ).update({models.ProjectTask.assignee_id: None, models.ProjectTask.updated_at: datetime.utcnow()})
    db.delete(membership)
    db.commit()
    return _project_for_member_or_404(project_id, current_user.id, db)


@router.get("/{project_id}/messages", response_model=list[schemas.ProjectMessageOut])
def list_messages(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    return (
        _message_query(db)
        .filter(models.ProjectMessage.project_id == project_id)
        .order_by(models.ProjectMessage.created_at.asc())
        .all()
    )


@router.post("/{project_id}/messages", response_model=schemas.ProjectMessageOut, status_code=201)
async def create_message(
    project_id: int,
    payload: schemas.ProjectMessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Сообщение не должно быть пустым")
    message = models.ProjectMessage(
        project_id=project_id,
        author_id=current_user.id,
        body=body,
    )
    db.add(message)
    db.commit()
    saved = _get_message_or_404(project_id, message.id, db)
    await chat_manager.broadcast(project_id, {"type": "message.created", "message": _serialize_message(saved)})
    return saved


@router.post("/{project_id}/tasks", response_model=schemas.ProjectTaskOut, status_code=201)
def create_task(
    project_id: int,
    payload: schemas.ProjectTaskCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    _validate_assignee(project_id, payload.assignee_id, db)
    task = models.ProjectTask(
        project_id=project_id,
        created_by_id=current_user.id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        assignee_id=payload.assignee_id,
    )
    _apply_task_status(task, payload.status or "todo")
    db.add(task)
    db.commit()
    return _get_task_or_404(project_id, task.id, db)


@router.patch("/{project_id}/tasks/{task_id}", response_model=schemas.ProjectTaskOut)
def update_task(
    project_id: int,
    task_id: int,
    payload: schemas.ProjectTaskUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    task = _get_task_or_404(project_id, task_id, db)

    updates = payload.model_dump(exclude_unset=True)
    if "assignee_id" in updates:
        _validate_assignee(project_id, updates["assignee_id"], db)

    for field, value in updates.items():
        if field == "status":
            continue
        setattr(task, field, value)

    if "status" in updates:
        _apply_task_status(task, updates["status"])
    else:
        task.updated_at = datetime.utcnow()
    db.commit()
    return _get_task_or_404(project_id, task.id, db)


@router.post("/{project_id}/tasks/{task_id}/comments", response_model=schemas.ProjectTaskCommentOut, status_code=201)
def create_task_comment(
    project_id: int,
    task_id: int,
    payload: schemas.ProjectTaskCommentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    task = _get_task_or_404(project_id, task_id, db)
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Комментарий не должен быть пустым")

    comment = models.ProjectTaskComment(task_id=task.id, author_id=current_user.id, body=body)
    task.updated_at = datetime.utcnow()
    db.add(comment)
    db.commit()
    return (
        db.query(models.ProjectTaskComment)
        .options(selectinload(models.ProjectTaskComment.author))
        .filter(models.ProjectTaskComment.id == comment.id)
        .first()
    )


@router.delete("/{project_id}/tasks/{task_id}", status_code=204)
def delete_task(
    project_id: int,
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    task = _get_task_or_404(project_id, task_id, db)
    delete_context_chunks(db, entity_type="project_task", entity_id=task.id)
    db.delete(task)
    db.commit()


@router.get("/{project_id}/files", response_model=list[schemas.ProjectFileOut])
def list_files(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    return (
        db.query(models.ProjectFile)
        .options(selectinload(models.ProjectFile.uploader))
        .filter(models.ProjectFile.project_id == project_id)
        .order_by(models.ProjectFile.created_at.desc())
        .all()
    )


@router.post("/{project_id}/files", response_model=schemas.ProjectFileOut, status_code=201)
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    ext = os.path.splitext(file.filename or "file")[1]
    disk_name = f"{uuid.uuid4().hex}{ext}"
    disk_path = os.path.join(UPLOAD_DIR, disk_name)
    with open(disk_path, "wb") as fh:
        fh.write(contents)

    mime = file.content_type or "application/octet-stream"
    icon, bg = MIME_ICONS.get(mime, ("📎", "#e2e8f0"))
    item = models.ProjectFile(
        project_id=project_id,
        uploader_id=current_user.id,
        name=file.filename or disk_name,
        file_path=disk_path,
        size_bytes=len(contents),
        mime_type=mime,
        icon=icon,
        icon_bg=bg,
    )
    db.add(item)
    db.commit()
    return (
        db.query(models.ProjectFile)
        .options(selectinload(models.ProjectFile.uploader))
        .filter(models.ProjectFile.id == item.id)
        .first()
    )


@router.get("/{project_id}/files/{file_id}/download")
def download_file(
    project_id: int,
    file_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    item = (
        db.query(models.ProjectFile)
        .filter(models.ProjectFile.id == file_id, models.ProjectFile.project_id == project_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Файл проекта не найден")
    if not os.path.exists(item.file_path):
        raise HTTPException(status_code=404, detail="Файл отсутствует на диске")
    return FileResponse(item.file_path, filename=item.name, media_type=item.mime_type)


@router.get("/{project_id}/files/{file_id}/preview")
def preview_file(
    project_id: int,
    file_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _project_for_member_or_404(project_id, current_user.id, db)
    item = (
        db.query(models.ProjectFile)
        .filter(models.ProjectFile.id == file_id, models.ProjectFile.project_id == project_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Файл проекта не найден")
    text, state = read_file_text_raw(item.file_path)
    if not text:
        raise HTTPException(status_code=400, detail=state)
    return {"text": text, "name": item.name, "mime_type": item.mime_type}


@router.delete("/{project_id}/files/{file_id}", status_code=204)
def delete_file(
    project_id: int,
    file_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _project_for_member_or_404(project_id, current_user.id, db)
    item = (
        db.query(models.ProjectFile)
        .filter(models.ProjectFile.id == file_id, models.ProjectFile.project_id == project_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Файл проекта не найден")

    current_membership = next((member for member in project.members if member.user_id == current_user.id), None)
    is_owner = current_membership and current_membership.role == "owner"
    if item.uploader_id != current_user.id and not is_owner:
        raise HTTPException(status_code=403, detail="Удалить файл может загрузивший его участник или владелец проекта")

    if item.file_path and os.path.exists(item.file_path):
        os.remove(item.file_path)
    delete_context_chunks(db, entity_type="project_file", entity_id=item.id)
    db.delete(item)
    db.commit()


@ws_router.websocket("/{project_id}/chat")
async def project_chat_socket(websocket: WebSocket, project_id: int):
    token = websocket.query_params.get("token", "")
    db = SessionLocal()
    user = None

    try:
        user = get_user_by_token(token, db)
        if not user:
            await websocket.close(code=4401, reason="auth_required")
            return

        membership = (
            db.query(models.ProjectMember)
            .filter(models.ProjectMember.project_id == project_id, models.ProjectMember.user_id == user.id)
            .first()
        )
        if not membership:
            await websocket.close(code=4403, reason="forbidden")
            return

        await chat_manager.connect(project_id, websocket)
        await chat_manager.broadcast(project_id, {
            "type": "presence.update",
            "project_id": project_id,
            "connections": chat_manager.connection_count(project_id),
        })
        await websocket.send_json({
            "type": "connection.ready",
            "project_id": project_id,
            "user_id": user.id,
            "connections": chat_manager.connection_count(project_id),
        })

        while True:
            payload = await websocket.receive_json()
            event_type = (payload.get("type") or "").strip()

            if event_type == "typing":
                await chat_manager.broadcast(project_id, {
                    "type": "typing",
                    "project_id": project_id,
                    "user_id": user.id,
                    "user_name": user.name,
                    "is_typing": bool(payload.get("is_typing")),
                }, exclude=websocket)
                continue

            if event_type != "message":
                await websocket.send_json({"type": "error", "detail": "Unsupported event type"})
                continue

            body = str(payload.get("body") or "").strip()
            if not body:
                await websocket.send_json({"type": "error", "detail": "Сообщение не должно быть пустым"})
                continue

            message = models.ProjectMessage(project_id=project_id, author_id=user.id, body=body)
            db.add(message)
            db.commit()
            saved = _get_message_or_404(project_id, message.id, db)
            await chat_manager.broadcast(project_id, {"type": "message.created", "message": _serialize_message(saved)})

    except WebSocketDisconnect:
        pass
    finally:
        chat_manager.disconnect(project_id, websocket)
        if user:
            await chat_manager.broadcast(project_id, {
                "type": "presence.update",
                "project_id": project_id,
                "connections": chat_manager.connection_count(project_id),
            })
        db.close()
