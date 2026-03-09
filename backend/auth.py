import hashlib
import hmac
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
import models

security = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    actual_salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        actual_salt.encode("utf-8"),
        120_000,
    ).hex()
    return actual_salt, hashed


def verify_password(password: str, salt: str | None, password_hash: str | None) -> bool:
    if not salt or not password_hash:
        return False
    _, candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, password_hash)


def issue_token() -> str:
    return secrets.token_urlsafe(32)


def compute_initials(name: str) -> str:
    parts = [part for part in (name or "").strip().split() if part]
    if not parts:
        return "ST"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Session = Depends(get_db),
) -> models.User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется вход в аккаунт")

    token = credentials.credentials.strip()
    user = db.query(models.User).filter(models.User.auth_token == token).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия недействительна")
    return user


def ensure_same_user(requested_user_id: int, current_user: models.User):
    if current_user.id != requested_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к данным другого пользователя")


def get_course_for_user_or_404(course_id: int, user_id: int, db: Session) -> models.Course:
    course = (
        db.query(models.Course)
        .filter(models.Course.id == course_id, models.Course.user_id == user_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return course


def get_assignment_for_user_or_404(assignment_id: int, user_id: int, db: Session) -> models.Assignment:
    assignment = (
        db.query(models.Assignment)
        .join(models.Course, models.Course.id == models.Assignment.course_id)
        .filter(models.Assignment.id == assignment_id, models.Course.user_id == user_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    return assignment
