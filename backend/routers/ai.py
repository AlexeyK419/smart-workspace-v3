"""
AI Router — endpoints backed by the workspace assistant.
All user-specific endpoints are protected and return only the current user's data.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_assignment_for_user_or_404, get_course_for_user_or_404, get_current_user
from database import get_db
from gigachat import chat_complete, list_models, Message
import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


def _extract_file_text(file_path: str | None, max_chars: int = 3000) -> str:
    if not file_path or not os.path.exists(file_path):
        return ""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in (".txt", ".md", ".csv", ".py", ".js", ".html", ".css", ".json", ".xml"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(max_chars)
        if ext == ".odt":
            return _read_odt(file_path, max_chars)
    except Exception:
        pass
    return ""


def _read_odt(path: str, max_chars: int) -> str:
    import zipfile
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(path) as z:
        with z.open("content.xml") as f:
            tree = ET.parse(f)
    texts = []
    for elem in tree.iter():
        if elem.text:
            texts.append(elem.text)
    return " ".join(texts)[:max_chars]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 0.7
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


NO_DIRECT_ANSWERS = (
    "ВАЖНОЕ ПРАВИЛО: Ты НИКОГДА не даёшь готовых решений, ответов на задания, "
    "готового кода или прямых ответов на вопросы заданий. "
    "Вместо этого ты подсказываешь направление, объясняешь концепции, "
    "даёшь план действий и наводящие вопросы, чтобы студент пришёл к ответу сам. "
    "Если студент просит дать готовое решение — вежливо откажи и предложи помочь разобраться."
)

SYSTEM_CHAT = (
    "Ты — умный ИИ-ассистент платформы «Smart Student Workspace». "
    "Помогаешь студентам разбираться в учебном материале, "
    "объяснять сложные темы простым языком, составлять планы "
    "подготовки и давать советы по учёбе. "
    "Отвечай кратко, структурированно, на русском языке. "
    + NO_DIRECT_ANSWERS
)

SYSTEM_PLAN = "Ты опытный академический ментор. Составляй чёткие учебные планы. " + NO_DIRECT_ANSWERS
SYSTEM_HELP = "Ты помощник студента. Давай конкретные, практичные советы. " + NO_DIRECT_ANSWERS


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    req: ChatRequest,
    current_user: models.User = Depends(get_current_user),
):
    _ = current_user
    system = Message(role="system", content=SYSTEM_CHAT)
    history = [Message(role=m.role, content=m.content) for m in req.messages]
    try:
        reply = await chat_complete(
            [system, *history],
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
    course = get_course_for_user_or_404(course_id, current_user.id, db)

    all_assignments = course.assignments or []
    assignments_text = ""
    for assignment in all_assignments:
        line = f"  - «{assignment.title}» (дедлайн: {assignment.deadline}, статус: {assignment.status})"
        if assignment.description:
            line += f"\n    Описание: {assignment.description}"
        file_content = _extract_file_text(assignment.file_path)
        if file_content:
            line += f"\n    Содержимое файла: {file_content[:1000]}"
        assignments_text += line + "\n"
    if not assignments_text.strip():
        assignments_text = "  (нет заданий)\n"

    materials = course.materials or []
    materials_text = ""
    for material in materials:
        materials_text += f"  - {material.name} ({material.mime_type}, {material.size_bytes} байт)\n"
        file_content = _extract_file_text(material.file_path)
        if file_content:
            materials_text += f"    Содержимое: {file_content[:1000]}\n"
    if not materials_text.strip():
        materials_text = "  (нет материалов)\n"

    prompt = (
        f"Курс: «{course.name}»\n"
        f"Преподаватель: {course.teacher}\n"
        f"Семестр: {course.semester}\n"
        f"Кредиты: {course.credits}\n"
        f"Текущий прогресс: {course.progress:.0f}%\n\n"
        f"Материалы курса:\n{materials_text}\n"
        f"Задания курса:\n{assignments_text}\n"
        + (f"Дополнительный контекст от студента: {req.extra_context}\n" if req.extra_context else "")
        + "\nСоставь подробный учебный план для успешного освоения курса. "
        "Раздели план на фазы (неделями), укажи конкретные задачи для каждой фазы. "
        "Учитывай все перечисленные задания и материалы. "
        "Добавь советы по эффективному обучению. Ответь в формате Markdown."
    )

    try:
        plan = await chat_complete(
            [
                Message(role="system", content=SYSTEM_PLAN),
                Message(role="user", content=prompt),
            ],
            temperature=0.6,
            max_tokens=2000,
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
    course = db.get(models.Course, assignment.course_id)
    course_name = course.name if course else "неизвестный курс"

    file_context = ""
    file_content = _extract_file_text(assignment.file_path)
    if file_content:
        file_context = f"\nСодержимое приложенного файла ({assignment.file_name}):\n{file_content}\n"

    prompt = (
        f"Задание: «{assignment.title}»\n"
        f"Курс: {course_name}\n"
        f"Описание задания: {assignment.description}\n"
        + file_context
        + f"Дедлайн: {assignment.deadline}\n"
        f"Текущий статус: {assignment.status}\n"
        + (f"Вопрос студента: {req.question}\n" if req.question else "")
        + "\nДай студенту подсказки и план действий для выполнения этого задания: "
        "1) с чего начать, 2) ключевые шаги, 3) на что обратить внимание, "
        "4) как уложиться в дедлайн. "
        "НЕ давай готовое решение. Ответь структурированно."
    )

    try:
        advice = await chat_complete(
            [
                Message(role="system", content=SYSTEM_HELP),
                Message(role="user", content=prompt),
            ],
            temperature=0.5,
            max_tokens=1200,
        )
    except Exception as exc:
        logger.exception("AI help error")
        raise HTTPException(502, f"Ошибка AI-сервиса: {exc}") from exc

    assignment.ai_advice = advice
    db.commit()
    return HelpResponse(advice=advice)


@router.get("/models")
async def get_models(current_user: models.User = Depends(get_current_user)):
    _ = current_user
    try:
        return await list_models()
    except Exception as exc:
        raise HTTPException(502, f"Ошибка AI-сервиса: {exc}") from exc
