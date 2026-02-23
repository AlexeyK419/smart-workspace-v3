"""
Smart Student Workspace — FastAPI backend v3
  • PostgreSQL via SQLAlchemy 2
  • GigaChat LLM integration
  • File uploads (materials + assignments)

Run:
  uvicorn main:app --reload --port 8000
Docs:
  http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, SessionLocal
import models
from routers import users, courses, materials, assignments, ai

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


# ── DB init + seed ────────────────────────────────────────────
def init_db():
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")


def seed():
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            return
        user = models.User(name="Алексей Иванов", initials="АИ", role="2-й курс · ИТ")
        db.add(user)
        db.flush()

        db.add_all([
            models.Course(user_id=user.id, name="Алгоритмы и структуры данных",
                color="#3d52d5", emoji="⚙️", teacher="Проф. Морозов А.В.",
                semester="Весна 2025", credits=4, progress=72,
                assignments=[
                    models.Assignment(title="Реализация красно-чёрного дерева",
                        description="Реализовать структуру данных «красно-чёрное дерево» с операциями вставки, удаления и поиска.",
                        deadline="28 фев 2025", status="progress"),
                    models.Assignment(title="Анализ сложности алгоритмов",
                        description="Письменный анализ 5 алгоритмов с доказательством временной и пространственной сложности.",
                        deadline="10 мар 2025", status="pending"),
                ]),
            models.Course(user_id=user.id, name="Базы данных",
                color="#2d7a4f", emoji="🗄️", teacher="Доц. Сидорова К.И.",
                semester="Весна 2025", credits=3, progress=55,
                assignments=[
                    models.Assignment(title="Проектирование схемы БД",
                        description="Разработать нормализованную схему БД для интернет-магазина.",
                        deadline="5 мар 2025", status="done"),
                    models.Assignment(title="SQL-запросы",
                        description="Написать 20 SQL-запросов различной сложности.",
                        deadline="20 мар 2025", status="progress"),
                ]),
            models.Course(user_id=user.id, name="Теория вероятностей",
                color="#b45309", emoji="📊", teacher="Проф. Ковалёв Н.П.",
                semester="Весна 2025", credits=3, progress=40,
                assignments=[
                    models.Assignment(title="Контрольная работа №2",
                        description="Решение задач: мат. ожидание, дисперсия, законы распределения.",
                        deadline="1 мар 2025", status="overdue"),
                ]),
            models.Course(user_id=user.id, name="Английский язык",
                color="#0891b2", emoji="🌐", teacher="Ст. преп. Фролова О.С.",
                semester="Весна 2025", credits=2, progress=88,
                assignments=[
                    models.Assignment(title='Эссе "Technology in Education"',
                        description="Эссе 500–600 слов о влиянии технологий на образование.",
                        deadline="25 фев 2025", status="progress"),
                ]),
        ])
        db.commit()
        logger.info("✅ Seed data inserted (user id=1)")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Student Workspace API",
    version="3.0.0",
    description=(
        "REST API for the student workspace diploma project.\n\n"
        "**Database:** PostgreSQL\n"
        "**LLM:** GigaChat (Sberbank)\n\n"
        "Set credentials in `backend/.env` (copy from `.env.example`)."
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

# ── Routers ───────────────────────────────────────────────────
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(assignments.router)
app.include_router(ai.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "db": settings.database_url.split("@")[-1]}
