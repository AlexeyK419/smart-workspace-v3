import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_course_for_user_or_404, get_current_user
from ai_embeddings import delete_context_chunks
from database import get_db
import models
import schemas

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/", response_model=list[schemas.CourseOut])
def list_courses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Course)
        .filter(models.Course.user_id == current_user.id)
        .order_by(models.Course.id.asc())
        .all()
    )


@router.post("/", response_model=schemas.CourseOut, status_code=201)
def create_course(
    payload: schemas.CourseCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = models.Course(**payload.model_dump(), user_id=current_user.id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/{course_id}", response_model=schemas.CourseOut)
def get_course(
    course_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_course_for_user_or_404(course_id, current_user.id, db)


@router.patch("/{course_id}", response_model=schemas.CourseOut)
def update_course(
    course_id: int,
    payload: schemas.CourseUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = get_course_for_user_or_404(course_id, current_user.id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = get_course_for_user_or_404(course_id, current_user.id, db)
    for mat in (course.materials or []):
        if mat.file_path and os.path.exists(mat.file_path):
            os.remove(mat.file_path)
    for assignment in (course.assignments or []):
        if assignment.file_path and os.path.exists(assignment.file_path):
            os.remove(assignment.file_path)
    delete_context_chunks(db, user_id=current_user.id, parent_type="course", parent_id=course.id)
    db.delete(course)
    db.commit()
