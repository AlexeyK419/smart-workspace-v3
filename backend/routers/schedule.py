from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(prefix="/users/{user_id}/schedule", tags=["schedule"])


def _get_user_or_404(user_id: int, db: Session) -> models.User:
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


def _get_event_or_404(user_id: int, event_id: int, db: Session) -> models.ScheduleEvent:
    event = (
        db.query(models.ScheduleEvent)
        .filter(models.ScheduleEvent.id == event_id, models.ScheduleEvent.user_id == user_id)
        .first()
    )
    if not event:
        raise HTTPException(404, "Schedule event not found")
    return event


@router.get("/", response_model=list[schemas.ScheduleEventOut])
def list_schedule_events(user_id: int, db: Session = Depends(get_db)):
    _get_user_or_404(user_id, db)
    return (
        db.query(models.ScheduleEvent)
        .filter(models.ScheduleEvent.user_id == user_id)
        .order_by(models.ScheduleEvent.day_index.asc(), models.ScheduleEvent.start_minute.asc())
        .all()
    )


@router.post("/", response_model=schemas.ScheduleEventOut, status_code=201)
def create_schedule_event(
    user_id: int,
    payload: schemas.ScheduleEventCreate,
    db: Session = Depends(get_db),
):
    _get_user_or_404(user_id, db)
    event = models.ScheduleEvent(user_id=user_id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.patch("/{event_id}", response_model=schemas.ScheduleEventOut)
def update_schedule_event(
    user_id: int,
    event_id: int,
    payload: schemas.ScheduleEventUpdate,
    db: Session = Depends(get_db),
):
    event = _get_event_or_404(user_id, event_id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
def delete_schedule_event(user_id: int, event_id: int, db: Session = Depends(get_db)):
    event = _get_event_or_404(user_id, event_id, db)
    db.delete(event)
    db.commit()
