"""
AI Router - endpoints for workspace assistant.
All user-specific endpoints are protected and return only data available to current user.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from ai_context import (
    build_assignment_help_context,
    build_chat_context,
    build_course_plan_context,
    build_project_context,
    build_workspace_context,
)
from auth import (
    get_assignment_for_user_or_404,
    get_course_for_user_or_404,
    get_current_user,
)
from database import get_db
from llm_provider import Message, chat_complete, list_models
import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 0.6
    max_tokens: int = 1024


class ChatResponse(BaseModel):
    reply: str


class PlanRequest(BaseModel):
    extra_context: str = ""


class PlanResponse(BaseModel):
    plan: str


class HelpRequest(BaseModel):
    question: str = ""


class HelpResponse(BaseModel):
    advice: str


class SummaryResponse(BaseModel):
    summary: str


COMMON_STYLE_RULES = """
Общие правила ответа:
- Пиши только на русском языке.
- Пиши кратко, по делу, без воды и повторов.
- Используй короткие секции и списки.
- Не выдумывай факты, комментарии, файлы и сообщения, которых нет в контексте.
- Если данных недостаточно, честно скажи об этом.
- Давай максимум пользы на единицу текста: фокус, риски, конкретные действия.
""".strip()

NO_DIRECT_ASSIGNMENT_SOLUTIONS = """
Критическое правило для задач и учебных активностей:
- Не давай готовое решение задания, готовый код, готовые ответы.
- Помогай понять задачу, разбить на шаги и проверить себя.
""".strip()

SYSTEM_CHAT = (
    "Ты — AI-ассистент платформы Smart Student Workspace. "
    "Помогаешь учиться, планировать нагрузку и принимать приоритетные решения на основе фактического контекста.\n\n"
    f"{COMMON_STYLE_RULES}\n\n{NO_DIRECT_ASSIGNMENT_SOLUTIONS}"
)

SYSTEM_PLAN = (
    "Ты — академический наставник. Составляешь реалистичный и компактный план обучения по курсу, "
    "с учетом материалов, заданий, дедлайнов и текущего статуса.\n\n"
    f"{COMMON_STYLE_RULES}\n\n{NO_DIRECT_ASSIGNMENT_SOLUTIONS}"
)

SYSTEM_HELP = (
    "Ты — помощник по учебному заданию. Объясняешь смысл задания и путь выполнения без выдачи готового решения.\n\n"
    f"{COMMON_STYLE_RULES}\n\n{NO_DIRECT_ASSIGNMENT_SOLUTIONS}"
)

SYSTEM_WORKSPACE_SUMMARY = (
    "Ты — AI-аналитик workspace студента. Формируешь краткую рабочую сводку по учебе и проектам.\n\n"
    f"{COMMON_STYLE_RULES}"
)

SYSTEM_PROJECT_SUMMARY = (
    "Ты — AI-аналитик командного проекта. Даешь короткую управленческую сводку состояния проекта и рисков.\n\n"
    f"{COMMON_STYLE_RULES}"
)


def _course_with_details_for_user(course_id: int, user_id: int, db: Session) -> models.Course:
    course = (
        db.query(models.Course)
        .options(
            selectinload(models.Course.materials),
            selectinload(models.Course.assignments),
        )
        .filter(models.Course.id == course_id, models.Course.user_id == user_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return course


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    req: ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    context_text = build_chat_context(db, current_user.id)
    system_messages = [
        Message(role="system", content=SYSTEM_CHAT),
        Message(
            role="system",
            content=(
                "Фактический контекст workspace пользователя. "
                "Используй его как источник фактов, не выдумывай данные:\n\n"
                f"{context_text}"
            ),
        ),
    ]
    history = [Message(role=m.role, content=m.content) for m in req.messages]

    try:
        reply = await chat_complete(
            [*system_messages, *history],
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except Exception as exc:
        logger.exception("AI chat error")
        raise HTTPException(502, f"Ошибка AI-сервиса: {exc}") from exc

    return ChatResponse(reply=reply)


@router.post("/courses/{course_id}/plan", response_model=PlanResponse)
async def generate_study_plan(
    course_id: int,
    req: PlanRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_course_for_user_or_404(course_id, current_user.id, db)
    course = _course_with_details_for_user(course_id, current_user.id, db)
    context_text = build_course_plan_context(course, req.extra_context)

    user_prompt = (
        "Составь компактный учебный план по курсу на основе фактического контекста ниже.\n"
        "Формат ответа:\n"
        "Приоритеты\n"
        "Этапы\n"
        "Ближайшие действия\n"
        "Советы по темпу\n\n"
        "Требования: кратко, структурно, без повторов, без готовых решений заданий.\n\n"
        f"Контекст:\n{context_text}"
    )

    try:
        plan = await chat_complete(
            [
                Message(role="system", content=SYSTEM_PLAN),
                Message(role="user", content=user_prompt),
            ],
            temperature=0.45,
            max_tokens=1700,
        )
    except Exception as exc:
        logger.exception("AI plan error")
        raise HTTPException(502, f"Ошибка AI-сервиса: {exc}") from exc

    course.ai_plan = plan
    db.commit()
    return PlanResponse(plan=plan)


@router.post("/assignments/{assignment_id}/help", response_model=HelpResponse)
async def assignment_help(
    assignment_id: int,
    req: HelpRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = get_assignment_for_user_or_404(assignment_id, current_user.id, db)
    course = _course_with_details_for_user(assignment.course_id, current_user.id, db)
    context_text = build_assignment_help_context(assignment, course)

    question_block = f"Вопрос пользователя: {req.question.strip()}\n\n" if req.question.strip() else ""
    user_prompt = (
        "Дай помощь по заданию строго в формате:\n"
        "Что означает задание\n"
        "С чего начать\n"
        "Шаги\n"
        "На что обратить внимание\n\n"
        "Требования: кратко, конкретно, без воды, без готового решения.\n"
        "Если данных мало — прямо укажи это.\n\n"
        f"{question_block}"
        f"Контекст:\n{context_text}"
    )

    try:
        advice = await chat_complete(
            [
                Message(role="system", content=SYSTEM_HELP),
                Message(role="user", content=user_prompt),
            ],
            temperature=0.35,
            max_tokens=1300,
        )
    except Exception as exc:
        logger.exception("AI help error")
        raise HTTPException(502, f"Ошибка AI-сервиса: {exc}") from exc

    assignment.ai_advice = advice
    db.commit()
    return HelpResponse(advice=advice)


@router.post("/workspace/summary", response_model=SummaryResponse)
async def workspace_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    context_text = build_workspace_context(db, current_user.id)
    user_prompt = (
        "Сформируй AI-сводку workspace строго в формате:\n"
        "Фокус\n"
        "Что сделать сейчас\n"
        "Риски\n"
        "Совет\n\n"
        "Учитывай: ближайшие дедлайны, просрочки, сегодняшнее расписание, "
        "ближайшие проектные задачи, конфликты сроков и приоритизацию.\n"
        "Пиши кратко и конкретно.\n\n"
        f"Контекст:\n{context_text}"
    )

    try:
        summary = await chat_complete(
            [
                Message(role="system", content=SYSTEM_WORKSPACE_SUMMARY),
                Message(role="user", content=user_prompt),
            ],
            temperature=0.3,
            max_tokens=1300,
        )
    except Exception as exc:
        logger.exception("AI workspace summary error")
        raise HTTPException(502, f"Ошибка AI-сервиса: {exc}") from exc

    return SummaryResponse(summary=summary)


@router.post("/projects/{project_id}/summary", response_model=SummaryResponse)
async def project_summary(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    context_text = build_project_context(db, project_id, current_user.id)
    if context_text is None:
        raise HTTPException(status_code=404, detail="Проект не найден")

    user_prompt = (
        "Сформируй AI-сводку проекта строго в формате:\n"
        "Состояние проекта\n"
        "Ближайшие действия команды\n"
        "Риски\n"
        "Координация\n\n"
        "Учитывай: статусы, дедлайны, ответственных, просрочки, риски, "
        "дисбаланс нагрузки, комментарии, файлы и последние сообщения проекта.\n"
        "Пиши кратко и по делу.\n\n"
        f"Контекст:\n{context_text}"
    )

    try:
        summary = await chat_complete(
            [
                Message(role="system", content=SYSTEM_PROJECT_SUMMARY),
                Message(role="user", content=user_prompt),
            ],
            temperature=0.3,
            max_tokens=1300,
        )
    except Exception as exc:
        logger.exception("AI project summary error")
        raise HTTPException(502, f"Ошибка AI-сервиса: {exc}") from exc

    return SummaryResponse(summary=summary)


@router.get("/models")
async def get_models(current_user: models.User = Depends(get_current_user)):
    _ = current_user
    try:
        return await list_models()
    except Exception as exc:
        raise HTTPException(502, f"Ошибка AI-сервиса: {exc}") from exc
