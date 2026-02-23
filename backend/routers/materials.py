import os
import uuid
import math
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/courses/{course_id}/materials", tags=["materials"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Map MIME type → (icon emoji, icon background)
MIME_ICONS: dict[str, tuple[str, str]] = {
    "application/pdf":                               ("📄", "#fee2e2"),
    "application/msword":                            ("📝", "#dbeafe"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ("📝", "#dbeafe"),
    "application/vnd.ms-powerpoint":                ("📊", "#fef9c3"),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ("📊", "#fef9c3"),
    "application/vnd.ms-excel":                     ("📈", "#d1fae5"),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ("📈", "#d1fae5"),
    "text/plain":                                    ("📃", "#f0fdf4"),
    "image/png":                                     ("🖼️",  "#d1fae5"),
    "image/jpeg":                                    ("🖼️",  "#d1fae5"),
    "image/gif":                                     ("🖼️",  "#d1fae5"),
    "video/mp4":                                     ("🎬", "#ede9fe"),
    "audio/mpeg":                                    ("🎵", "#fce7f3"),
    "application/zip":                               ("📦", "#e0e7ff"),
}


def human_size(n: int) -> str:
    if n < 1024:
        return f"{n} Б"
    if n < 1024 ** 2:
        return f"{n/1024:.0f} КБ"
    return f"{n/1024**2:.1f} МБ"


def _get_course_or_404(course_id: int, db: Session) -> models.Course:
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    return course


@router.get("/", response_model=list[schemas.MaterialOut])
def list_materials(course_id: int, db: Session = Depends(get_db)):
    _get_course_or_404(course_id, db)
    return db.query(models.Material).filter(models.Material.course_id == course_id).all()


@router.post("/", response_model=schemas.MaterialOut, status_code=201)
async def upload_material(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    _get_course_or_404(course_id, db)

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 50 MB)")

    # Save to disk
    ext       = os.path.splitext(file.filename or "file")[1]
    disk_name = f"{uuid.uuid4().hex}{ext}"
    disk_path = os.path.join(UPLOAD_DIR, disk_name)
    with open(disk_path, "wb") as f:
        f.write(contents)

    mime      = file.content_type or "application/octet-stream"
    icon, bg  = MIME_ICONS.get(mime, ("📎", "#e2e8f0"))

    material = models.Material(
        course_id  = course_id,
        name       = file.filename or disk_name,
        file_path  = disk_path,
        size_bytes = len(contents),
        mime_type  = mime,
        icon       = icon,
        icon_bg    = bg,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("/{material_id}/download")
def download_material(course_id: int, material_id: int, db: Session = Depends(get_db)):
    mat = db.query(models.Material).filter(
        models.Material.id == material_id,
        models.Material.course_id == course_id,
    ).first()
    if not mat:
        raise HTTPException(404, "Material not found")
    if not os.path.exists(mat.file_path):
        raise HTTPException(404, "File missing on disk")
    return FileResponse(mat.file_path, filename=mat.name, media_type=mat.mime_type)


@router.delete("/{material_id}", status_code=204)
def delete_material(course_id: int, material_id: int, db: Session = Depends(get_db)):
    mat = db.query(models.Material).filter(
        models.Material.id == material_id,
        models.Material.course_id == course_id,
    ).first()
    if not mat:
        raise HTTPException(404, "Material not found")
    if os.path.exists(mat.file_path):
        os.remove(mat.file_path)
    db.delete(mat)
    db.commit()
