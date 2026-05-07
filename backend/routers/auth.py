from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import compute_initials, get_current_user, hash_password, issue_token, verify_password
from database import get_db
import models
import schemas

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    value = (email or "").strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise HTTPException(status_code=400, detail="Укажите корректный email")
    return value


@router.post("/register", response_model=schemas.AuthResponse, status_code=201)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    existing = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    role = payload.role.strip() or "Студент"
    if role.lower() == "administrator":
        role = "Студент"

    salt, password_hash = hash_password(payload.password)
    user = models.User(
        name=payload.name.strip(),
        initials=compute_initials(payload.name),
        role=role,
        email=email,
        password_salt=salt,
        password_hash=password_hash,
        auth_token=issue_token(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.AuthResponse(token=user.auth_token or "", user=user)


@router.post("/login", response_model=schemas.AuthResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if not user or not verify_password(payload.password, user.password_salt, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")

    user.auth_token = issue_token()
    db.commit()
    db.refresh(user)
    return schemas.AuthResponse(token=user.auth_token or "", user=user)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/logout", status_code=204)
def logout(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.auth_token = None
    db.commit()
