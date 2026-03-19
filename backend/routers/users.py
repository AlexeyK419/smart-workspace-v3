from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
import models
import schemas

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def get_current_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/me/courses", response_model=list[schemas.CourseOut])
def get_current_user_courses(current_user: models.User = Depends(get_current_user)):
    return current_user.courses


@router.get("/search", response_model=list[schemas.UserOut])
def search_users(
    q: str = Query(default=""),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    term = f"%{q.strip().lower()}%"
    if not q.strip():
        return []

    return (
        db.query(models.User)
        .filter(models.User.id != current_user.id)
        .filter(
            or_(
                func.lower(models.User.name).like(term),
                func.lower(func.coalesce(models.User.email, "")).like(term),
            )
        )
        .order_by(models.User.name.asc())
        .limit(12)
        .all()
    )
