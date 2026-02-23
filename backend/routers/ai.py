"""
AI Router — endpoints backed by GigaChat
─────────────────────────────────────────
POST /ai/chat                — general chat (history-aware)
POST /ai/courses/{id}/plan   — generate study plan for a course
POST /ai/assignments/{id}/help — get structured help for an assignment
GET  /ai/models              — list available GigaChat models
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from gigachat import chat_complete, list_models, Message
import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


# ── Pydantic schemas ──────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str     # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 1024


class ChatResponse(BaseModel):
    reply: str


class PlanRequest(BaseModel):
    extra_context: str = ""   # optional user notes


class PlanResponse(BaseModel):
    plan: str


class HelpRequest(BaseModel):
    question: str = ""        # optional specific question about the assignment


class HelpResponse(BaseModel):
    advice: str


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    """
    General-purpose chat with GigaChat.
    Prepends a system message positioning GigaChat as a student assistant.
    """
    system = Message(
        role="system",
        content=(
            "Ты — умный ИИ-ассистент платформы «Smart Student Workspace». "
            "Помогаешь студентам разбираться в учебном материале, "
            "объяснять сложные темы простым языком, составлять планы "
            "подготовки и давать советы по учёбе. "
            "Отвечай кратко, структурированно, на русском языке."
        ),
    )
    history = [Message(role=m.role, content=m.content) for m in req.messages]

    try:
        reply = await chat_complete(
            [system, *history],
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except Exception as exc:
        logger.exception("GigaChat chat error")
        raise HTTPException(502, f"GigaChat error: {exc}") from exc

    return ChatResponse(reply=reply)


@router.post("/courses/{course_id}/plan", response_model=PlanResponse)
async def generate_study_plan(
    course_id: int,
    req: PlanRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a personalised study plan for a course.
    Passes course name, teacher, semester and pending assignments to GigaChat.
    """
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")

    pending = [
        a for a in course.assignments
        if a.status in ("pending", "progress", "overdue")
    ]
    pending_text = "\n".join(
        f"  - «{a.title}» (дедлайн: {a.deadline}, статус: {a.status})"
        for a in pending
    ) or "  (нет активных заданий)"

    prompt = (
        f"Курс: «{course.name}»\n"
        f"Преподаватель: {course.teacher}\n"
        f"Семестр: {course.semester}\n"
        f"Текущий прогресс: {course.progress:.0f}%\n"
        f"Активные задания:\n{pending_text}\n"
        + (f"\nДополнительный контекст от студента: {req.extra_context}\n" if req.extra_context else "")
        + "\nСоставь подробный учебный план для успешного освоения курса. "
          "Раздели план на фазы (неделями), укажи конкретные задачи для каждой фазы. "
          "Добавь советы по эффективному обучению. Ответь в формате Markdown."
    )

    try:
        plan = await chat_complete(
            [
                Message(role="system", content="Ты опытный академический ментор. Составляй чёткие учебные планы."),
                Message(role="user",   content=prompt),
            ],
            temperature=0.6,
            max_tokens=1500,
        )
    except Exception as exc:
        logger.exception("GigaChat plan error")
        raise HTTPException(502, f"GigaChat error: {exc}") from exc

    return PlanResponse(plan=plan)


@router.post("/assignments/{assignment_id}/help", response_model=HelpResponse)
async def assignment_help(
    assignment_id: int,
    req: HelpRequest,
    db: Session = Depends(get_db),
):
    """
    Give structured advice for completing a specific assignment.
    """
    assignment = db.get(models.Assignment, assignment_id)
    if not assignment:
        raise HTTPException(404, "Assignment not found")

    course = db.get(models.Course, assignment.course_id)
    course_name = course.name if course else "неизвестный курс"

    prompt = (
        f"Задание: «{assignment.title}»\n"
        f"Курс: {course_name}\n"
        f"Описание задания: {assignment.description}\n"
        f"Дедлайн: {assignment.deadline}\n"
        f"Текущий статус: {assignment.status}\n"
        + (f"Вопрос студента: {req.question}\n" if req.question else "")
        + "\nДай студенту чёткий план выполнения этого задания: "
          "1) с чего начать, 2) ключевые шаги, 3) на что обратить внимание, "
          "4) как уложиться в дедлайн. Ответь структурированно."
    )

    try:
        advice = await chat_complete(
            [
                Message(role="system", content="Ты помощник студента. Давай конкретные, практичные советы."),
                Message(role="user",   content=prompt),
            ],
            temperature=0.5,
            max_tokens=900,
        )
    except Exception as exc:
        logger.exception("GigaChat help error")
        raise HTTPException(502, f"GigaChat error: {exc}") from exc

    return HelpResponse(advice=advice)


@router.get("/models")
async def get_models():
    """Return available GigaChat models."""
    try:
        return await list_models()
    except Exception as exc:
        raise HTTPException(502, f"GigaChat error: {exc}") from exc
