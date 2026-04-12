from __future__ import annotations

import os
import zipfile
from collections import defaultdict
from datetime import datetime
import xml.etree.ElementTree as ET

from sqlalchemy.orm import Session, selectinload

import models


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".json",
    ".xml",
    ".yml",
    ".yaml",
    ".sql",
    ".log",
}

COURSE_FILE_TEXT_LIMIT = 1400
ASSIGNMENT_FILE_TEXT_LIMIT = 1400
PROJECT_FILE_TEXT_LIMIT = 1400
COMMENT_TEXT_LIMIT = 320
MESSAGE_TEXT_LIMIT = 280

MAX_TASK_COMMENTS_IN_CONTEXT = 8
MAX_PROJECT_MESSAGES_IN_CONTEXT = 20

WORKSPACE_CONTEXT_CHAR_LIMIT = 110_000
CHAT_CONTEXT_CHAR_LIMIT = 55_000
PROJECT_CONTEXT_CHAR_LIMIT = 75_000
COURSE_CONTEXT_CHAR_LIMIT = 55_000
ASSIGNMENT_CONTEXT_CHAR_LIMIT = 45_000


class ContextBuilder:
    def __init__(self, max_chars: int):
        self.max_chars = max_chars
        self._chunks: list[str] = []
        self._size = 0
        self._truncated = False

    def add(self, text: str):
        if not text:
            return
        if self._size >= self.max_chars:
            self._truncated = True
            return
        remaining = self.max_chars - self._size
        if len(text) <= remaining:
            self._chunks.append(text)
            self._size += len(text)
            return

        reserve = 88
        clipped = text[: max(0, remaining - reserve)].rstrip()
        tail = "\n...[контекст усечен из-за большого объема]\n"
        self._chunks.append(clipped + tail)
        self._size = self.max_chars
        self._truncated = True

    def build(self) -> str:
        return "".join(self._chunks)

    @property
    def truncated(self) -> bool:
        return self._truncated


def _clip(text: str | None, max_chars: int) -> str:
    if not text:
        return ""
    value = text.strip()
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars].rstrip()}\n...[усечено, показано {max_chars} символов]"


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
    labels = {
        "pending": "ожидает",
        "progress": "в процессе",
        "done": "выполнено",
        "overdue": "просрочено",
    }
    return labels.get((status or "").strip(), status or "не указан")


def _fmt_task_status(status: str | None) -> str:
    labels = {
        "todo": "к выполнению",
        "in_progress": "в работе",
        "done": "выполнено",
    }
    return labels.get((status or "").strip(), status or "не указан")


def _read_zip_xml_text(path: str, member: str, max_chars: int) -> str:
    with zipfile.ZipFile(path) as archive:
        with archive.open(member) as src:
            root = ET.parse(src).getroot()
    parts: list[str] = []
    for node in root.iter():
        if node.text and node.text.strip():
            parts.append(node.text.strip())
    return _clip(" ".join(parts), max_chars)


def extract_file_text(file_path: str | None, max_chars: int) -> tuple[str, str]:
    if not file_path:
        return "", "файл не прикреплен"
    if not os.path.exists(file_path):
        return "", "файл отсутствует на диске"

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in TEXT_EXTENSIONS:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                return _clip(handle.read(max_chars + 200), max_chars), "ok"
        if ext == ".odt":
            return _read_zip_xml_text(file_path, "content.xml", max_chars), "ok"
        if ext == ".docx":
            return _read_zip_xml_text(file_path, "word/document.xml", max_chars), "ok"
        return "", f"тип файла {ext or 'неизвестный'} не поддерживается для извлечения текста"
    except Exception as exc:
        return "", f"не удалось извлечь текст ({exc.__class__.__name__})"


