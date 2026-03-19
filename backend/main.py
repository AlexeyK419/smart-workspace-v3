"""
Smart Student Workspace — FastAPI backend v5
  • PostgreSQL via SQLAlchemy 2
  • token-based auth (register/login/me)
  • per-user data isolation
  • team projects with tasks, files and chat
  • AI assistant integration
  • file uploads (materials + assignments + project files)
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from auth import compute_initials, hash_password
from config import settings
from database import engine, SessionLocal
import models
from routers import auth, users, courses, materials, assignments, ai, schedule, projects

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


def init_db():
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")


def upgrade_schema():
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_salt VARCHAR(64)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_token VARCHAR(255)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_auth_token ON users (auth_token)"))
    logger.info("Database auth columns ensured")


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


def seed():
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            return

        salt, password_hash = hash_password("workspace123")
        user = models.User(
            name="Алексей Иванов",
            initials="АИ",
            role="2-й курс · ИТ",
            email="demo@workspace.local",
            password_salt=salt,
            password_hash=password_hash,
        )
        db.add(user)
        db.flush()

        db.add_all([
            models.Course(
                user_id=user.id,
                name="Алгоритмы и структуры данных",
                color="#3d52d5",
                emoji="⚙️",
                teacher="Проф. Морозов А.В.",
                semester="Весна 2025",
                credits=4,
                progress=72,
                assignments=[
                    models.Assignment(
                        title="Реализация красно-чёрного дерева",
                        description="Реализовать структуру данных «красно-чёрное дерево» с операциями вставки, удаления и поиска.",
                        deadline="28 фев 2025",
                        deadline_dt=datetime(2025, 2, 28),
                        status="progress",
                    ),
                    models.Assignment(
                        title="Анализ сложности алгоритмов",
                        description="Письменный анализ 5 алгоритмов с доказательством временной и пространственной сложности.",
                        deadline="10 мар 2025",
                        deadline_dt=datetime(2025, 3, 10),
                        status="pending",
                    ),
                ],
            ),
            models.Course(
                user_id=user.id,
                name="Базы данных",
                color="#2d7a4f",
                emoji="🗄️",
                teacher="Доц. Сидорова К.И.",
                semester="Весна 2025",
                credits=3,
                progress=55,
                assignments=[
                    models.Assignment(
                        title="Проектирование схемы БД",
                        description="Разработать нормализованную схему БД для интернет-магазина.",
                        deadline="5 мар 2025",
                        deadline_dt=datetime(2025, 3, 5),
                        status="done",
                    ),
                    models.Assignment(
                        title="SQL-запросы",
                        description="Написать 20 SQL-запросов различной сложности.",
                        deadline="20 мар 2025",
                        deadline_dt=datetime(2025, 3, 20),
                        status="progress",
                    ),
                ],
            ),
            models.Course(
                user_id=user.id,
                name="Теория вероятностей",
                color="#b45309",
                emoji="📊",
                teacher="Проф. Ковалёв Н.П.",
                semester="Весна 2025",
                credits=3,
                progress=40,
                assignments=[
                    models.Assignment(
                        title="Контрольная работа №2",
                        description="Решение задач: мат. ожидание, дисперсия, законы распределения.",
                        deadline="1 мар 2025",
                        deadline_dt=datetime(2025, 3, 1),
                        status="overdue",
                    ),
                ],
            ),
            models.Course(
                user_id=user.id,
                name="Английский язык",
                color="#0891b2",
                emoji="🌐",
                teacher="Ст. преп. Фролова О.С.",
                semester="Весна 2025",
                credits=2,
                progress=88,
                assignments=[
                    models.Assignment(
                        title='Эссе "Technology in Education"',
                        description="Эссе 500–600 слов о влиянии технологий на образование.",
                        deadline="25 фев 2025",
                        deadline_dt=datetime(2025, 2, 25),
                        status="progress",
                    ),
                ],
            ),
        ])

        db.add_all([
            models.ScheduleEvent(
                user_id=user.id,
                title="Алгоритмы и структуры данных",
                day_index=0,
                start_minute=9 * 60,
                duration_minutes=90,
                location="Аудитория 312",
                teacher="Проф. Морозов А.В.",
                type="lecture",
                color="#3d52d5",
            ),
            models.ScheduleEvent(
                user_id=user.id,
                title="Базы данных",
                day_index=1,
                start_minute=11 * 60,
                duration_minutes=120,
                location="Лаборатория 4Б",
                teacher="Доц. Сидорова К.И.",
                type="practice",
                color="#2d7a4f",
            ),
            models.ScheduleEvent(
                user_id=user.id,
                title="Английский язык",
                day_index=2,
                start_minute=14 * 60,
                duration_minutes=90,
                location="Онлайн (Zoom)",
                teacher="Ст. преп. Фролова О.С.",
                type="seminar",
                color="#0891b2",
            ),
        ])

        db.commit()
        logger.info("✅ Demo user inserted (email=demo@workspace.local, password=workspace123)")
    finally:
        db.close()


def seed_projects():
    db = SessionLocal()
    try:
        demo_user = db.query(models.User).filter(models.User.email == "demo@workspace.local").first()
        if not demo_user:
            return

        existing = (
            db.query(models.ProjectMember)
            .filter(models.ProjectMember.user_id == demo_user.id)
            .count()
        )
        if existing:
            return

        project = models.Project(
            owner_id=demo_user.id,
            name="Командный учебный проект",
            description="Пространство для совместной работы над групповым проектом: задачи, файлы и общий чат.",
            color="#7c3aed",
        )
        db.add(project)
        db.flush()

        db.add(models.ProjectMember(project_id=project.id, user_id=demo_user.id, role="owner"))
        db.add_all([
            models.ProjectTask(
                project_id=project.id,
                title="Собрать требования по MVP",
                description="Зафиксировать роли, разделить функциональность и подготовить список ближайших задач.",
                status="in_progress",
                created_by_id=demo_user.id,
                assignee_id=demo_user.id,
                due_date=datetime(2025, 3, 24, 18, 0),
            ),
            models.ProjectTask(
                project_id=project.id,
                title="Подготовить презентацию демо",
                description="Сделать короткую презентацию по целям проекта и пользовательским сценариям.",
                status="todo",
                created_by_id=demo_user.id,
                due_date=datetime(2025, 3, 28, 12, 0),
            ),
        ])
        db.add(models.ProjectMessage(
            project_id=project.id,
            author_id=demo_user.id,
            body="Добро пожаловать в командный проект. Здесь можно обсуждать задачи, хранить файлы и распределять работу.",
        ))
        db.commit()
        logger.info("Demo team project inserted")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    upgrade_schema()
    upgrade_legacy_users_auth()
    seed()
    seed_projects()
    yield


app = FastAPI(
    title="Smart Student Workspace API",
    version="5.0.0",
    description=(
        "REST API for the student workspace diploma project.\n\n"
        "**Database:** PostgreSQL\n"
        "**Authentication:** bearer token\n"
        "**Collaboration:** team projects, tasks, files and chat\n"
        "**Assistant:** Workspace AI\n"
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(assignments.router)
app.include_router(schedule.router)
app.include_router(projects.router)
app.include_router(ai.router)
