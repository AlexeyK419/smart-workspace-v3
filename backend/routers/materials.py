import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth import get_course_for_user_or_404, get_current_user
from ai_embeddings import delete_context_chunks
from database import get_db
import models
import schemas

router = APIRouter(prefix="/courses/{course_id}/materials", tags=["materials"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024

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


@router.get("/", response_model=list[schemas.MaterialOut])
def list_materials(
    course_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    return db.query(models.Material).filter(models.Material.course_id == course_id).all()


@router.post("/", response_model=schemas.MaterialOut, status_code=201)
async def upload_material(
    course_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 50 MB)")

    ext = os.path.splitext(file.filename or "file")[1]
    disk_name = f"{uuid.uuid4().hex}{ext}"
    disk_path = os.path.join(UPLOAD_DIR, disk_name)
    with open(disk_path, "wb") as f:
        f.write(contents)

    mime = file.content_type or "application/octet-stream"
    icon, bg = MIME_ICONS.get(mime, ("📎", "#e2e8f0"))

    material = models.Material(
        course_id=course_id,
        name=file.filename or disk_name,
        file_path=disk_path,
        size_bytes=len(contents),
        mime_type=mime,
        icon=icon,
        icon_bg=bg,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("/{material_id}/download")
def download_material(
    course_id: int,
    material_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    mat = (
        db.query(models.Material)
        .filter(models.Material.id == material_id, models.Material.course_id == course_id)
        .first()
    )
    if not mat:
        raise HTTPException(404, "Material not found")
    if not os.path.exists(mat.file_path):
        raise HTTPException(404, "File missing on disk")
    return FileResponse(mat.file_path, filename=mat.name, media_type=mat.mime_type)


@router.delete("/{material_id}", status_code=204)
def delete_material(
    course_id: int,
    material_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    mat = (
        db.query(models.Material)
        .filter(models.Material.id == material_id, models.Material.course_id == course_id)
        .first()
    )
    if not mat:
        raise HTTPException(404, "Material not found")
    if os.path.exists(mat.file_path):
        os.remove(mat.file_path)
    delete_context_chunks(db, user_id=current_user.id, entity_type="material", entity_id=mat.id)
    db.delete(mat)
    db.commit()