def _course_query(db: Session, user_id: int):
    return (
        db.query(models.Course)
        .options(
            selectinload(models.Course.materials),
            selectinload(models.Course.assignments),
        )
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


def _calc_workspace_derived(
    courses: list[models.Course],
    schedule_events: list[models.ScheduleEvent],
    projects: list[models.Project],
) -> dict[str, list[str]]:
    now = datetime.now()
    overdue: list[tuple[datetime, str]] = []
    upcoming: list[tuple[datetime, str]] = []
    conflicts_map: defaultdict[str, list[str]] = defaultdict(list)
    assignee_load: defaultdict[str, int] = defaultdict(int)

    for course in courses:
        for assignment in course.assignments or []:
            if not assignment.deadline_dt:
                continue
            label = f"Курс «{course.name}»: «{assignment.title}» ({_fmt_assignment_status(assignment.status)}) до {_fmt_dt(assignment.deadline_dt)}"
            if assignment.status != "done" and assignment.deadline_dt < now:
                overdue.append((assignment.deadline_dt, label))
            if assignment.status != "done" and assignment.deadline_dt >= now:
                upcoming.append((assignment.deadline_dt, label))
            if assignment.status != "done":
                conflicts_map[assignment.deadline_dt.date().isoformat()].append(label)

    for project in projects:
        for task in project.tasks or []:
            assignee_name = task.assignee.name if task.assignee else "Без исполнителя"
            if task.status != "done":
                assignee_load[assignee_name] += 1
            if not task.due_date:
                continue
            label = f"Проект «{project.name}»: «{task.title}» ({_fmt_task_status(task.status)}, {assignee_name}) до {_fmt_dt(task.due_date)}"
            if task.status != "done" and task.due_date < now:
                overdue.append((task.due_date, label))
            if task.status != "done" and task.due_date >= now:
                upcoming.append((task.due_date, label))
            if task.status != "done":
                conflicts_map[task.due_date.date().isoformat()].append(label)

    today_events: list[str] = []
    current_weekday = now.weekday()
    today = [event for event in schedule_events if event.day_index == current_weekday]
    for event in sorted(today, key=lambda item: item.start_minute):
        start_h = event.start_minute // 60
        start_m = event.start_minute % 60
        end_total = event.start_minute + event.duration_minutes
        end_h = end_total // 60
        end_m = end_total % 60
        today_events.append(
            f"{start_h:02d}:{start_m:02d}–{end_h:02d}:{end_m:02d} — {event.title} ({event.location or 'локация не указана'})"
        )

    sorted_overdue = [item[1] for item in sorted(overdue, key=lambda x: x[0])[:14]]
    sorted_upcoming = [item[1] for item in sorted(upcoming, key=lambda x: x[0])[:18]]
    conflicts = []
    for date_key, labels in sorted(conflicts_map.items()):
        if len(labels) < 2:
            continue
        conflicts.append(f"{date_key}: {len(labels)} пересечения")
        for label in labels[:4]:
            conflicts.append(f"  - {label}")

    load_lines = []
    if assignee_load:
        ordered = sorted(assignee_load.items(), key=lambda item: item[1], reverse=True)
        for name, count in ordered:
            load_lines.append(f"{name}: {count} открытых задач")
        if len(ordered) >= 2:
            max_count = ordered[0][1]
            min_count = ordered[-1][1]
            if max_count - min_count >= 2:
                load_lines.append(
                    f"Признак дисбаланса: у «{ordered[0][0]}» на {max_count - min_count} задач больше, чем у «{ordered[-1][0]}»."
                )

    return {
        "overdue": sorted_overdue,
        "upcoming": sorted_upcoming,
        "today_events": today_events,
        "conflicts": conflicts,
        "assignee_load": load_lines,
    }


def _render_course_details(course: models.Course, include_material_text: bool, include_assignment_file_text: bool) -> str:
    lines = [
        f"- Курс: «{course.name}»",
        f"  Преподаватель: {course.teacher or '—'}; семестр: {course.semester or '—'}; прогресс: {course.progress:.0f}%",
        f"  Материалы: {(len(course.materials or []))}; задания: {(len(course.assignments or []))}",
    ]

    materials = course.materials or []
    if materials:
        lines.append("  Материалы курса:")
        for material in materials:
            lines.append(
                f"    - {material.name} ({material.mime_type or 'тип не указан'}, {material.size_bytes} байт)"
            )
            if include_material_text:
                text, state = extract_file_text(material.file_path, COURSE_FILE_TEXT_LIMIT)
                if text:
                    lines.append(f"      Текст материала:\n{_clip(text, COURSE_FILE_TEXT_LIMIT)}")
                else:
                    lines.append(f"      Текст материала: {state}.")
    else:
        lines.append("  Материалы курса: нет.")

    assignments = course.assignments or []
    if assignments:
        lines.append("  Задания курса:")
        for assignment in assignments:
            lines.append(
                f"    - «{assignment.title}»; статус: {_fmt_assignment_status(assignment.status)}; дедлайн: {assignment.deadline or _fmt_dt(assignment.deadline_dt)}"
            )
            lines.append(f"      Описание: {_clip(assignment.description or '—', 900)}")
            if assignment.file_name:
                lines.append(f"      Файл задания: {assignment.file_name}")
            if include_assignment_file_text and assignment.file_path:
                text, state = extract_file_text(assignment.file_path, ASSIGNMENT_FILE_TEXT_LIMIT)
                if text:
                    lines.append(f"      Текст файла задания:\n{_clip(text, ASSIGNMENT_FILE_TEXT_LIMIT)}")
                else:
                    lines.append(f"      Текст файла задания: {state}.")
    else:
        lines.append("  Задания курса: нет.")
    return "\n".join(lines) + "\n"


def build_course_plan_context(course: models.Course, extra_context: str) -> str:
    builder = ContextBuilder(COURSE_CONTEXT_CHAR_LIMIT)
    builder.add("Контекст курса для AI-плана:\n")
    builder.add(_render_course_details(course, include_material_text=True, include_assignment_file_text=True))
    if extra_context.strip():
        builder.add(f"\nДополнительный контекст от пользователя:\n{_clip(extra_context, 4000)}\n")
    return builder.build()


def build_assignment_help_context(
    assignment: models.Assignment,
    course: models.Course | None,
) -> str:
    builder = ContextBuilder(ASSIGNMENT_CONTEXT_CHAR_LIMIT)
    builder.add("Контекст для помощи по заданию:\n")
    builder.add(f"Задание: «{assignment.title}»\n")
    builder.add(f"Описание задания: {_clip(assignment.description or '—', 2500)}\n")
    builder.add(f"Статус: {_fmt_assignment_status(assignment.status)}\n")
    builder.add(f"Дедлайн: {assignment.deadline or _fmt_dt(assignment.deadline_dt)}\n")
    if assignment.file_name:
        builder.add(f"Прикрепленный файл задания: {assignment.file_name}\n")
    text, state = extract_file_text(assignment.file_path, ASSIGNMENT_FILE_TEXT_LIMIT)
    if text:
        builder.add(f"Текст прикрепленного файла задания:\n{text}\n")
    else:
        builder.add(f"Текст прикрепленного файла задания: {state}.\n")

    if course:
        builder.add("\nСвязанный курс:\n")
        builder.add(_render_course_details(course, include_material_text=True, include_assignment_file_text=True))
        other_assignments = [
            item for item in (course.assignments or []) if item.id != assignment.id
        ]
        if other_assignments:
            builder.add("Другие задания этого курса (для нагрузки и приоритетов):\n")
            for item in other_assignments:
                builder.add(
                    f"- «{item.title}»; статус: {_fmt_assignment_status(item.status)}; дедлайн: {item.deadline or _fmt_dt(item.deadline_dt)}\n"
                )
    return builder.build()


def _render_project_details(project: models.Project, include_messages: bool) -> str:
    lines: list[str] = [
        f"- Проект: «{project.name}»",
        f"  Описание: {_clip(project.description or '—', 2200)}",
        f"  Участников: {len(project.members or [])}; задач: {len(project.tasks or [])}; файлов: {len(project.files or [])}",
    ]
    if project.owner:
        lines.append(f"  Владелец: {project.owner.name} ({project.owner.email or 'без email'})")

    members = project.members or []
    if members:
        lines.append("  Участники:")
        for member in members:
            if not member.user:
                continue
            lines.append(
                f"    - {member.user.name} ({member.user.email or 'без email'}), роль: {member.role}"
            )
    else:
        lines.append("  Участники: нет данных.")

    tasks = project.tasks or []
    if tasks:
        lines.append("  Задачи проекта:")
        for task in tasks:
            assignee = task.assignee.name if task.assignee else "Без исполнителя"
            lines.append(
                f"    - «{task.title}»; статус: {_fmt_task_status(task.status)}; дедлайн: {_fmt_dt(task.due_date)}; ответственный: {assignee}"
            )
            lines.append(f"      Описание: {_clip(task.description or '—', 850)}")

            comments = task.comments or []
            if comments:
                lines.append(f"      Комментарии ({len(comments)}):")
                for comment in comments[:MAX_TASK_COMMENTS_IN_CONTEXT]:
                    author = comment.author.name if comment.author else "Участник"
                    lines.append(
                        f"        - {_fmt_dt(comment.created_at)}; {author}: {_clip(comment.body, COMMENT_TEXT_LIMIT)}"
                    )
                if len(comments) > MAX_TASK_COMMENTS_IN_CONTEXT:
                    lines.append(
                        f"        - ...ещё {len(comments) - MAX_TASK_COMMENTS_IN_CONTEXT} комментариев"
                    )
            else:
                lines.append("      Комментарии: нет.")
    else:
        lines.append("  Задачи проекта: нет.")

    files = project.files or []
    if files:
        lines.append("  Файлы проекта:")
        for file_item in files:
            uploader = file_item.uploader.name if file_item.uploader else "Участник"
            lines.append(
                f"    - {file_item.name} ({file_item.mime_type or 'тип не указан'}, {file_item.size_bytes} байт), загрузил: {uploader}"
            )
            text, state = extract_file_text(file_item.file_path, PROJECT_FILE_TEXT_LIMIT)
            if text:
                lines.append(f"      Текст файла:\n{_clip(text, PROJECT_FILE_TEXT_LIMIT)}")
            else:
                lines.append(f"      Текст файла: {state}.")
    else:
        lines.append("  Файлы проекта: нет.")

    if include_messages:
        messages = sorted(project.messages or [], key=lambda item: item.created_at, reverse=True)
        if messages:
            lines.append(
                f"  Последние сообщения проекта (показаны последние {min(MAX_PROJECT_MESSAGES_IN_CONTEXT, len(messages))}):"
            )
            for message in messages[:MAX_PROJECT_MESSAGES_IN_CONTEXT]:
                author = message.author.name if message.author else "Участник"
                lines.append(
                    f"    - {_fmt_dt(message.created_at)}; {author}: {_clip(message.body, MESSAGE_TEXT_LIMIT)}"
                )
        else:
            lines.append("  Сообщения проекта: нет.")
    return "\n".join(lines) + "\n"


def _render_derived_block(derived: dict[str, list[str]]) -> str:
    lines = ["\nАгрегированные факты для аналитики:\n"]
    if derived["overdue"]:
        lines.append("Просрочки:")
        for item in derived["overdue"]:
            lines.append(f"- {item}")
    else:
        lines.append("Просрочки: нет.")

    if derived["upcoming"]:
        lines.append("Ближайшие дедлайны:")
        for item in derived["upcoming"]:
            lines.append(f"- {item}")
    else:
        lines.append("Ближайшие дедлайны: нет.")

    if derived["today_events"]:
        lines.append("Расписание на сегодня:")
        for item in derived["today_events"]:
            lines.append(f"- {item}")
    else:
        lines.append("Расписание на сегодня: занятий нет.")

    if derived["conflicts"]:
        lines.append("Конфликты сроков:")
        for item in derived["conflicts"]:
            lines.append(f"- {item}")
    else:
        lines.append("Конфликты сроков: явных пересечений нет.")

    if derived["assignee_load"]:
        lines.append("Нагрузка по исполнителям:")
        for item in derived["assignee_load"]:
            lines.append(f"- {item}")
    else:
        lines.append("Нагрузка по исполнителям: недостаточно данных.")
    return "\n".join(lines) + "\n"


def build_workspace_context(db: Session, user_id: int, *, for_chat: bool = False) -> str:
    courses = _course_query(db, user_id).all()
    schedule_events = (
        db.query(models.ScheduleEvent)
        .filter(models.ScheduleEvent.user_id == user_id)
        .order_by(models.ScheduleEvent.day_index.asc(), models.ScheduleEvent.start_minute.asc())
        .all()
    )
    projects = _project_query_for_user(db, user_id).all()
    derived = _calc_workspace_derived(courses, schedule_events, projects)

    max_chars = CHAT_CONTEXT_CHAR_LIMIT if for_chat else WORKSPACE_CONTEXT_CHAR_LIMIT
    builder = ContextBuilder(max_chars)

    builder.add("Контекст workspace пользователя:\n\n")
    builder.add(f"Курсов: {len(courses)}\n")
    for course in courses:
        builder.add(_render_course_details(course, include_material_text=True, include_assignment_file_text=True))

    builder.add("\nРасписание пользователя:\n")
    if schedule_events:
        for event in schedule_events:
            start_h = event.start_minute // 60
            start_m = event.start_minute % 60
            end_total = event.start_minute + event.duration_minutes
            end_h = end_total // 60
            end_m = end_total % 60
            builder.add(
                f"- {_fmt_day_index(event.day_index)} {start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d} — {event.title} ({event.location or 'локация не указана'})\n"
            )
    else:
        builder.add("- Расписание пустое.\n")

    builder.add(f"\nПроектов: {len(projects)}\n")
    if projects:
        for project in projects:
            builder.add(_render_project_details(project, include_messages=True))
    else:
        builder.add("Проекты отсутствуют.\n")

    builder.add(_render_derived_block(derived))
    return builder.build()


def build_project_context(db: Session, project_id: int, user_id: int) -> str | None:
    project = _project_query_by_id_for_user(db, project_id, user_id).first()
    if not project:
        return None

    now = datetime.now()
    single_project_courses: list[models.Course] = []
    single_schedule: list[models.ScheduleEvent] = []
    derived = _calc_workspace_derived(single_project_courses, single_schedule, [project])

    builder = ContextBuilder(PROJECT_CONTEXT_CHAR_LIMIT)
    builder.add("Контекст командного проекта:\n\n")
    builder.add(_render_project_details(project, include_messages=True))
    builder.add(_render_derived_block(derived))
    if project.created_at:
        builder.add(f"\nДата создания проекта: {_fmt_dt(project.created_at)}\n")
    builder.add(f"Текущий момент анализа: {_fmt_dt(now)}\n")
    return builder.build()


def build_chat_context(db: Session, user_id: int) -> str:
    return build_workspace_context(db, user_id, for_chat=True)

