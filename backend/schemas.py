from datetime import datetime
from pydantic import BaseModel, Field


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


class CourseCreate(BaseModel):
    name: str
    color: str = "#3d52d5"
    emoji: str = "📘"
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
    ai_plan: str | None = None
    materials: list["MaterialOut"] = Field(default_factory=list)
    assignments: list["AssignmentOut"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


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
    deadline_dt: datetime | None = None
    status: str
    file_name: str | None = None
    ai_advice: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleEventBase(BaseModel):
    title: str
    day_index: int
    start_minute: int
    duration_minutes: int = 90
    location: str = ""
    teacher: str = ""
    type: str = "lecture"
    color: str = "#3d52d5"


class ScheduleEventCreate(ScheduleEventBase):
    pass


class ScheduleEventUpdate(BaseModel):
    title: str | None = None
    day_index: int | None = None
    start_minute: int | None = None
    duration_minutes: int | None = None
    location: str | None = None
    teacher: str | None = None
    type: str | None = None
    color: str | None = None


class ScheduleEventOut(ScheduleEventBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
