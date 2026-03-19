import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth import get_course_for_user_or_404, get_current_user
from database import get_db
import models
import schemas

router = APIRouter(prefix="/courses/{course_id}/assignments", tags=["assignments"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads", "assignments")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024

RU_MONTHS = {
    "янв": 1, "января": 1,
    "фев": 2, "февраля": 2,
    "мар": 3, "марта": 3,
    "апр": 4, "апреля": 4,
    "май": 5, "мая": 5,
    "июн": 6, "июня": 6,
    "июл": 7, "июля": 7,
    "авг": 8, "августа": 8,
    "сен": 9, "сентября": 9,
    "окт": 10, "октября": 10,
    "ноя": 11, "ноября": 11,
    "дек": 12, "декабря": 12,
}


def parse_deadline(deadline: str) -> datetime | None:
    value = (deadline or "").strip().lower()
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    parts = value.replace(",", " ").split()
    if len(parts) == 3 and parts[1] in RU_MONTHS:
        day = int(parts[0])
        month = RU_MONTHS[parts[1]]
        year = int(parts[2])
        return datetime(year, month, day)

    return None


def _get_assignment_or_404(course_id: int, assignment_id: int, db: Session) -> models.Assignment:
    assignment = (
        db.query(models.Assignment)
        .filter(models.Assignment.id == assignment_id, models.Assignment.course_id == course_id)
        .first()
    )
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    return assignment


@router.get("/", response_model=list[schemas.AssignmentOut])
def list_assignments(
    course_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    return (
        db.query(models.Assignment)
        .filter(models.Assignment.course_id == course_id)
        .order_by(models.Assignment.deadline_dt.asc().nullslast(), models.Assignment.created_at.asc())
        .all()
    )


@router.post("/", response_model=schemas.AssignmentOut, status_code=201)
async def create_assignment(
    course_id: int,
    title: str = Form(...),
    description: str = Form(""),
    deadline: str = Form(""),
    status: str = Form("pending"),
    file: UploadFile | None = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)

    file_path = None
    file_name = None

    if file and file.filename:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(413, "File too large (max 50 MB)")

        ext = os.path.splitext(file.filename)[1]
        disk_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, disk_name)
        with open(file_path, "wb") as f:
            f.write(contents)
        file_name = file.filename

    assignment = models.Assignment(
        course_id=course_id,
        title=title,
        description=description,
        deadline=deadline,
        deadline_dt=parse_deadline(deadline),
        status=status,
        file_path=file_path,
        file_name=file_name,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.patch("/{assignment_id}", response_model=schemas.AssignmentOut)
def update_assignment(
    course_id: int,
    assignment_id: int,
    payload: schemas.AssignmentUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    assignment = _get_assignment_or_404(course_id, assignment_id, db)

    data = payload.model_dump(exclude_none=True)
    if "deadline" in data:
        data["deadline_dt"] = parse_deadline(data["deadline"])

    for field, value in data.items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)
    return assignment


@router.put("/{assignment_id}", response_model=schemas.AssignmentOut)
async def full_update_assignment(
    course_id: int,
    assignment_id: int,
    title: str = Form(...),
    description: str = Form(""),
    deadline: str = Form(""),
    status: str = Form("pending"),
    file: UploadFile | None = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    assignment = _get_assignment_or_404(course_id, assignment_id, db)

    assignment.title = title
    assignment.description = description
    assignment.deadline = deadline
    assignment.deadline_dt = parse_deadline(deadline)
    assignment.status = status

    if file and file.filename:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(413, "File too large (max 50 MB)")

        if assignment.file_path and os.path.exists(assignment.file_path):
            os.remove(assignment.file_path)

        ext = os.path.splitext(file.filename)[1]
        disk_name = f"{uuid.uuid4().hex}{ext}"
        disk_path = os.path.join(UPLOAD_DIR, disk_name)
        with open(disk_path, "wb") as f:
            f.write(contents)
        assignment.file_path = disk_path
        assignment.file_name = file.filename

    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/{assignment_id}/download")
def download_assignment_file(
    course_id: int,
    assignment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    assignment = _get_assignment_or_404(course_id, assignment_id, db)
    if not assignment.file_path or not os.path.exists(assignment.file_path):
        raise HTTPException(404, "No file attached")
    return FileResponse(assignment.file_path, filename=assignment.file_name)


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(
    course_id: int,
    assignment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    assignment = _get_assignment_or_404(course_id, assignment_id, db)
    if assignment.file_path and os.path.exists(assignment.file_path):
        os.remove(assignment.file_path)
    db.delete(assignment)
    db.commit()
