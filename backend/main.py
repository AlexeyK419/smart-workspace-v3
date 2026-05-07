"""
Smart Student Workspace — FastAPI backend v5
  • PostgreSQL via SQLAlchemy 2
  • token-based auth (register/login/me)
  • per-user data isolation
  • team projects with tasks, files, comments and realtime chat
  • AI assistant integration
  • WebSocket project chat
  • file uploads (materials + assignments + project files)
"""

import logging
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, text

from auth import compute_initials, hash_password
from config import settings
from database import engine, SessionLocal
import models
from routers import admin, auth, users, courses, materials, assignments, ai, schedule, projects, chats

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

os.makedirs(settings.upload_dir_path, exist_ok=True)


def init_db():
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")


def upgrade_schema():
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_salt VARCHAR(64)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_token VARCHAR(255)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS workspace_ai_summary TEXT"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_auth_token ON users (auth_token)"))
        conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS ai_summary TEXT"))
        conn.execute(text("ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"))
        conn.execute(text("ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP"))
        conn.execute(text("UPDATE project_tasks SET updated_at = COALESCE(updated_at, created_at, NOW())"))
        conn.execute(text("UPDATE project_tasks SET completed_at = COALESCE(completed_at, created_at, NOW()) WHERE status = 'done'"))
    logger.info("Database auth and project task columns ensured")

    migrate_legacy_assignment_files()


def upgrade_legacy_users_auth():
    db = SessionLocal()
    try:
        legacy_users = (
            db.query(models.User)
            .filter(
                (models.User.email.is_(None))
                | (models.User.password_hash.is_(None))
                | (models.User.password_salt.is_(None))
            )
            .all()
        )
        for user in legacy_users:
            if not user.email:
                user.email = f"legacy{user.id}@workspace.local"
            if not user.initials:
                user.initials = compute_initials(user.name)
            if not user.password_hash or not user.password_salt:
                salt, password_hash = hash_password("workspace123")
                user.password_salt = salt
                user.password_hash = password_hash
        if legacy_users:
            db.commit()
            logger.info("Legacy users received auth credentials")
    finally:
        db.close()


def ensure_admin_user():
    db = SessionLocal()
    try:
        admin_email = settings.admin_email.strip().lower()
        raw_password = (settings.admin_password or "").strip() or secrets.token_urlsafe(16)
        salt, password_hash = hash_password(raw_password)
        admin_user = db.query(models.User).filter(func.lower(models.User.email) == admin_email).first()
        if admin_user:
            changed = False
            if admin_user.name != "Admin":
                admin_user.name = "Admin"
                changed = True
            if admin_user.initials != "AD":
                admin_user.initials = "AD"
                changed = True
            if admin_user.role != "Administrator":
                admin_user.role = "Administrator"
                changed = True
            if not admin_user.password_salt or not admin_user.password_hash:
                salt, password_hash = hash_password(raw_password)
                admin_user.password_salt = salt
                admin_user.password_hash = password_hash
                changed = True
            if changed:
                db.commit()
                logger.info("Admin user updated (email=%s)", settings.admin_email)
        else:
            db.add(models.User(
                name="Admin",
                initials="AD",
                role="Administrator",
                email=settings.admin_email,
                password_salt=salt,
                password_hash=password_hash,
            ))
            db.commit()
            if (settings.admin_password or "").strip():
                logger.info("Admin user created (email=%s)", settings.admin_email)
            else:
                logger.warning("Admin user created with generated password; email=%s", settings.admin_email)
    finally:
        db.close()


def migrate_legacy_assignment_files():
    db = SessionLocal()
    try:
        assignments_with_legacy_file = (
            db.query(models.Assignment)
            .filter(
                models.Assignment.file_path.isnot(None),
                models.Assignment.file_name.isnot(None),
            )
            .all()
        )
        if not assignments_with_legacy_file:
            return

        already_migrated_ids = set(
            row[0] for row in db.query(models.AssignmentFile.assignment_id).distinct().all()
        )

        migrated = 0
        for assignment in assignments_with_legacy_file:
            if assignment.id in already_migrated_ids:
                continue

            import os as _os
            size = 0
            mime = "application/octet-stream"
            icon, icon_bg = "📄", "#e2e8f0"
            if _os.path.exists(assignment.file_path):
                stat = _os.stat(assignment.file_path)
                size = stat.st_size

            if assignment.file_name:
                ext = _os.path.splitext(assignment.file_name)[1].lower()
                MIME_MAP = {
                    ".pdf": ("📄", "#fee2e2", "application/pdf"),
                    ".docx": ("📝", "#dbeafe", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                    ".doc": ("📝", "#dbeafe", "application/msword"),
                    ".xlsx": ("📈", "#d1fae5", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    ".xls": ("📈", "#d1fae5", "application/vnd.ms-excel"),
                    ".pptx": ("📊", "#fef9c3", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
                    ".ppt": ("📊", "#fef9c3", "application/vnd.ms-powerpoint"),
                    ".txt": ("📃", "#f0fdf4", "text/plain"),
                    ".png": ("🖼️", "#d1fae5", "image/png"),
                    ".jpg": ("🖼️", "#d1fae5", "image/jpeg"),
                    ".jpeg": ("🖼️", "#d1fae5", "image/jpeg"),
                    ".zip": ("📦", "#e0e7ff", "application/zip"),
                }
                result = MIME_MAP.get(ext)
                if result:
                    icon, icon_bg, mime = result

            db.add(models.AssignmentFile(
                assignment_id=assignment.id,
                name=assignment.file_name,
                file_path=assignment.file_path,
                size_bytes=size,
                mime_type=mime,
                icon=icon,
                icon_bg=icon_bg,
            ))
            migrated += 1

        if migrated:
            db.commit()
            logger.info("Migrated %d legacy assignment files to assignment_files table", migrated)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    upgrade_schema()
    upgrade_legacy_users_auth()
    ensure_admin_user()
    yield


app = FastAPI(
    title="Smart Student Workspace API",
    version="5.0.0",
    description=(
        "REST API for the student workspace diploma project.\n\n"
        "**Database:** PostgreSQL\n"
        "**Authentication:** bearer token\n"
        "**Collaboration:** team projects, tasks, comments, shared files and realtime chat\n"
        "**Assistant:** Workspace AI\n"
    ),
    lifespan=lifespan,
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir_path), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(assignments.router)
app.include_router(schedule.router)
app.include_router(projects.router)
app.include_router(projects.ws_router)
app.include_router(chats.router)
app.include_router(chats.ws_router)
app.include_router(ai.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
