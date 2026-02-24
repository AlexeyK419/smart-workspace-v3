import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/courses/{course_id}/assignments", tags=["assignments"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "assignments")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024


def _get_course_or_404(course_id: int, db: Session) -> models.Course:
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    return course


def _get_assignment_or_404(course_id: int, assignment_id: int, db: Session) -> models.Assignment:
    a = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id,
        models.Assignment.course_id == course_id,
    ).first()
    if not a:
        raise HTTPException(404, "Assignment not found")
    return a


@router.get("/", response_model=list[schemas.AssignmentOut])
def list_assignments(course_id: int, db: Session = Depends(get_db)):
    _get_course_or_404(course_id, db)
    return (
        db.query(models.Assignment)
        .filter(models.Assignment.course_id == course_id)
        .order_by(models.Assignment.deadline_dt.asc())
        .all()
    )


@router.post("/", response_model=schemas.AssignmentOut, status_code=201)
async def create_assignment(
    course_id:   int,
    title:       str = Form(...),
    description: str = Form(""),
    deadline:    str = Form(""),
    status:      str = Form("pending"),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    _get_course_or_404(course_id, db)

    file_path = None
    file_name = None

    if file and file.filename:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(413, "File too large (max 50 MB)")
        ext       = os.path.splitext(file.filename)[1]
        disk_name = f"{uuid.uuid4().hex}{ext}"
        disk_path = os.path.join(UPLOAD_DIR, disk_name)
        with open(disk_path, "wb") as f:
            f.write(contents)
        file_path = disk_path
        file_name = file.filename

    assignment = models.Assignment(
        course_id   = course_id,
        title       = title,
        description = description,
        deadline    = deadline,
        status      = status,
        file_path   = file_path,
        file_name   = file_name,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.patch("/{assignment_id}", response_model=schemas.AssignmentOut)
def update_assignment(
    course_id:     int,
    assignment_id: int,
    payload:       schemas.AssignmentUpdate,
    db:            Session = Depends(get_db),
):
    a = _get_assignment_or_404(course_id, assignment_id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(a, field, value)
    db.commit()
    db.refresh(a)
    return a


@router.put("/{assignment_id}", response_model=schemas.AssignmentOut)
async def full_update_assignment(
    course_id:     int,
    assignment_id: int,
    title:       str = Form(...),
    description: str = Form(""),
    deadline:    str = Form(""),
    status:      str = Form("pending"),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Full update of an assignment including optional file replacement."""
    a = _get_assignment_or_404(course_id, assignment_id, db)

    a.title = title
    a.description = description
    a.deadline = deadline
    a.status = status

    if file and file.filename:
        # Remove old file
        if a.file_path and os.path.exists(a.file_path):
            os.remove(a.file_path)
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(413, "File too large (max 50 MB)")
        ext       = os.path.splitext(file.filename)[1]
        disk_name = f"{uuid.uuid4().hex}{ext}"
        disk_path = os.path.join(UPLOAD_DIR, disk_name)
        with open(disk_path, "wb") as f:
            f.write(contents)
        a.file_path = disk_path
        a.file_name = file.filename

    db.commit()
    db.refresh(a)
    return a


@router.get("/{assignment_id}/download")
def download_assignment_file(course_id: int, assignment_id: int, db: Session = Depends(get_db)):
    a = _get_assignment_or_404(course_id, assignment_id, db)
    if not a.file_path or not os.path.exists(a.file_path):
        raise HTTPException(404, "No file attached")
    return FileResponse(a.file_path, filename=a.file_name)


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(course_id: int, assignment_id: int, db: Session = Depends(get_db)):
    a = _get_assignment_or_404(course_id, assignment_id, db)
    if a.file_path and os.path.exists(a.file_path):
        os.remove(a.file_path)
    db.delete(a)
    db.commit()