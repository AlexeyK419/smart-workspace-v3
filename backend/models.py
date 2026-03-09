from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id:       Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name:     Mapped[str] = mapped_column(String(120))
    initials: Mapped[str] = mapped_column(String(10))
    role:     Mapped[str] = mapped_column(String(120), default="Студент")

    courses: Mapped[list["Course"]] = relationship("Course", back_populates="user", cascade="all, delete-orphan")
    schedule_events: Mapped[list["ScheduleEvent"]] = relationship(
        "ScheduleEvent",
        back_populates="user",
        cascade="all, delete-orphan",
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
