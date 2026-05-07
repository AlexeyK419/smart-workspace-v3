from __future__ import annotations

import os
import re
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session, selectinload

import models
from ai_embeddings import (
    ContextSource,
    ensure_context_sources_indexed,
    prune_stale_context_sources,
    render_semantic_hits,
    semantic_search_context,
)
from file_utils import read_file_text_raw, TEXT_EXTENSIONS, FILE_READ_LIMIT

WORKSPACE_SUMMARY_CONTEXT_CHAR_LIMIT = 30_000
CHAT_CONTEXT_CHAR_LIMIT = 22_000
PROJECT_SUMMARY_CONTEXT_CHAR_LIMIT = 24_000
COURSE_PLAN_CONTEXT_CHAR_LIMIT = 22_000
ASSIGNMENT_HELP_CONTEXT_CHAR_LIMIT = 18_000

CHAT_RECENT_MESSAGES_LIMIT = 8
CHAT_OLD_HISTORY_SUMMARY_LIMIT = 2_600

MAX_COURSES_IN_CONTEXT = 4
MAX_ASSIGNMENTS_IN_CONTEXT = 5
MAX_PROJECTS_IN_CONTEXT = 3
MAX_TASKS_IN_CONTEXT = 8
MAX_FILES_IN_CONTEXT = 4
MAX_PROJECT_SIGNALS = 8

FILE_CACHE_MAX_ITEMS = 256
RAW_FILE_TAIL_BUDGET = 1_200
EXCERPT_DEFAULT_MAX_CHARS = 900

BUDGET_FACTS = 10
BUDGET_ENTITIES = 20
BUDGET_EXCERPTS = 30
BUDGET_RAW_TEXT = 40

_CHAT_ROUTE_STUDY_GENERAL = "study_general"
_CHAT_ROUTE_COURSE = "course"
_CHAT_ROUTE_ASSIGNMENT = "assignment"
_CHAT_ROUTE_SCHEDULE_DEADLINE = "schedule_deadline"
_CHAT_ROUTE_PROJECT = "project"
_CHAT_ROUTE_PLANNING_PRODUCTIVITY = "planning_productivity"

CHAT_ROUTE_LABELS: dict[str, str] = {
    _CHAT_ROUTE_STUDY_GENERAL: "Учеба в целом",
    _CHAT_ROUTE_COURSE: "Конкретный курс",
    _CHAT_ROUTE_ASSIGNMENT: "Конкретное задание",
    _CHAT_ROUTE_SCHEDULE_DEADLINE: "Расписание/дедлайны",
    _CHAT_ROUTE_PROJECT: "Проект",
    _CHAT_ROUTE_PLANNING_PRODUCTIVITY: "Планирование/продуктивность",
}

_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9_]{2,}")

_STOPWORDS = {
    "и", "или", "но", "а", "да", "нет", "что", "как", "это", "эта", "этот", "эти",
    "меня", "мне", "мы", "вы", "они", "она", "он", "его", "ее", "их", "у", "в", "во",
    "на", "по", "к", "ко", "с", "со", "из", "за", "для", "до", "от", "под", "над", "без",
    "же", "ли", "бы", "ну", "давай", "нужно", "надо", "can", "could", "would", "should",
    "the", "a", "an", "to", "for", "and", "or", "in", "on", "at", "is", "are", "be",
    "with", "of", "from", "about", "help", "please",
}

_FILE_TEXT_CACHE: OrderedDict[tuple[str, int, float], str] = OrderedDict()


@dataclass
class ChatHistoryMessage:
    role: str
    content: str


@dataclass
class ChatContextPackage:
    route: str
    route_label: str
    route_reason: str
    keywords: list[str]
    context_text: str
    recent_messages: list[ChatHistoryMessage]
    older_history_summary: str


@dataclass
class _ContextBlock:
    priority: int
    order: int
    title: str
    text: str


@dataclass
class DerivedFacts:
    overdue: list[str]
    upcoming: list[str]
    today_events: list[str]
    conflicts: list[str]
    assignee_load: list[str]
    blockers: list[str]


class PriorityContextAssembler:
    def __init__(self, max_chars: int):
        self.max_chars = max_chars
        self._counter = 0
        self._blocks: list[_ContextBlock] = []

    def add(self, title: str, text: str, priority: int) -> None:
        if not text:
            return
        self._counter += 1
        self._blocks.append(_ContextBlock(priority=priority, order=self._counter, title=title, text=text.strip()))

    def build(self, preface: str = "") -> str:
        chunks: list[str] = []
        used = 0

        if preface:
            clipped_preface = _clip(preface.strip(), self.max_chars)
            chunks.append(clipped_preface + "\n\n")
            used = len(chunks[0])

        for block in sorted(self._blocks, key=lambda item: (item.priority, item.order)):
            if used >= self.max_chars:
                break

            section = f"### {block.title}\n{block.text}\n\n"
            remaining = self.max_chars - used

            if len(section) <= remaining:
                chunks.append(section)
                used += len(section)
                continue

            clipped = _clip(section, remaining)
            if clipped:
                chunks.append(clipped)
            break

        return "".join(chunks).strip()


def _clip(text: str | None, max_chars: int) -> str:
    if not text or max_chars <= 0:
        return ""
    value = text.strip()
    if len(value) <= max_chars:
        return value
    marker = "\n...[контекст усечен]"
    reserve = len(marker) + 4
    limit = max(0, max_chars - reserve)
    return f"{value[:limit].rstrip()}{marker}"


def _fmt_dt(value: datetime | None) -> str:
    if not value:
        return "—"
    return value.strftime("%d.%m.%Y %H:%M")


def _fmt_day_index(day_index: int) -> str:
    names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    if 0 <= day_index < len(names):
        return names[day_index]
    return f"День {day_index}"


def _fmt_assignment_status(status: str | None) -> str:
    labels = {"pending": "ожидает", "progress": "в процессе", "done": "выполнено", "overdue": "просрочено"}
    return labels.get((status or "").strip(), status or "не указан")


def _fmt_task_status(status: str | None) -> str:
    labels = {"todo": "к выполнению", "in_progress": "в работе", "done": "выполнено"}
    return labels.get((status or "").strip(), status or "не указан")


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def _to_text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def extract_keywords(text: str, max_keywords: int = 16) -> list[str]:
    lowered = _to_text(text).casefold()
    if not lowered:
        return []

    counts: Counter[str] = Counter()
    for token in _WORD_RE.findall(lowered):
        normalized = token.strip("_")
        if len(normalized) < 3 or normalized in _STOPWORDS:
            continue
        counts[normalized] += 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [word for word, _ in ordered[:max_keywords]]


def _text_match_score(text: str, keywords: list[str]) -> int:
    value = _to_text(text).casefold()
    if not value or not keywords:
        return 0
    return sum(1 for keyword in keywords if keyword in value)


def _match_name_in_text(name: str, text: str) -> bool:
    left = _to_text(name).casefold().strip()
    right = _to_text(text).casefold()
    return bool(left and right and left in right)

def _get_file_cache_key(file_path: str) -> tuple[str, int, float] | None:
    if not file_path or not os.path.exists(file_path):
        return None
    stat = os.stat(file_path)
    return (os.path.abspath(file_path), int(stat.st_size), float(stat.st_mtime))


