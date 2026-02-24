import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/", response_model=list[schemas.CourseOut])
def list_courses(user_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Course)
    if user_id:
        q = q.filter(models.Course.user_id == user_id)
    return q.all()


@router.post("/", response_model=schemas.CourseOut, status_code=201)
def create_course(user_id: int, payload: schemas.CourseCreate, db: Session = Depends(get_db)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    course = models.Course(**payload.model_dump(), user_id=user_id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/{course_id}", response_model=schemas.CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    return course


@router.patch("/{course_id}", response_model=schemas.CourseOut)
def update_course(course_id: int, payload: schemas.CourseUpdate, db: Session = Depends(get_db)):
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    # Clean up files on disk
    for mat in (course.materials or []):
        if mat.file_path and os.path.exists(mat.file_path):
            os.remove(mat.file_path)
    for a in (course.assignments or []):
        if a.file_path and os.path.exists(a.file_path):
            os.remove(a.file_path)
    db.delete(course)
    db.commit()