from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from auth import compute_initials, get_current_user, hash_password, verify_password
from database import get_db
import models
import schemas

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def get_current_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UserOut)
def update_current_profile(
    payload: schemas.UserProfileUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = payload.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Имя должно содержать минимум 2 символа")

    current_user.name = name
    current_user.initials = compute_initials(name)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password", status_code=204)
def update_current_password(
    payload: schemas.UserPasswordUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_salt, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Текущий пароль указан неверно")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="Новый пароль должен отличаться от текущего")

    salt, password_hash = hash_password(payload.new_password)
    current_user.password_salt = salt
    current_user.password_hash = password_hash
    db.commit()


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
