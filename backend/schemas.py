from datetime import datetime
from pydantic import BaseModel


# ── User ──────────────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    initials: str
    role: str = "Студент"


class UserOut(BaseModel):
    id: int
    name: str
    initials: str
    role: str

    model_config = {"from_attributes": True}


# ── Course ────────────────────────────────────────────────────
class CourseCreate(BaseModel):
    name: str
    color: str = "#3d52d5"
    emoji: str = "📚"
    teacher: str = ""
    semester: str = ""
    credits: int = 3
    progress: float = 0.0


class CourseUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    emoji: str | None = None
    teacher: str | None = None
    semester: str | None = None
    credits: int | None = None
    progress: float | None = None


class CourseOut(BaseModel):
    id: int
    user_id: int
    name: str
    color: str
    emoji: str
    teacher: str
    semester: str
    credits: int
    progress: float
    materials: list["MaterialOut"] = []
    assignments: list["AssignmentOut"] = []

    model_config = {"from_attributes": True}


# ── Material ──────────────────────────────────────────────────
class MaterialOut(BaseModel):
    id: int
    course_id: int
    name: str
    size_bytes: int
    mime_type: str
    icon: str
    icon_bg: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Assignment ────────────────────────────────────────────────
class AssignmentCreate(BaseModel):
    title: str
    description: str = ""
    deadline: str = ""
    deadline_dt: datetime | None = None
    status: str = "pending"


class AssignmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    deadline: str | None = None
    deadline_dt: datetime | None = None
    status: str | None = None


class AssignmentOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: str
    deadline: str
    status: str
    file_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
