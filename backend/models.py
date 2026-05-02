from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id:            Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name:          Mapped[str] = mapped_column(String(120))
    initials:      Mapped[str] = mapped_column(String(10))
    role:          Mapped[str] = mapped_column(String(120), default="Студент")
    email:         Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_salt: Mapped[str | None] = mapped_column(String(64), nullable=True)
    auth_token:    Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)

    courses: Mapped[list["Course"]] = relationship("Course", back_populates="user", cascade="all, delete-orphan")
    schedule_events: Mapped[list["ScheduleEvent"]] = relationship(
        "ScheduleEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    owned_projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Project.owner_id",
    )
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    assigned_project_tasks: Mapped[list["ProjectTask"]] = relationship(
        "ProjectTask",
        back_populates="assignee",
        foreign_keys="ProjectTask.assignee_id",
    )
    created_project_tasks: Mapped[list["ProjectTask"]] = relationship(
        "ProjectTask",
        back_populates="creator",
        foreign_keys="ProjectTask.created_by_id",
    )
    project_task_comments: Mapped[list["ProjectTaskComment"]] = relationship(
        "ProjectTaskComment",
        back_populates="author",
        foreign_keys="ProjectTaskComment.author_id",
    )
    uploaded_project_files: Mapped[list["ProjectFile"]] = relationship(
        "ProjectFile",
        back_populates="uploader",
        foreign_keys="ProjectFile.uploader_id",
    )
    project_messages: Mapped[list["ProjectMessage"]] = relationship(
        "ProjectMessage",
        back_populates="author",
        foreign_keys="ProjectMessage.author_id",
    )
    direct_chats_as_first_user: Mapped[list["DirectChat"]] = relationship(
        "DirectChat",
        back_populates="first_user",
        foreign_keys="DirectChat.first_user_id",
    )
    direct_chats_as_second_user: Mapped[list["DirectChat"]] = relationship(
        "DirectChat",
        back_populates="second_user",
        foreign_keys="DirectChat.second_user_id",
    )
    direct_chat_participations: Mapped[list["DirectChatParticipant"]] = relationship(
        "DirectChatParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    direct_messages: Mapped[list["DirectMessage"]] = relationship(
        "DirectMessage",
        back_populates="sender",
        foreign_keys="DirectMessage.sender_id",
    )


class Course(Base):
    __tablename__ = "courses"

    id:        Mapped[int]   = mapped_column(Integer, primary_key=True, index=True)
    user_id:   Mapped[int]   = mapped_column(Integer, ForeignKey("users.id"))
    name:      Mapped[str]   = mapped_column(String(200))
    color:     Mapped[str]   = mapped_column(String(20), default="#3d52d5")
    emoji:     Mapped[str]   = mapped_column(String(10), default="📘")
    teacher:   Mapped[str]   = mapped_column(String(200), default="")
    semester:  Mapped[str]   = mapped_column(String(100), default="")
    credits:   Mapped[int]   = mapped_column(Integer, default=3)
    progress:  Mapped[float] = mapped_column(Float, default=0.0)
    ai_plan:   Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    user:        Mapped["User"]             = relationship("User", back_populates="courses")
    materials:   Mapped[list["Material"]]   = relationship("Material", back_populates="course", cascade="all, delete-orphan")
    assignments: Mapped[list["Assignment"]] = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")


class Material(Base):
    __tablename__ = "materials"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    course_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("courses.id"))
    name:       Mapped[str]      = mapped_column(String(300))
    file_path:  Mapped[str]      = mapped_column(String(500))
    size_bytes: Mapped[int]      = mapped_column(Integer, default=0)
    mime_type:  Mapped[str]      = mapped_column(String(100), default="")
    icon:       Mapped[str]      = mapped_column(String(10), default="📄")
    icon_bg:    Mapped[str]      = mapped_column(String(20), default="#fee2e2")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    course: Mapped["Course"] = relationship("Course", back_populates="materials")


class Assignment(Base):
    __tablename__ = "assignments"

    id:          Mapped[int]             = mapped_column(Integer, primary_key=True, index=True)
    course_id:   Mapped[int]             = mapped_column(Integer, ForeignKey("courses.id"))
    title:       Mapped[str]             = mapped_column(String(300))
    description: Mapped[str]             = mapped_column(Text, default="")
    deadline:    Mapped[str]             = mapped_column(String(50), default="")
    deadline_dt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status:      Mapped[str]             = mapped_column(String(50), default="pending")
    file_path:   Mapped[str | None]      = mapped_column(String(500), nullable=True)
    file_name:   Mapped[str | None]      = mapped_column(String(300), nullable=True)
    ai_advice:   Mapped[str | None]      = mapped_column(Text, nullable=True, default=None)
    created_at:  Mapped[datetime]        = mapped_column(DateTime, default=datetime.utcnow)

    course: Mapped["Course"] = relationship("Course", back_populates="assignments")


class ScheduleEvent(Base):
    __tablename__ = "schedule_events"

    id:               Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    user_id:          Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"))
    title:            Mapped[str]      = mapped_column(String(200))
    day_index:        Mapped[int]      = mapped_column(Integer, default=0)
    start_minute:     Mapped[int]      = mapped_column(Integer, default=540)
    duration_minutes: Mapped[int]      = mapped_column(Integer, default=90)
    location:         Mapped[str]      = mapped_column(String(200), default="")
    teacher:          Mapped[str]      = mapped_column(String(200), default="")
    type:             Mapped[str]      = mapped_column(String(40), default="lecture")
    color:            Mapped[str]      = mapped_column(String(20), default="#3d52d5")
    created_at:       Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="schedule_events")


