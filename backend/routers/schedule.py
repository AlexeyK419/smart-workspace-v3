from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
import models
import schemas

router = APIRouter(prefix="/schedule", tags=["schedule"])


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
def list_schedule_events(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.ScheduleEvent)
        .filter(models.ScheduleEvent.user_id == current_user.id)
        .order_by(models.ScheduleEvent.day_index.asc(), models.ScheduleEvent.start_minute.asc())
        .all()
    )


@router.post("/", response_model=schemas.ScheduleEventOut, status_code=201)
def create_schedule_event(
    payload: schemas.ScheduleEventCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = models.ScheduleEvent(user_id=current_user.id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.patch("/{event_id}", response_model=schemas.ScheduleEventOut)
def update_schedule_event(
    event_id: int,
    payload: schemas.ScheduleEventUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _get_event_or_404(current_user.id, event_id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
def delete_schedule_event(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _get_event_or_404(current_user.id, event_id, db)
    db.delete(event)
    db.commit()
