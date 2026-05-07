import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from auth import get_course_for_user_or_404, get_current_user
from ai_embeddings import delete_context_chunks
from database import get_db
from file_utils import read_file_text_raw
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


MIME_ICONS: dict[str, tuple[str, str]] = {
    "application/pdf": ("📄", "#fee2e2"),
    "application/msword": ("📝", "#dbeafe"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ("📝", "#dbeafe"),
    "application/vnd.ms-powerpoint": ("📊", "#fef9c3"),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ("📊", "#fef9c3"),
    "application/vnd.ms-excel": ("📈", "#d1fae5"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ("📈", "#d1fae5"),
    "text/plain": ("📃", "#f0fdf4"),
    "image/png": ("🖼️", "#d1fae5"),
    "image/jpeg": ("🖼️", "#d1fae5"),
    "image/gif": ("🖼️", "#d1fae5"),
    "video/mp4": ("🎬", "#ede9fe"),
    "audio/mpeg": ("🎵", "#fce7f3"),
    "application/zip": ("📦", "#e0e7ff"),
}


def _save_uploaded_file(upload_file: UploadFile) -> models.AssignmentFile:
    contents = upload_file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File {upload_file.filename} too large (max 50 MB)")

    ext = os.path.splitext(upload_file.filename)[1]
    disk_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, disk_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    mime = upload_file.content_type or "application/octet-stream"
    icon, icon_bg = MIME_ICONS.get(mime, ("📄", "#e2e8f0"))

    return models.AssignmentFile(
        name=upload_file.filename,
        file_path=file_path,
        size_bytes=len(contents),
        mime_type=mime,
        icon=icon,
        icon_bg=icon_bg,
    )


def _remove_assignment_files_from_disk(assignment_files: list[models.AssignmentFile]):
    for af in assignment_files:
        if af.file_path and os.path.exists(af.file_path):
            os.remove(af.file_path)


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
        .options(selectinload(models.Assignment.files))
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
        .options(selectinload(models.Assignment.files))
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
    files: list[UploadFile] = File(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)

    upload_files: list[UploadFile] = []
    if files:
        for f_obj in files:
            if f_obj.filename:
                upload_files.append(f_obj)

    old_file_path = None
    old_file_name = None
    assignment_files: list[models.AssignmentFile] = []

    if upload_files:
        old_file_name = upload_files[0].filename
        for upload_file in upload_files:
            contents = await upload_file.read()
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(413, f"File {upload_file.filename} too large (max 50 MB)")

            ext = os.path.splitext(upload_file.filename)[1]
            disk_name = f"{uuid.uuid4().hex}{ext}"
            disk_path = os.path.join(UPLOAD_DIR, disk_name)
            with open(disk_path, "wb") as f:
                f.write(contents)

            mime = upload_file.content_type or "application/octet-stream"
            icon, icon_bg = MIME_ICONS.get(mime, ("📄", "#e2e8f0"))

            assignment_files.append(models.AssignmentFile(
                name=upload_file.filename,
                file_path=disk_path,
                size_bytes=len(contents),
                mime_type=mime,
                icon=icon,
                icon_bg=icon_bg,
            ))

            if old_file_path is None:
                old_file_path = disk_path

    assignment = models.Assignment(
        course_id=course_id,
        title=title,
        description=description,
        deadline=deadline,
        deadline_dt=parse_deadline(deadline),
        status=status,
        file_path=old_file_path,
        file_name=old_file_name,
    )
    db.add(assignment)
    db.flush()

    for assignment_file in assignment_files:
        assignment_file.assignment_id = assignment.id
        db.add(assignment_file)

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
    files: list[UploadFile] = File(None),
    replace_files: str = Form("false"),
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

    upload_files: list[UploadFile] = []
    if files:
        for f_obj in files:
            if f_obj.filename:
                upload_files.append(f_obj)

    if upload_files:
        if replace_files.lower() == "true":
            _remove_assignment_files_from_disk(assignment.files)
            for af in assignment.files:
                db.delete(af)

        old_file_path = None
        old_file_name = None

        for upload_file in upload_files:
            contents = await upload_file.read()
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(413, f"File {upload_file.filename} too large (max 50 MB)")

            ext = os.path.splitext(upload_file.filename)[1]
            disk_name = f"{uuid.uuid4().hex}{ext}"
            disk_path = os.path.join(UPLOAD_DIR, disk_name)
            with open(disk_path, "wb") as f:
                f.write(contents)

            mime = upload_file.content_type or "application/octet-stream"
            icon, icon_bg = MIME_ICONS.get(mime, ("📄", "#e2e8f0"))

            new_assignment_file = models.AssignmentFile(
                assignment_id=assignment.id,
                name=upload_file.filename,
                file_path=disk_path,
                size_bytes=len(contents),
                mime_type=mime,
                icon=icon,
                icon_bg=icon_bg,
            )
            db.add(new_assignment_file)

            if old_file_path is None:
                old_file_path = disk_path
                old_file_name = upload_file.filename

        if assignment.file_path and os.path.exists(assignment.file_path):
            os.remove(assignment.file_path)
        assignment.file_path = old_file_path
        assignment.file_name = old_file_name

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


@router.get("/{assignment_id}/preview")
def preview_assignment_file(
    course_id: int,
    assignment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    assignment = _get_assignment_or_404(course_id, assignment_id, db)
    if not assignment.file_path:
        raise HTTPException(400, "No file attached to this assignment")
    text, state = read_file_text_raw(assignment.file_path)
    if not text:
        raise HTTPException(400, state)
    return {"text": text, "name": assignment.file_name or "assignment", "mime_type": "application/octet-stream"}


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
    _remove_assignment_files_from_disk(assignment.files)
    delete_context_chunks(db, user_id=current_user.id, entity_type="assignment", entity_id=assignment.id)
    for af in assignment.files:
        delete_context_chunks(db, user_id=current_user.id, entity_type="assignment_file", entity_id=af.id)
    db.delete(assignment)
    db.commit()


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


@router.get("/{assignment_id}/preview")
def preview_assignment_file(
    course_id: int,
    assignment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    assignment = _get_assignment_or_404(course_id, assignment_id, db)
    if not assignment.file_path:
        raise HTTPException(400, "No file attached to this assignment")
    text, state = read_file_text_raw(assignment.file_path)
    if not text:
        raise HTTPException(400, state)
    return {"text": text, "name": assignment.file_name or "assignment", "mime_type": "application/octet-stream"}


@router.post("/{assignment_id}/files", response_model=schemas.AssignmentFileOut, status_code=201)
async def upload_assignment_file(
    course_id: int,
    assignment_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    _get_assignment_or_404(course_id, assignment_id, db)

    contents = await file.read()
    if not file.filename:
        raise HTTPException(400, "No file provided")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 50 MB)")

    ext = os.path.splitext(file.filename)[1]
    disk_name = f"{uuid.uuid4().hex}{ext}"
    disk_path = os.path.join(UPLOAD_DIR, disk_name)
    with open(disk_path, "wb") as f:
        f.write(contents)

    mime = file.content_type or "application/octet-stream"
    icon, icon_bg = MIME_ICONS.get(mime, ("📄", "#e2e8f0"))

    assignment_file = models.AssignmentFile(
        assignment_id=assignment_id,
        name=file.filename,
        file_path=disk_path,
        size_bytes=len(contents),
        mime_type=mime,
        icon=icon,
        icon_bg=icon_bg,
    )
    db.add(assignment_file)
    db.commit()
    db.refresh(assignment_file)
    return assignment_file


@router.get("/{assignment_id}/files/{file_id}/download")
def download_assignment_file_item(
    course_id: int,
    assignment_id: int,
    file_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    _get_assignment_or_404(course_id, assignment_id, db)
    assignment_file = db.query(models.AssignmentFile).filter(
        models.AssignmentFile.id == file_id,
        models.AssignmentFile.assignment_id == assignment_id,
    ).first()
    if not assignment_file or not os.path.exists(assignment_file.file_path):
        raise HTTPException(404, "File not found")
    return FileResponse(assignment_file.file_path, filename=assignment_file.name)


@router.get("/{assignment_id}/files/{file_id}/preview")
def preview_assignment_file_item(
    course_id: int,
    assignment_id: int,
    file_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    _get_assignment_or_404(course_id, assignment_id, db)
    assignment_file = db.query(models.AssignmentFile).filter(
        models.AssignmentFile.id == file_id,
        models.AssignmentFile.assignment_id == assignment_id,
    ).first()
    if not assignment_file:
        raise HTTPException(404, "File not found")
    text, state = read_file_text_raw(assignment_file.file_path)
    if not text:
        raise HTTPException(400, state)
    return {"text": text, "name": assignment_file.name, "mime_type": assignment_file.mime_type}


@router.delete("/{assignment_id}/files/{file_id}", status_code=204)
def delete_assignment_file_item(
    course_id: int,
    assignment_id: int,
    file_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    _get_assignment_or_404(course_id, assignment_id, db)
    assignment_file = db.query(models.AssignmentFile).filter(
        models.AssignmentFile.id == file_id,
        models.AssignmentFile.assignment_id == assignment_id,
    ).first()
    if not assignment_file:
        raise HTTPException(404, "File not found")
    if assignment_file.file_path and os.path.exists(assignment_file.file_path):
        os.remove(assignment_file.file_path)
    delete_context_chunks(db, user_id=current_user.id, entity_type="assignment_file", entity_id=assignment_file.id)
    db.delete(assignment_file)
    db.commit()