class Project(Base):
    __tablename__ = "projects"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    owner_id:    Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"))
    name:        Mapped[str]      = mapped_column(String(200))
    description: Mapped[str]      = mapped_column(Text, default="")
    color:       Mapped[str]      = mapped_column(String(20), default="#3d52d5")
    created_at:  Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["User"] = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    members: Mapped[list["ProjectMember"]] = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks: Mapped[list["ProjectTask"]] = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")
    files: Mapped[list["ProjectFile"]] = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    messages: Mapped[list["ProjectMessage"]] = relationship("ProjectMessage", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int]      = mapped_column(Integer, ForeignKey("projects.id"))
    user_id:    Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"))
    role:       Mapped[str]      = mapped_column(String(40), default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="project_memberships")


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id:            Mapped[int]             = mapped_column(Integer, primary_key=True, index=True)
    project_id:    Mapped[int]             = mapped_column(Integer, ForeignKey("projects.id"))
    title:         Mapped[str]             = mapped_column(String(300))
    description:   Mapped[str]             = mapped_column(Text, default="")
    status:        Mapped[str]             = mapped_column(String(50), default="todo")
    due_date:      Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    assignee_id:   Mapped[int | None]      = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id: Mapped[int]             = mapped_column(Integer, ForeignKey("users.id"))
    created_at:    Mapped[datetime]        = mapped_column(DateTime, default=datetime.utcnow)
    updated_at:    Mapped[datetime]        = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at:  Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped["User"] = relationship("User", back_populates="assigned_project_tasks", foreign_keys=[assignee_id])
    creator: Mapped["User"] = relationship("User", back_populates="created_project_tasks", foreign_keys=[created_by_id])
    comments: Mapped[list["ProjectTaskComment"]] = relationship(
        "ProjectTaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="ProjectTaskComment.created_at.asc()",
    )


class ProjectTaskComment(Base):
    __tablename__ = "project_task_comments"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    task_id:    Mapped[int]      = mapped_column(Integer, ForeignKey("project_tasks.id"))
    author_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"))
    body:       Mapped[str]      = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped["ProjectTask"] = relationship("ProjectTask", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="project_task_comments", foreign_keys=[author_id])


class ProjectFile(Base):
    __tablename__ = "project_files"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    project_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("projects.id"))
    uploader_id: Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"))
    name:        Mapped[str]      = mapped_column(String(300))
    file_path:   Mapped[str]      = mapped_column(String(500))
    size_bytes:  Mapped[int]      = mapped_column(Integer, default=0)
    mime_type:   Mapped[str]      = mapped_column(String(100), default="")
    icon:        Mapped[str]      = mapped_column(String(10), default="📄")
    icon_bg:     Mapped[str]      = mapped_column(String(20), default="#fee2e2")
    created_at:  Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="files")
    uploader: Mapped["User"] = relationship("User", back_populates="uploaded_project_files", foreign_keys=[uploader_id])


class ProjectMessage(Base):
    __tablename__ = "project_messages"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int]      = mapped_column(Integer, ForeignKey("projects.id"))
    author_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"))
    body:       Mapped[str]      = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="messages")
    author: Mapped["User"] = relationship("User", back_populates="project_messages", foreign_keys=[author_id])


class DirectChat(Base):
    __tablename__ = "direct_chats"
    __table_args__ = (UniqueConstraint("first_user_id", "second_user_id", name="uq_direct_chat_pair"),)

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    first_user_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"), index=True)
    second_user_id: Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"), index=True)
    created_at:     Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at:     Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    first_user: Mapped["User"] = relationship(
        "User",
        back_populates="direct_chats_as_first_user",
        foreign_keys=[first_user_id],
    )
    second_user: Mapped["User"] = relationship(
        "User",
        back_populates="direct_chats_as_second_user",
        foreign_keys=[second_user_id],
    )
    participants: Mapped[list["DirectChatParticipant"]] = relationship(
        "DirectChatParticipant",
        back_populates="chat",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["DirectMessage"]] = relationship(
        "DirectMessage",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="DirectMessage.created_at.asc()",
    )


class DirectChatParticipant(Base):
    __tablename__ = "direct_chat_participants"
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_direct_chat_participant"),)

    id:           Mapped[int]             = mapped_column(Integer, primary_key=True, index=True)
    chat_id:      Mapped[int]             = mapped_column(Integer, ForeignKey("direct_chats.id"), index=True)
    user_id:      Mapped[int]             = mapped_column(Integer, ForeignKey("users.id"), index=True)
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at:   Mapped[datetime]        = mapped_column(DateTime, default=datetime.utcnow)

    chat: Mapped["DirectChat"] = relationship("DirectChat", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="direct_chat_participations")


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    chat_id:    Mapped[int]      = mapped_column(Integer, ForeignKey("direct_chats.id"), index=True)
    sender_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("users.id"), index=True)
    body:       Mapped[str]      = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    chat: Mapped["DirectChat"] = relationship("DirectChat", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="direct_messages", foreign_keys=[sender_id])


class AiContextChunk(Base):
    __tablename__ = "ai_context_chunks"
    __table_args__ = (
        UniqueConstraint("user_id", "source_key", "chunk_index", name="uq_ai_context_chunk_source_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    scope: Mapped[str] = mapped_column(String(40), index=True)
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[str] = mapped_column(String(80), index=True)
    parent_type: Mapped[str] = mapped_column(String(60), default="", index=True)
    parent_id: Mapped[str] = mapped_column(String(80), default="", index=True)
    source_key: Mapped[str] = mapped_column(String(220), index=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(400), default="")
    text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    embedding_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