def _get_cached_file_text(file_path: str | None) -> tuple[str, str]:
    if not file_path:
        return "", "файл не прикреплен"

    key = _get_file_cache_key(file_path)
    if key is None:
        return "", "файл отсутствует на диске"

    cached = _FILE_TEXT_CACHE.get(key)
    if cached is not None:
        _FILE_TEXT_CACHE.move_to_end(key)
        return cached, "ok"

    text, state = read_file_text_raw(file_path)
    if not text:
        return "", state

    _FILE_TEXT_CACHE[key] = text
    _FILE_TEXT_CACHE.move_to_end(key)

    while len(_FILE_TEXT_CACHE) > FILE_CACHE_MAX_ITEMS:
        _FILE_TEXT_CACHE.popitem(last=False)

    return text, "ok"


def _slice_windows_around_matches(
    text: str,
    keywords: list[str],
    *,
    window_chars: int,
    max_windows: int,
) -> list[tuple[int, int]]:
    if not keywords or not text:
        return []

    lowered = text.casefold()
    positions: list[int] = []

    for keyword in keywords:
        start = 0
        hits = 0
        while hits < 2:
            idx = lowered.find(keyword, start)
            if idx < 0:
                break
            positions.append(idx)
            hits += 1
            start = idx + len(keyword)

    if not positions:
        return []

    half = max(120, window_chars // 2)
    raw_windows: list[tuple[int, int]] = []
    for idx in sorted(positions):
        raw_windows.append((max(0, idx - half), min(len(text), idx + half)))

    merged: list[tuple[int, int]] = []
    for left, right in raw_windows:
        if not merged:
            merged.append((left, right))
            continue
        prev_left, prev_right = merged[-1]
        if left <= prev_right + 80:
            merged[-1] = (prev_left, max(prev_right, right))
        else:
            merged.append((left, right))

    return merged[:max_windows]


def select_keyword_excerpt(
    text: str,
    keywords: list[str],
    *,
    max_chars: int = EXCERPT_DEFAULT_MAX_CHARS,
    window_chars: int = 420,
    max_windows: int = 3,
) -> str:
    clean = _to_text(text)
    if not clean:
        return ""

    if len(clean) <= max_chars:
        return clean.strip()

    windows = _slice_windows_around_matches(clean, keywords, window_chars=window_chars, max_windows=max_windows)
    if not windows:
        return _clip(clean, max_chars)

    chunks: list[str] = []
    for index, (left, right) in enumerate(windows):
        excerpt = clean[left:right].strip()
        if not excerpt:
            continue
        prefix = "..." if left > 0 else ""
        suffix = "..." if right < len(clean) else ""
        if index > 0:
            chunks.append("\n---\n")
        chunks.append(f"{prefix}{excerpt}{suffix}")

    return _clip("".join(chunks), max_chars)


def extract_file_excerpt(
    file_path: str | None,
    keywords: list[str],
    *,
    max_chars: int = EXCERPT_DEFAULT_MAX_CHARS,
) -> tuple[str, str]:
    raw_text, state = _get_cached_file_text(file_path)
    if not raw_text:
        return "", state
    return select_keyword_excerpt(raw_text, keywords, max_chars=max_chars), "ok"


def extract_file_text(file_path: str | None, max_chars: int) -> tuple[str, str]:
    raw_text, state = _get_cached_file_text(file_path)
    if not raw_text:
        return "", state
    return _clip(raw_text, max_chars), "ok"


def _file_text_for_index(file_path: str | None) -> str:
    text, _ = extract_file_text(file_path, FILE_READ_LIMIT)
    return text


def _collect_course_semantic_sources(user_id: int, courses: list[models.Course]) -> list[ContextSource]:
    sources: list[ContextSource] = []
    for course in courses:
        course_bits = [
            f"Course: {course.name}",
            f"Teacher: {course.teacher or ''}",
            f"Semester: {course.semester or ''}",
            f"Progress: {course.progress:.0f}%",
        ]
        sources.append(
            ContextSource(
                user_id=user_id,
                scope="course",
                entity_type="course",
                entity_id=course.id,
                parent_type="course",
                parent_id=course.id,
                title=f"Курс «{course.name}»",
                text="\n".join(course_bits),
                metadata={"course_id": course.id},
            )
        )

        for material in course.materials or []:
            file_text = _file_text_for_index(material.file_path)
            if not file_text:
                continue
            sources.append(
                ContextSource(
                    user_id=user_id,
                    scope="course",
                    entity_type="material",
                    entity_id=material.id,
                    parent_type="course",
                    parent_id=course.id,
                    title=f"Материал «{material.name}» / курс «{course.name}»",
                    text=file_text,
                    metadata={
                        "course_id": course.id,
                        "course_name": course.name,
                        "material_id": material.id,
                        "file_name": material.name,
                    },
                )
            )

        for assignment in course.assignments or []:
            file_text = _file_text_for_index(assignment.file_path)
            text = "\n".join(
                part
                for part in [
                    f"Assignment: {assignment.title}",
                    f"Course: {course.name}",
                    f"Status: {assignment.status}",
                    f"Deadline: {assignment.deadline or _fmt_dt(assignment.deadline_dt)}",
                    f"Description: {assignment.description or ''}",
                    f"Attached file: {assignment.file_name or ''}",
                    file_text,
                ]
                if part.strip()
            )
            if not text.strip():
                continue
            sources.append(
                ContextSource(
                    user_id=user_id,
                    scope="course",
                    entity_type="assignment",
                    entity_id=assignment.id,
                    parent_type="course",
                    parent_id=course.id,
                    title=f"Задание «{assignment.title}» / курс «{course.name}»",
                    text=text,
                    metadata={
                        "course_id": course.id,
                        "course_name": course.name,
                        "assignment_id": assignment.id,
                        "assignment_title": assignment.title,
                    },
                )
            )
    return sources


def _collect_project_semantic_sources(user_id: int, projects: list[models.Project]) -> list[ContextSource]:
    sources: list[ContextSource] = []
    for project in projects:
        sources.append(
            ContextSource(
                user_id=user_id,
                scope="project",
                entity_type="project",
                entity_id=project.id,
                parent_type="project",
                parent_id=project.id,
                title=f"Проект «{project.name}»",
                text=f"Project: {project.name}\nDescription: {project.description or ''}",
                metadata={"project_id": project.id, "project_name": project.name},
            )
        )

        for task in project.tasks or []:
            comments = []
            for comment in task.comments or []:
                author = comment.author.name if comment.author else ""
                comments.append(f"[{_fmt_dt(comment.created_at)}] {author}: {comment.body}")
            text = "\n".join(
                part
                for part in [
                    f"Task: {task.title}",
                    f"Project: {project.name}",
                    f"Status: {task.status}",
                    f"Due date: {_fmt_dt(task.due_date)}",
                    f"Assignee: {task.assignee.name if task.assignee else ''}",
                    f"Description: {task.description or ''}",
                    "\n".join(comments),
                ]
                if part.strip()
            )
            sources.append(
                ContextSource(
                    user_id=user_id,
                    scope="project",
                    entity_type="project_task",
                    entity_id=task.id,
                    parent_type="project",
                    parent_id=project.id,
                    title=f"Задача «{task.title}» / проект «{project.name}»",
                    text=text,
                    metadata={"project_id": project.id, "project_name": project.name, "task_id": task.id},
                )
            )

        for file_item in project.files or []:
            file_text = _file_text_for_index(file_item.file_path)
            if not file_text:
                continue
            sources.append(
                ContextSource(
                    user_id=user_id,
                    scope="project",
                    entity_type="project_file",
                    entity_id=file_item.id,
                    parent_type="project",
                    parent_id=project.id,
                    title=f"Файл «{file_item.name}» / проект «{project.name}»",
                    text=file_text,
                    metadata={"project_id": project.id, "project_name": project.name, "file_id": file_item.id},
                )
            )

        for message in project.messages or []:
            author = message.author.name if message.author else ""
            sources.append(
                ContextSource(
                    user_id=user_id,
                    scope="project",
                    entity_type="project_message",
                    entity_id=message.id,
                    parent_type="project",
                    parent_id=project.id,
                    title=f"Сообщение проекта «{project.name}» от {author or 'участника'}",
                    text=f"[{_fmt_dt(message.created_at)}] {author}: {message.body}",
                    metadata={"project_id": project.id, "project_name": project.name, "message_id": message.id},
                )
            )
    return sources


def _collect_workspace_semantic_sources(
    user_id: int,
    courses: list[models.Course],
    projects: list[models.Project],
) -> list[ContextSource]:
    return [
        *_collect_course_semantic_sources(user_id, courses),
        *_collect_project_semantic_sources(user_id, projects),
    ]


def _collect_chat_history_semantic_sources(
    user_id: int,
    messages: list[ChatHistoryMessage],
) -> list[ContextSource]:
    sources: list[ContextSource] = []
    for index, message in enumerate(messages):
        content = _normalize_whitespace(message.content)
        if not content:
            continue
        sources.append(
            ContextSource(
                user_id=user_id,
                scope="chat_history",
                entity_type="chat_message",
                entity_id=index,
                title=f"Chat history message #{index + 1} ({message.role})",
                text=f"{message.role}: {content}",
                metadata={"role": message.role, "message_index": index},
            )
        )
    return sources


def _semantic_context_block(
    db: Session,
    *,
    user_id: int,
    query: str,
    sources: list[ContextSource],
    scopes: set[str] | None = None,
    parent_type: str | None = None,
    parent_id: str | int | None = None,
    limit: int = 6,
) -> str:
    if not query.strip():
        return ""
    try:
        prune_stale_context_sources(
            db,
            user_id=user_id,
            sources=sources,
            scopes=scopes,
            parent_type=parent_type,
            parent_id=parent_id,
        )
        ensure_context_sources_indexed(db, sources)
        hits = semantic_search_context(
            db,
            user_id=user_id,
            query=query,
            scopes=scopes,
            parent_type=parent_type,
            parent_id=parent_id,
            limit=limit,
        )
        return render_semantic_hits(hits)
    except Exception:  # pragma: no cover
        return ""


def _course_query(db: Session, user_id: int):
    return (
        db.query(models.Course)
        .options(selectinload(models.Course.materials), selectinload(models.Course.assignments))
        .filter(models.Course.user_id == user_id)
        .order_by(models.Course.id.asc())
    )


def _project_query_for_user(db: Session, user_id: int):
    return (
        db.query(models.Project)
        .options(
            selectinload(models.Project.owner),
            selectinload(models.Project.members).selectinload(models.ProjectMember.user),
            selectinload(models.Project.tasks).selectinload(models.ProjectTask.assignee),
            selectinload(models.Project.tasks).selectinload(models.ProjectTask.creator),
            selectinload(models.Project.tasks)
            .selectinload(models.ProjectTask.comments)
            .selectinload(models.ProjectTaskComment.author),
            selectinload(models.Project.files).selectinload(models.ProjectFile.uploader),
            selectinload(models.Project.messages).selectinload(models.ProjectMessage.author),
        )
        .join(models.ProjectMember, models.ProjectMember.project_id == models.Project.id)
        .filter(models.ProjectMember.user_id == user_id)
        .order_by(models.Project.created_at.desc())
    )


def _project_query_by_id_for_user(db: Session, project_id: int, user_id: int):
    return _project_query_for_user(db, user_id).filter(models.Project.id == project_id)


def _load_workspace_data(
    db: Session,
    user_id: int,
) -> tuple[list[models.Course], list[models.ScheduleEvent], list[models.Project]]:
    courses = _course_query(db, user_id).all()
    schedule_events = (
        db.query(models.ScheduleEvent)
        .filter(models.ScheduleEvent.user_id == user_id)
        .order_by(models.ScheduleEvent.day_index.asc(), models.ScheduleEvent.start_minute.asc())
        .all()
    )
    projects = _project_query_for_user(db, user_id).all()
    return courses, schedule_events, projects

def _nearest_course_deadline(course: models.Course) -> datetime | None:
    now = datetime.now()
    candidates = [
        assignment.deadline_dt
        for assignment in (course.assignments or [])
        if assignment.deadline_dt and assignment.status != "done" and assignment.deadline_dt >= now
    ]
    return min(candidates) if candidates else None


def _nearest_project_deadline(project: models.Project) -> datetime | None:
    now = datetime.now()
    candidates = [
        task.due_date
        for task in (project.tasks or [])
        if task.due_date and task.status != "done" and task.due_date >= now
    ]
    return min(candidates) if candidates else None


def _calc_workspace_derived(
    courses: list[models.Course],
    schedule_events: list[models.ScheduleEvent],
    projects: list[models.Project],
) -> DerivedFacts:
    now = datetime.now()

    overdue: list[tuple[datetime, str]] = []
    upcoming: list[tuple[datetime, str]] = []
    conflicts_map: defaultdict[str, list[str]] = defaultdict(list)
    assignee_load: defaultdict[str, int] = defaultdict(int)
    blockers: list[str] = []

    for course in courses:
        for assignment in course.assignments or []:
            if not assignment.deadline_dt:
                continue
            label = (
                f"Курс «{course.name}»: «{assignment.title}» "
                f"({_fmt_assignment_status(assignment.status)}), до {_fmt_dt(assignment.deadline_dt)}"
            )

            if assignment.status != "done" and assignment.deadline_dt < now:
                overdue.append((assignment.deadline_dt, label))

            if assignment.status != "done" and assignment.deadline_dt >= now:
                upcoming.append((assignment.deadline_dt, label))
                conflicts_map[assignment.deadline_dt.date().isoformat()].append(label)

            if assignment.status != "done" and not (assignment.description or "").strip() and not assignment.file_path:
                blockers.append(
                    f"Курс «{course.name}», задание «{assignment.title}»: мало входных данных (нет описания и файла)."
                )

    for project in projects:
        for task in project.tasks or []:
            assignee_name = task.assignee.name if task.assignee else "Без исполнителя"

            if task.status != "done":
                assignee_load[assignee_name] += 1

            if task.status != "done" and not task.assignee:
                blockers.append(f"Проект «{project.name}», задача «{task.title}»: нет исполнителя.")

            if task.status == "in_progress" and not (task.description or "").strip():
                blockers.append(f"Проект «{project.name}», задача «{task.title}»: в работе без описания.")

            if not task.due_date:
                continue

            label = (
                f"Проект «{project.name}»: «{task.title}» "
                f"({_fmt_task_status(task.status)}, {assignee_name}), до {_fmt_dt(task.due_date)}"
            )

            if task.status != "done" and task.due_date < now:
                overdue.append((task.due_date, label))

            if task.status != "done" and task.due_date >= now:
                upcoming.append((task.due_date, label))
                conflicts_map[task.due_date.date().isoformat()].append(label)

    today_events: list[str] = []
    today_index = now.weekday()
    today_schedule = [item for item in schedule_events if item.day_index == today_index]

    for event in sorted(today_schedule, key=lambda item: item.start_minute):
        start_h = event.start_minute // 60
        start_m = event.start_minute % 60
        end_total = event.start_minute + event.duration_minutes
        end_h = end_total // 60
        end_m = end_total % 60
        today_events.append(
            f"{start_h:02d}:{start_m:02d}–{end_h:02d}:{end_m:02d} — {event.title} ({event.location or 'локация не указана'})"
        )

    sorted_overdue = [item[1] for item in sorted(overdue, key=lambda row: row[0])[:16]]
    sorted_upcoming = [item[1] for item in sorted(upcoming, key=lambda row: row[0])[:20]]

    conflicts: list[str] = []
    for date_key, labels in sorted(conflicts_map.items()):
        if len(labels) < 2:
            continue
        conflicts.append(f"{date_key}: {len(labels)} пересечения")
        for label in labels[:4]:
            conflicts.append(f"- {label}")

    load_lines: list[str] = []
    if assignee_load:
        ordered = sorted(assignee_load.items(), key=lambda row: row[1], reverse=True)
        for name, count in ordered:
            load_lines.append(f"{name}: {count} открытых задач")

        if len(ordered) >= 2:
            max_count = ordered[0][1]
            min_count = ordered[-1][1]
            if max_count - min_count >= 2:
                load_lines.append(
                    f"Признак дисбаланса: у «{ordered[0][0]}» на {max_count - min_count} задач больше, чем у «{ordered[-1][0]}»."
                )

    return DerivedFacts(
        overdue=sorted_overdue,
        upcoming=sorted_upcoming,
        today_events=today_events,
        conflicts=conflicts,
        assignee_load=load_lines,
        blockers=blockers[:14],
    )


def _render_derived_block(derived: DerivedFacts) -> str:
    lines: list[str] = []

    lines.append("Просрочки:")
    lines.extend([f"- {item}" for item in derived.overdue] or ["- Нет."])

    lines.append("\nБлижайшие дедлайны:")
    lines.extend([f"- {item}" for item in derived.upcoming[:12]] or ["- Нет."])

    lines.append("\nРасписание на сегодня:")
    lines.extend([f"- {item}" for item in derived.today_events] or ["- На сегодня занятий нет."])

    lines.append("\nКонфликты сроков:")
    lines.extend([f"- {item}" for item in derived.conflicts[:10]] or ["- Явных пересечений нет."])

    lines.append("\nНагрузка по исполнителям:")
    lines.extend([f"- {item}" for item in derived.assignee_load[:10]] or ["- Недостаточно данных."])

    lines.append("\nБлокеры и узкие места:")
    lines.extend([f"- {item}" for item in derived.blockers[:8]] or ["- Явных блокеров не найдено."])

    return "\n".join(lines)


def _render_workspace_snapshot(
    courses: list[models.Course],
    schedule_events: list[models.ScheduleEvent],
    projects: list[models.Project],
) -> str:
    now = datetime.now()

    open_assignments = sum(
        1 for course in courses for assignment in (course.assignments or []) if assignment.status != "done"
    )
    open_tasks = sum(1 for project in projects for task in (project.tasks or []) if task.status != "done")

    lines = [
        f"Текущее время анализа: {_fmt_dt(now)}",
        f"Курсов: {len(courses)}, открытых учебных заданий: {open_assignments}",
        f"Событий расписания: {len(schedule_events)}",
        f"Проектов: {len(projects)}, открытых проектных задач: {open_tasks}",
    ]

    near_courses = sorted(
        [course for course in courses if _nearest_course_deadline(course)],
        key=lambda item: _nearest_course_deadline(item) or datetime.max,
    )[:3]
    if near_courses:
        lines.append("\nКурсы с ближайшими дедлайнами:")
        lines.extend(f"- {course.name}: до {_fmt_dt(_nearest_course_deadline(course))}" for course in near_courses)

    near_projects = sorted(
        [project for project in projects if _nearest_project_deadline(project)],
        key=lambda item: _nearest_project_deadline(item) or datetime.max,
    )[:3]
    if near_projects:
        lines.append("\nПроекты с ближайшими дедлайнами:")
        lines.extend(f"- {project.name}: до {_fmt_dt(_nearest_project_deadline(project))}" for project in near_projects)

    return "\n".join(lines)


def _render_course_summary(course: models.Course) -> str:
    assignments = course.assignments or []
    pending = [item for item in assignments if item.status != "done"]
    overdue = [item for item in pending if item.deadline_dt and item.deadline_dt < datetime.now()]

    lines = [
        f"Курс: «{course.name}»",
        f"Преподаватель: {course.teacher or '—'}; семестр: {course.semester or '—'}; прогресс: {course.progress:.0f}%",
        f"Материалов: {len(course.materials or [])}; заданий: {len(assignments)}; открытых: {len(pending)}; просроченных: {len(overdue)}",
    ]

    nearest_dt = _nearest_course_deadline(course)
    if nearest_dt:
        lines.append(f"Ближайший дедлайн: {_fmt_dt(nearest_dt)}")

    return "\n".join(lines)


def _render_assignment_summary(assignment: models.Assignment, course: models.Course | None) -> str:
    lines = [
        f"Задание: «{assignment.title}»",
        f"Курс: {course.name if course else '—'}",
        f"Статус: {_fmt_assignment_status(assignment.status)}",
        f"Дедлайн: {assignment.deadline or _fmt_dt(assignment.deadline_dt)}",
        f"Описание: {_clip(assignment.description or '—', 800)}",
    ]
    if assignment.file_name:
        lines.append(f"Файл задания: {assignment.file_name}")
    return "\n".join(lines)


def _render_project_summary(project: models.Project) -> str:
    tasks = project.tasks or []
    open_tasks = [item for item in tasks if item.status != "done"]
    overdue_tasks = [item for item in open_tasks if item.due_date and item.due_date < datetime.now()]

    lines = [
        f"Проект: «{project.name}»",
        f"Описание: {_clip(project.description or '—', 900)}",
        f"Участников: {len(project.members or [])}; задач: {len(tasks)}; открытых: {len(open_tasks)}; просроченных: {len(overdue_tasks)}",
        f"Файлов: {len(project.files or [])}; сообщений: {len(project.messages or [])}",
    ]

    nearest = _nearest_project_deadline(project)
    if nearest:
        lines.append(f"Ближайший дедлайн по задаче: {_fmt_dt(nearest)}")
    if project.owner:
        lines.append(f"Владелец: {project.owner.name} ({project.owner.email or 'без email'})")

    return "\n".join(lines)


def _render_schedule_snapshot(schedule_events: list[models.ScheduleEvent]) -> str:
    if not schedule_events:
        return "Расписание пустое."

    lines: list[str] = []
    for event in schedule_events[:14]:
        start_h = event.start_minute // 60
        start_m = event.start_minute % 60
        end_total = event.start_minute + event.duration_minutes
        end_h = end_total // 60
        end_m = end_total % 60
        lines.append(
            f"- {_fmt_day_index(event.day_index)} {start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d} — {event.title} ({event.location or 'локация не указана'})"
        )

    return "\n".join(lines)

def _select_relevant_courses(
    courses: list[models.Course],
    keywords: list[str],
    *,
    max_items: int,
) -> list[models.Course]:
    if not courses:
        return []

    ranked: list[tuple[int, datetime, models.Course]] = []
    for course in courses:
        score = _text_match_score(course.name, keywords) * 3 + _text_match_score(course.teacher, keywords)

        for assignment in course.assignments or []:
            score += _text_match_score(assignment.title, keywords) * 2
            score += _text_match_score(assignment.description, keywords)

        ranked.append((score, _nearest_course_deadline(course) or datetime.max, course))

    ranked.sort(key=lambda row: (-row[0], row[1], row[2].id))
    selected = [row[2] for row in ranked if row[0] > 0][:max_items]
    if selected:
        return selected

    fallback = sorted(courses, key=lambda item: _nearest_course_deadline(item) or datetime.max)
    return fallback[:max_items]


def _select_relevant_assignments(
    courses: list[models.Course],
    keywords: list[str],
    *,
    max_items: int,
) -> list[tuple[models.Course, models.Assignment]]:
    rows: list[tuple[int, datetime, models.Course, models.Assignment]] = []

    for course in courses:
        for assignment in course.assignments or []:
            score = (
                _text_match_score(assignment.title, keywords) * 3
                + _text_match_score(assignment.description, keywords)
                + _text_match_score(course.name, keywords)
            )
            rows.append((score, assignment.deadline_dt or datetime.max, course, assignment))

    rows.sort(key=lambda row: (-row[0], row[1], row[3].id))

    selected = [(row[2], row[3]) for row in rows if row[0] > 0][:max_items]
    if selected:
        return selected

    fallback = [(row[2], row[3]) for row in rows if row[3].status != "done"]
    if fallback:
        return fallback[:max_items]

    return [(row[2], row[3]) for row in rows[:max_items]]


def _select_relevant_projects(
    projects: list[models.Project],
    keywords: list[str],
    *,
    max_items: int,
) -> list[models.Project]:
    if not projects:
        return []

    ranked: list[tuple[int, datetime, models.Project]] = []
    for project in projects:
        score = _text_match_score(project.name, keywords) * 3 + _text_match_score(project.description, keywords)

        for task in project.tasks or []:
            score += _text_match_score(task.title, keywords) * 2
            score += _text_match_score(task.description, keywords)

        for file_item in project.files or []:
            score += _text_match_score(file_item.name, keywords)

        ranked.append((score, _nearest_project_deadline(project) or datetime.max, project))

    ranked.sort(key=lambda row: (-row[0], row[1], row[2].id))
    selected = [row[2] for row in ranked if row[0] > 0][:max_items]
    if selected:
        return selected

    fallback = sorted(projects, key=lambda item: _nearest_project_deadline(item) or datetime.max)
    return fallback[:max_items]


def _render_task_risks(project: models.Project, *, limit: int = 8) -> str:
    now = datetime.now()
    lines: list[str] = []

    for task in sorted(project.tasks or [], key=lambda item: item.due_date or datetime.max):
        if task.status == "done":
            continue

        assignee = task.assignee.name if task.assignee else "Без исполнителя"

        if task.due_date and task.due_date < now:
            lines.append(f"- Просрочено: «{task.title}», до {_fmt_dt(task.due_date)}, исполнитель: {assignee}.")
        elif not task.assignee:
            lines.append(f"- Риск: «{task.title}» без исполнителя.")
        elif not task.due_date:
            lines.append(f"- Риск: «{task.title}» без дедлайна (исполнитель: {assignee}).")

    return "\n".join(lines[:limit]) if lines else "- Критичных рисков по задачам не найдено."


def _collect_project_signals(project: models.Project, keywords: list[str]) -> str:
    signals: list[tuple[datetime, str]] = []

    for message in project.messages or []:
        author = message.author.name if message.author else "Участник"
        excerpt = select_keyword_excerpt(message.body, keywords, max_chars=260, window_chars=240, max_windows=1)
        if excerpt:
            signals.append((message.created_at or datetime.min, f"[{_fmt_dt(message.created_at)}] {author}: {excerpt}"))

    for task in project.tasks or []:
        for comment in task.comments or []:
            author = comment.author.name if comment.author else "Участник"
            excerpt = select_keyword_excerpt(comment.body, keywords, max_chars=240, window_chars=220, max_windows=1)
            if excerpt:
                signals.append(
                    (
                        comment.created_at or datetime.min,
                        f"[{_fmt_dt(comment.created_at)}] Комментарий к «{task.title}», {author}: {excerpt}",
                    )
                )

    if not signals:
        return "- Сигналы по сообщениям/комментариям отсутствуют."

    signals.sort(key=lambda row: row[0], reverse=True)
    return "\n".join(f"- {line}" for _, line in signals[:MAX_PROJECT_SIGNALS])


def _render_assignment_timeline(courses: list[models.Course], *, limit: int = 10) -> str:
    rows: list[tuple[datetime, str]] = []

    for course in courses:
        for assignment in course.assignments or []:
            if assignment.status == "done" or not assignment.deadline_dt:
                continue
            rows.append(
                (
                    assignment.deadline_dt,
                    f"- Курс «{course.name}»: «{assignment.title}» до {_fmt_dt(assignment.deadline_dt)} ({_fmt_assignment_status(assignment.status)})",
                )
            )

    if not rows:
        return "- Нет открытых учебных дедлайнов с датой."

    rows.sort(key=lambda row: row[0])
    return "\n".join(row[1] for row in rows[:limit])


def _render_project_timeline(projects: list[models.Project], *, limit: int = 10) -> str:
    rows: list[tuple[datetime, str]] = []

    for project in projects:
        for task in project.tasks or []:
            if task.status == "done" or not task.due_date:
                continue
            assignee = task.assignee.name if task.assignee else "без исполнителя"
            rows.append(
                (
                    task.due_date,
                    f"- Проект «{project.name}»: «{task.title}» до {_fmt_dt(task.due_date)} ({_fmt_task_status(task.status)}, {assignee})",
                )
            )

    if not rows:
        return "- Нет открытых проектных дедлайнов с датой."

    rows.sort(key=lambda row: row[0])
    return "\n".join(row[1] for row in rows[:limit])


def _course_material_excerpts(course: models.Course, keywords: list[str], *, max_items: int = 2) -> str:
    lines: list[str] = []

    for material in (course.materials or [])[: max_items * 2]:
        excerpt, state = extract_file_excerpt(material.file_path, keywords, max_chars=700)
        if excerpt:
            lines.append(f"- Материал «{material.name}»:\n{excerpt}")
        else:
            lines.append(f"- Материал «{material.name}»: {state}.")
        if len(lines) >= max_items:
            break

    return "\n".join(lines) if lines else "- Релевантные фрагменты материалов не найдены."


def _assignment_file_excerpt(assignment: models.Assignment, keywords: list[str]) -> str:
    if not assignment.file_path:
        return "- Файл задания не прикреплен."

    excerpt, state = extract_file_excerpt(assignment.file_path, keywords, max_chars=850)
    if not excerpt:
        return f"- Файл задания: {state}."
    return f"- Файл задания «{assignment.file_name or assignment.title}»:\n{excerpt}"


def _project_file_excerpts(project: models.Project, keywords: list[str], *, max_items: int = 2) -> str:
    if not project.files:
        return "- В проекте нет файлов."

    ranked = sorted(project.files, key=lambda file_item: (-_text_match_score(file_item.name, keywords), file_item.id))
    lines: list[str] = []
    for file_item in ranked:
        excerpt, state = extract_file_excerpt(file_item.file_path, keywords, max_chars=700)
        if excerpt:
            lines.append(f"- Файл «{file_item.name}»:\n{excerpt}")
        else:
            lines.append(f"- Файл «{file_item.name}»: {state}.")
        if len(lines) >= max_items:
            break

    return "\n".join(lines)


def _render_course_assignment_briefs(course: models.Course, *, limit: int = 6) -> str:
    now = datetime.now()
    rows = [
        (
            assignment.deadline_dt or now,
            f"- «{assignment.title}»: {_fmt_assignment_status(assignment.status)}, дедлайн {assignment.deadline or _fmt_dt(assignment.deadline_dt)}",
        )
        for assignment in (course.assignments or [])
    ]

    if not rows:
        return "- В курсе нет заданий."

    rows.sort(key=lambda row: row[0])
    return "\n".join(item[1] for item in rows[:limit])


def _render_project_task_briefs(project: models.Project, *, limit: int = 8) -> str:
    now = datetime.now()
    rows = []
    for task in project.tasks or []:
        assignee = task.assignee.name if task.assignee else "без исполнителя"
        rows.append(
            (
                task.due_date or now,
                f"- «{task.title}»: {_fmt_task_status(task.status)}, дедлайн {_fmt_dt(task.due_date)}, исполнитель {assignee}",
            )
        )

    if not rows:
        return "- В проекте нет задач."

    rows.sort(key=lambda row: row[0])
    return "\n".join(item[1] for item in rows[:limit])


def _normalize_history_message(item: object) -> ChatHistoryMessage | None:
    role = ""
    content = ""

    if hasattr(item, "role"):
        role = _to_text(getattr(item, "role", "")).strip()
        content = _to_text(getattr(item, "content", "")).strip()
    elif isinstance(item, dict):
        role = _to_text(item.get("role", "")).strip()
        content = _to_text(item.get("content", "")).strip()

    if not role or not content or role not in {"user", "assistant", "system"}:
        return None

    return ChatHistoryMessage(role=role, content=content)


def summarize_old_history(messages: list[ChatHistoryMessage], max_chars: int = CHAT_OLD_HISTORY_SUMMARY_LIMIT) -> str:
    if not messages:
        return ""

    user_points = [_clip(_normalize_whitespace(m.content), 180) for m in messages if m.role == "user"]
    assistant_points = [_clip(_normalize_whitespace(m.content), 180) for m in messages if m.role == "assistant"]

    lines: list[str] = [
        "Сжатая история более раннего диалога:",
        f"- Сообщений в сжатии: {len(messages)}",
    ]

    if user_points:
        lines.append("- Ранние запросы пользователя:")
        lines.extend(f"  - {item}" for item in user_points[-6:])

    if assistant_points:
        lines.append("- Ранние ответы ассистента:")
        lines.extend(f"  - {item}" for item in assistant_points[-6:])

    return _clip("\n".join(lines), max_chars)


def split_chat_history(
    messages: list[ChatHistoryMessage],
    *,
    keep_recent: int = CHAT_RECENT_MESSAGES_LIMIT,
) -> tuple[list[ChatHistoryMessage], str]:
    if len(messages) <= keep_recent:
        return messages, ""
    return messages[-keep_recent:], summarize_old_history(messages[:-keep_recent])


def _last_user_message(messages: list[ChatHistoryMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return messages[-1].content if messages else ""

def classify_chat_intent(
    last_message: str,
    courses: list[models.Course],
    projects: list[models.Project],
) -> tuple[str, str]:
    text = _to_text(last_message).casefold()
    keywords = extract_keywords(last_message)

    if not text:
        return _CHAT_ROUTE_STUDY_GENERAL, "Пустой запрос, выбран общий учебный режим."

    assignment_triggers = ["задани", "домаш", "лаба", "лаборат", "assignment", "hw"]
    project_triggers = ["проект", "команд", "task", "таск", "спринт", "беклог"]
    schedule_triggers = ["распис", "пара", "дедлайн", "срок", "когда", "today", "сегодня"]
    planning_triggers = ["план", "приоритет", "продуктив", "успеть", "нагруз", "time", "тайм"]
    course_triggers = ["курс", "предмет", "лекц", "семинар", "экзам", "зачет"]

    for course in courses:
        for assignment in course.assignments or []:
            if _match_name_in_text(assignment.title, text):
                return _CHAT_ROUTE_ASSIGNMENT, "Обнаружено упоминание конкретного задания."

    for project in projects:
        if _match_name_in_text(project.name, text):
            return _CHAT_ROUTE_PROJECT, "Обнаружено упоминание конкретного проекта."
        for task in project.tasks or []:
            if _match_name_in_text(task.title, text):
                return _CHAT_ROUTE_PROJECT, "Обнаружено упоминание задачи проекта."

    if any(trigger in text for trigger in assignment_triggers):
        return _CHAT_ROUTE_ASSIGNMENT, "Обнаружены признаки запроса по заданию."
    if any(trigger in text for trigger in project_triggers):
        return _CHAT_ROUTE_PROJECT, "Обнаружены признаки проектного запроса."
    if any(trigger in text for trigger in schedule_triggers):
        return _CHAT_ROUTE_SCHEDULE_DEADLINE, "Обнаружены признаки запроса про расписание/дедлайны."
    if any(trigger in text for trigger in planning_triggers):
        return _CHAT_ROUTE_PLANNING_PRODUCTIVITY, "Обнаружены признаки запроса по планированию."

    for course in courses:
        if _match_name_in_text(course.name, text):
            return _CHAT_ROUTE_COURSE, "Обнаружено упоминание курса."

    if any(trigger in text for trigger in course_triggers):
        return _CHAT_ROUTE_COURSE, "Обнаружены признаки запроса про курс."
    if keywords:
        return _CHAT_ROUTE_STUDY_GENERAL, "Выбран общий режим по учебным ключевым словам."
    return _CHAT_ROUTE_STUDY_GENERAL, "Выбран общий учебный режим по умолчанию."


def _semantic_route_from_hits(hits: list[object]) -> tuple[str | None, str]:
    if not hits:
        return None, ""

    route_scores: defaultdict[str, float] = defaultdict(float)
    route_titles: dict[str, str] = {}

    for hit in hits:
        entity_type = getattr(hit, "entity_type", "")
        scope = getattr(hit, "scope", "")
        score = float(getattr(hit, "score", 0.0) or 0.0)

        if entity_type == "assignment":
            route = _CHAT_ROUTE_ASSIGNMENT
        elif scope == "course" or entity_type in {"course", "material"}:
            route = _CHAT_ROUTE_COURSE
        elif scope == "project" or entity_type in {"project", "project_task", "project_file", "project_message"}:
            route = _CHAT_ROUTE_PROJECT
        else:
            continue

        route_scores[route] += score
        route_titles.setdefault(route, getattr(hit, "title", ""))

    if not route_scores:
        return None, ""

    route, score = max(route_scores.items(), key=lambda item: item[1])
    if score < 0.18:
        return None, ""

    title = route_titles.get(route) or "релевантный фрагмент"
    return route, f"Маршрут уточнен semantic search: найден близкий по смыслу контекст «{title}»."


def _should_apply_semantic_route(current_route: str, semantic_route: str | None) -> bool:
    if not semantic_route:
        return False
    if current_route == _CHAT_ROUTE_STUDY_GENERAL:
        return True
    if current_route == _CHAT_ROUTE_COURSE and semantic_route == _CHAT_ROUTE_ASSIGNMENT:
        return True
    return False


def build_workspace_summary_context(db: Session, user_id: int) -> str:
    courses, schedule_events, projects = _load_workspace_data(db, user_id)
    derived = _calc_workspace_derived(courses, schedule_events, projects)
    semantic_block = _semantic_context_block(
        db,
        user_id=user_id,
        query="workspace summary deadlines risks priorities courses projects",
        sources=_collect_workspace_semantic_sources(user_id, courses, projects),
        limit=5,
    )

    assembler = PriorityContextAssembler(WORKSPACE_SUMMARY_CONTEXT_CHAR_LIMIT)
    assembler.add("Stable snapshot", _render_workspace_snapshot(courses, schedule_events, projects), BUDGET_FACTS)
    assembler.add("Derived facts", _render_derived_block(derived), BUDGET_FACTS)
    assembler.add("Semantic excerpts", semantic_block, BUDGET_EXCERPTS)
    assembler.add("Timeline по учебным дедлайнам", _render_assignment_timeline(courses), BUDGET_ENTITIES)
    assembler.add("Timeline по проектным дедлайнам", _render_project_timeline(projects), BUDGET_ENTITIES)

    if courses:
        course_lines = [
            _render_course_summary(course)
            for course in _select_relevant_courses(courses, [], max_items=MAX_COURSES_IN_CONTEXT)
        ]
        assembler.add("Краткие сущности: курсы", "\n\n".join(course_lines), BUDGET_ENTITIES)

    if projects:
        project_lines = [
            _render_project_summary(project)
            for project in _select_relevant_projects(projects, [], max_items=MAX_PROJECTS_IN_CONTEXT)
        ]
        assembler.add("Краткие сущности: проекты", "\n\n".join(project_lines), BUDGET_ENTITIES)

    return assembler.build("Контекст workspace для AI-сводки")


def build_project_summary_context(db: Session, project_id: int, user_id: int) -> str | None:
    project = _project_query_by_id_for_user(db, project_id, user_id).first()
    if not project:
        return None

    derived = _calc_workspace_derived([], [], [project])
    project_keywords = extract_keywords(f"{project.name} {project.description}")
    semantic_block = _semantic_context_block(
        db,
        user_id=user_id,
        query=f"{project.name} {project.description} project status risks tasks files discussion",
        sources=_collect_project_semantic_sources(user_id, [project]),
        scopes={"project"},
        parent_type="project",
        parent_id=project.id,
        limit=6,
    )

    assembler = PriorityContextAssembler(PROJECT_SUMMARY_CONTEXT_CHAR_LIMIT)
    assembler.add("Semantic excerpts", semantic_block, BUDGET_EXCERPTS)
    assembler.add("Stable snapshot проекта", _render_project_summary(project), BUDGET_FACTS)
    assembler.add("Derived facts проекта", _render_derived_block(derived), BUDGET_FACTS)
    assembler.add("Риски по задачам", _render_task_risks(project, limit=MAX_TASKS_IN_CONTEXT), BUDGET_FACTS)
    assembler.add("Ключевые задачи", _render_project_task_briefs(project), BUDGET_ENTITIES)
    assembler.add("Recent signals (сообщения и комментарии)", _collect_project_signals(project, project_keywords), BUDGET_ENTITIES)
    assembler.add("File excerpts", _project_file_excerpts(project, project_keywords, max_items=MAX_FILES_IN_CONTEXT), BUDGET_EXCERPTS)

    return assembler.build("Контекст проекта для AI-сводки")


def build_course_plan_context(
    course: models.Course,
    extra_context: str,
    db: Session | None = None,
    user_id: int | None = None,
) -> str:
    keywords = extract_keywords(f"{course.name} {extra_context}")
    semantic_block = ""
    if db is not None and user_id is not None:
        semantic_block = _semantic_context_block(
            db,
            user_id=user_id,
            query=f"{course.name} {extra_context} course plan materials assignments",
            sources=_collect_course_semantic_sources(user_id, [course]),
            scopes={"course"},
            parent_type="course",
            parent_id=course.id,
            limit=6,
        )

    assembler = PriorityContextAssembler(COURSE_PLAN_CONTEXT_CHAR_LIMIT)
    assembler.add("Semantic excerpts", semantic_block, BUDGET_EXCERPTS)
    assembler.add("Stable snapshot курса", _render_course_summary(course), BUDGET_FACTS)
    assembler.add("Задания курса", _render_course_assignment_briefs(course), BUDGET_ENTITIES)

    if extra_context.strip():
        assembler.add("Дополнительный контекст пользователя", _clip(extra_context, 4_500), BUDGET_FACTS)

    assembler.add("Excerpts из материалов курса", _course_material_excerpts(course, keywords, max_items=MAX_FILES_IN_CONTEXT), BUDGET_EXCERPTS)

    assignment_file_lines: list[str] = []
    for assignment in (course.assignments or [])[:MAX_ASSIGNMENTS_IN_CONTEXT]:
        if assignment.file_path:
            assignment_file_lines.append(f"- «{assignment.title}»\n{_assignment_file_excerpt(assignment, keywords)}")

    if assignment_file_lines:
        assembler.add("Excerpts из файлов заданий", "\n".join(assignment_file_lines), BUDGET_EXCERPTS)

    if course.materials:
        raw_lines: list[str] = []
        for material in course.materials[:2]:
            raw_text, state = extract_file_text(material.file_path, RAW_FILE_TAIL_BUDGET)
            raw_lines.append(f"- {material.name}:\n{raw_text}" if raw_text else f"- {material.name}: {state}.")
        assembler.add("Raw text fallback", "\n".join(raw_lines), BUDGET_RAW_TEXT)

    return assembler.build("Контекст курса для AI-плана")


def build_assignment_help_context(
    assignment: models.Assignment,
    course: models.Course | None,
    question: str = "",
    db: Session | None = None,
    user_id: int | None = None,
) -> str:
    base_text = f"{assignment.title} {assignment.description or ''} {question}"
    if course:
        base_text += f" {course.name}"
    keywords = extract_keywords(base_text)
    semantic_block = ""
    if db is not None and user_id is not None and course is not None:
        semantic_block = _semantic_context_block(
            db,
            user_id=user_id,
            query=base_text,
            sources=_collect_course_semantic_sources(user_id, [course]),
            scopes={"course"},
            parent_type="course",
            parent_id=course.id,
            limit=5,
        )

    assembler = PriorityContextAssembler(ASSIGNMENT_HELP_CONTEXT_CHAR_LIMIT)
    assembler.add("Semantic excerpts", semantic_block, BUDGET_EXCERPTS)
    assembler.add("Stable snapshot задания", _render_assignment_summary(assignment, course), BUDGET_FACTS)

    if question.strip():
        assembler.add("Вопрос пользователя", _clip(question, 2_200), BUDGET_FACTS)
    else:
        assembler.add(
            "Режим помощи",
            "Пользователь не задал явный вопрос: нужна полезная авто-подсказка по старту, шагам и рискам.",
            BUDGET_FACTS,
        )

    assembler.add("Excerpt из файла задания", _assignment_file_excerpt(assignment, keywords), BUDGET_EXCERPTS)

    if course:
        assembler.add("Курс задания", _render_course_summary(course), BUDGET_ENTITIES)

        sibling_lines: list[str] = []
        for item in (course.assignments or [])[: MAX_ASSIGNMENTS_IN_CONTEXT + 2]:
            if item.id == assignment.id:
                continue
            sibling_lines.append(
                f"- «{item.title}»: {_fmt_assignment_status(item.status)}, дедлайн {item.deadline or _fmt_dt(item.deadline_dt)}"
            )
            if len(sibling_lines) >= MAX_ASSIGNMENTS_IN_CONTEXT:
                break

        if sibling_lines:
            assembler.add("Другие задания курса (нагрузка и приоритеты)", "\n".join(sibling_lines), BUDGET_ENTITIES)

        assembler.add("Excerpts из материалов курса", _course_material_excerpts(course, keywords, max_items=2), BUDGET_EXCERPTS)

    return assembler.build("Контекст для помощи по заданию")


def _build_chat_context_text(
    route: str,
    courses: list[models.Course],
    schedule_events: list[models.ScheduleEvent],
    projects: list[models.Project],
    derived: DerivedFacts,
    keywords: list[str],
    semantic_block: str = "",
) -> str:
    assembler = PriorityContextAssembler(CHAT_CONTEXT_CHAR_LIMIT)

    assembler.add("Stable snapshot", _render_workspace_snapshot(courses, schedule_events, projects), BUDGET_FACTS)
    assembler.add("Derived facts", _render_derived_block(derived), BUDGET_FACTS)
    assembler.add("Semantic excerpts", semantic_block, BUDGET_EXCERPTS)

    if route == _CHAT_ROUTE_COURSE:
        selected_courses = _select_relevant_courses(courses, keywords, max_items=2)
        if selected_courses:
            assembler.add("Relevant courses", "\n\n".join(_render_course_summary(c) for c in selected_courses), BUDGET_ENTITIES)
            assembler.add("Relevant assignments", "\n\n".join(_render_course_assignment_briefs(c, limit=5) for c in selected_courses), BUDGET_ENTITIES)
            assembler.add("Excerpts", "\n\n".join(_course_material_excerpts(c, keywords, max_items=2) for c in selected_courses), BUDGET_EXCERPTS)

    elif route == _CHAT_ROUTE_ASSIGNMENT:
        selected = _select_relevant_assignments(courses, keywords, max_items=2)
        if selected:
            details = [_render_assignment_summary(assignment, course) for course, assignment in selected]
            excerpts = [_assignment_file_excerpt(assignment, keywords) for _, assignment in selected]
            assembler.add("Relevant assignments", "\n\n".join(details), BUDGET_ENTITIES)
            assembler.add("Excerpts", "\n\n".join(excerpts), BUDGET_EXCERPTS)

    elif route == _CHAT_ROUTE_SCHEDULE_DEADLINE:
        assembler.add("Расписание", _render_schedule_snapshot(schedule_events), BUDGET_ENTITIES)
        assembler.add("Учебный timeline", _render_assignment_timeline(courses), BUDGET_ENTITIES)
        assembler.add("Проектный timeline", _render_project_timeline(projects), BUDGET_ENTITIES)

    elif route == _CHAT_ROUTE_PROJECT:
        selected_projects = _select_relevant_projects(projects, keywords, max_items=2)
        if selected_projects:
            assembler.add("Relevant projects", "\n\n".join(_render_project_summary(p) for p in selected_projects), BUDGET_ENTITIES)
            assembler.add("Риски по задачам", "\n\n".join(_render_task_risks(p) for p in selected_projects), BUDGET_ENTITIES)
            assembler.add("Recent signals", "\n\n".join(_collect_project_signals(p, keywords) for p in selected_projects), BUDGET_ENTITIES)
            assembler.add("Excerpts файлов", "\n\n".join(_project_file_excerpts(p, keywords, max_items=2) for p in selected_projects), BUDGET_EXCERPTS)

    elif route == _CHAT_ROUTE_PLANNING_PRODUCTIVITY:
        selected_courses = _select_relevant_courses(courses, keywords, max_items=3)
        selected_projects = _select_relevant_projects(projects, keywords, max_items=2)

        if selected_courses:
            assembler.add("Приоритетные курсы", "\n\n".join(_render_course_summary(c) for c in selected_courses), BUDGET_ENTITIES)
        if selected_projects:
            assembler.add("Приоритетные проекты", "\n\n".join(_render_project_summary(p) for p in selected_projects), BUDGET_ENTITIES)

        assembler.add("Дедлайны", _render_assignment_timeline(courses), BUDGET_ENTITIES)
        assembler.add("Дедлайны проектов", _render_project_timeline(projects), BUDGET_ENTITIES)

    else:
        selected_courses = _select_relevant_courses(courses, keywords, max_items=3)
        selected_projects = _select_relevant_projects(projects, keywords, max_items=2)

        if selected_courses:
            assembler.add("Relevant courses", "\n\n".join(_render_course_summary(c) for c in selected_courses), BUDGET_ENTITIES)
        if selected_projects:
            assembler.add("Relevant projects", "\n\n".join(_render_project_summary(p) for p in selected_projects), BUDGET_ENTITIES)

        assembler.add("Учебный timeline", _render_assignment_timeline(courses), BUDGET_ENTITIES)

    if courses:
        raw_lines: list[str] = []
        for course in _select_relevant_courses(courses, keywords, max_items=1):
            for material in (course.materials or [])[:1]:
                raw_text, state = extract_file_text(material.file_path, RAW_FILE_TAIL_BUDGET)
                raw_lines.append(f"- {material.name}:\n{raw_text}" if raw_text else f"- {material.name}: {state}.")
        if raw_lines:
            assembler.add("Raw text fallback", "\n".join(raw_lines), BUDGET_RAW_TEXT)

    return assembler.build("Контекст для ответа в чате")

def build_chat_context_package(
    db: Session,
    user_id: int,
    messages: list[object],
) -> ChatContextPackage:
    normalized = [item for item in (_normalize_history_message(raw) for raw in messages) if item is not None]

    courses, schedule_events, projects = _load_workspace_data(db, user_id)

    last_message = _last_user_message(normalized)
    route, route_reason = classify_chat_intent(last_message, courses, projects)
    semantic_sources = [
        *_collect_workspace_semantic_sources(user_id, courses, projects),
        *_collect_chat_history_semantic_sources(user_id, normalized[:-1]),
    ]

    if last_message.strip():
        try:
            prune_stale_context_sources(
                db,
                user_id=user_id,
                sources=semantic_sources,
                scopes={"course", "project", "chat_history"},
            )
            ensure_context_sources_indexed(db, semantic_sources)
            route_hits = semantic_search_context(
                db,
                user_id=user_id,
                query=last_message,
                scopes={"course", "project"},
                limit=5,
                min_score=0.14,
            )
            semantic_route, semantic_reason = _semantic_route_from_hits(route_hits)
            if _should_apply_semantic_route(route, semantic_route):
                route = semantic_route or route
                route_reason = semantic_reason or route_reason
        except Exception:  # pragma: no cover
            pass

    route_label = CHAT_ROUTE_LABELS.get(route, CHAT_ROUTE_LABELS[_CHAT_ROUTE_STUDY_GENERAL])

    keywords = extract_keywords(last_message)
    derived = _calc_workspace_derived(courses, schedule_events, projects)
    semantic_scopes = {"course", "project", "chat_history"}
    if route in {_CHAT_ROUTE_COURSE, _CHAT_ROUTE_ASSIGNMENT}:
        semantic_scopes = {"course", "chat_history"}
    elif route == _CHAT_ROUTE_PROJECT:
        semantic_scopes = {"project", "chat_history"}
    elif route == _CHAT_ROUTE_SCHEDULE_DEADLINE:
        semantic_scopes = {"chat_history"}

    semantic_block = ""
    if semantic_scopes:
        semantic_block = _semantic_context_block(
            db,
            user_id=user_id,
            query=last_message,
            sources=semantic_sources,
            scopes=semantic_scopes,
            limit=6,
        )

    context_text = _build_chat_context_text(route, courses, schedule_events, projects, derived, keywords, semantic_block)
    recent_messages, older_history_summary = split_chat_history(normalized)

    return ChatContextPackage(
        route=route,
        route_label=route_label,
        route_reason=route_reason,
        keywords=keywords,
        context_text=context_text,
        recent_messages=recent_messages,
        older_history_summary=older_history_summary,
    )


def build_workspace_context(db: Session, user_id: int, *, for_chat: bool = False) -> str:
    if for_chat:
        return build_chat_context_package(db, user_id, []).context_text
    return build_workspace_summary_context(db, user_id)


def build_project_context(db: Session, project_id: int, user_id: int) -> str | None:
    return build_project_summary_context(db, project_id, user_id)


def build_chat_context(db: Session, user_id: int) -> str:
    return build_workspace_context(db, user_id, for_chat=True)
