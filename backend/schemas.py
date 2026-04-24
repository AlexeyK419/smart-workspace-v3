from datetime import datetime
from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    name: str
    initials: str
    role: str
    email: str | None = None

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=6)
    role: str = "Студент"


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class UserProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class UserPasswordUpdateRequest(BaseModel):
    current_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)


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
    materials: list[MaterialOut] = Field(default_factory=list)
    assignments: list[AssignmentOut] = Field(default_factory=list)

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


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    color: str = "#3d52d5"


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class ProjectMemberAddRequest(BaseModel):
    user_id: int | None = None
    email: str | None = None


class ProjectTaskCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class ProjectTaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "todo"
    due_date: datetime | None = None
    assignee_id: int | None = None


class ProjectTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    due_date: datetime | None = None
    assignee_id: int | None = None


class ProjectMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class DirectChatCreate(BaseModel):
    target_user_id: int


class DirectMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class ProjectMemberOut(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: str
    created_at: datetime
    user: UserOut

    model_config = {"from_attributes": True}


class ProjectTaskCommentOut(BaseModel):
    id: int
    task_id: int
    author_id: int
    body: str
    created_at: datetime
    author: UserOut | None = None

    model_config = {"from_attributes": True}


class ProjectTaskOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: str
    status: str
    due_date: datetime | None = None
    assignee_id: int | None = None
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    assignee: UserOut | None = None
    creator: UserOut | None = None
    comments: list[ProjectTaskCommentOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProjectFileOut(BaseModel):
    id: int
    project_id: int
    uploader_id: int
    name: str
    size_bytes: int
    mime_type: str
    icon: str
    icon_bg: str
    created_at: datetime
    uploader: UserOut | None = None

    model_config = {"from_attributes": True}


class ProjectMessageOut(BaseModel):
    id: int
    project_id: int
    author_id: int
    body: str
    created_at: datetime
    author: UserOut | None = None

    model_config = {"from_attributes": True}


class DirectMessageOut(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    body: str
    created_at: datetime
    sender: UserOut | None = None

    model_config = {"from_attributes": True}


class DirectChatOut(BaseModel):
    id: int
    first_user_id: int
    second_user_id: int
    created_at: datetime
    updated_at: datetime
    peer: UserOut
    last_message: DirectMessageOut | None = None
    unread_count: int = 0

    model_config = {"from_attributes": True}


class ProjectOut(BaseModel):
    id: int
    owner_id: int
    name: str
    description: str
    color: str
    created_at: datetime
    owner: UserOut | None = None
    members: list[ProjectMemberOut] = Field(default_factory=list)
    tasks: list[ProjectTaskOut] = Field(default_factory=list)
    files: list[ProjectFileOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
