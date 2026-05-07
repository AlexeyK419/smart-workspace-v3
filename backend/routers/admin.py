import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from config import settings
from auth import get_current_admin
from database import get_db
import models
import schemas

router = APIRouter(prefix="/admin", tags=["admin"])
ADMIN_EMAIL = settings.admin_email.strip().lower()


def _remove_file(path: str | None):
    if path and os.path.exists(path) and os.path.isfile(path):
        os.remove(path)


def _user_detail_query(db: Session):
    return db.query(models.User).options(
        selectinload(models.User.courses).selectinload(models.Course.materials),
        selectinload(models.User.courses).selectinload(models.Course.assignments).selectinload(models.Assignment.files),
        selectinload(models.User.schedule_events),
        selectinload(models.User.owned_projects).selectinload(models.Project.files),
        selectinload(models.User.owned_projects).selectinload(models.Project.tasks).selectinload(models.ProjectTask.comments),
        selectinload(models.User.owned_projects).selectinload(models.Project.messages),
        selectinload(models.User.owned_projects).selectinload(models.Project.members),
        selectinload(models.User.project_memberships),
    )


def _count_user_files(db: Session, user_id: int) -> int:
    material_count = (
        db.query(models.Material)
        .join(models.Course, models.Course.id == models.Material.course_id)
        .filter(models.Course.user_id == user_id)
        .count()
    )
    assignment_file_count = (
        db.query(models.AssignmentFile)
        .join(models.Assignment, models.Assignment.id == models.AssignmentFile.assignment_id)
        .join(models.Course, models.Course.id == models.Assignment.course_id)
        .filter(models.Course.user_id == user_id)
        .count()
    )
    project_file_count = db.query(models.ProjectFile).filter(models.ProjectFile.uploader_id == user_id).count()
    return material_count + assignment_file_count + project_file_count


def _serialize_admin_user(db: Session, user: models.User) -> schemas.AdminUserOut:
    return schemas.AdminUserOut(
        id=user.id,
        name=user.name,
        initials=user.initials,
        role=user.role,
        email=user.email,
        workspace_ai_summary=user.workspace_ai_summary,
        courses_count=db.query(models.Course).filter(models.Course.user_id == user.id).count(),
        projects_count=(
            db.query(models.ProjectMember.project_id)
            .filter(models.ProjectMember.user_id == user.id)
            .distinct()
            .count()
        ),
        files_count=_count_user_files(db, user.id),
    )


@router.get("/users", response_model=list[schemas.AdminUserOut])
def list_users(
    _: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = (
        db.query(models.User)
        .filter(func.lower(models.User.email) != ADMIN_EMAIL)
        .order_by(models.User.id.asc())
        .all()
    )
    return [_serialize_admin_user(db, user) for user in users]


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    _: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = _user_detail_query(db).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if (user.email or "").strip().lower() == ADMIN_EMAIL:
        raise HTTPException(status_code=400, detail="Admin account cannot be deleted")

    file_paths: set[str] = set()
    owned_project_ids = [project.id for project in user.owned_projects]
    owned_project_id_set = set(owned_project_ids)

    for course in user.courses:
        for material in course.materials:
            if material.file_path:
                file_paths.add(material.file_path)
        for assignment in course.assignments:
            if assignment.file_path:
                file_paths.add(assignment.file_path)
            for assignment_file in assignment.files:
                if assignment_file.file_path:
                    file_paths.add(assignment_file.file_path)

    for project in user.owned_projects:
        for project_file in project.files:
            if project_file.file_path:
                file_paths.add(project_file.file_path)

    uploaded_files = db.query(models.ProjectFile).filter(models.ProjectFile.uploader_id == user.id).all()
    for project_file in uploaded_files:
        if project_file.file_path:
            file_paths.add(project_file.file_path)

    direct_chats = (
        db.query(models.DirectChat)
        .options(selectinload(models.DirectChat.messages), selectinload(models.DirectChat.participants))
        .filter(or_(models.DirectChat.first_user_id == user.id, models.DirectChat.second_user_id == user.id))
        .all()
    )
    for chat in direct_chats:
        db.delete(chat)

    for project_file in uploaded_files:
        if project_file.project_id not in owned_project_id_set:
            db.delete(project_file)

    comments = db.query(models.ProjectTaskComment).filter(models.ProjectTaskComment.author_id == user.id).all()
    for comment in comments:
        db.delete(comment)

    messages = db.query(models.ProjectMessage).filter(models.ProjectMessage.author_id == user.id).all()
    for message in messages:
        db.delete(message)

    created_tasks_query = db.query(models.ProjectTask).filter(models.ProjectTask.created_by_id == user.id)
    if owned_project_ids:
        created_tasks_query = created_tasks_query.filter(~models.ProjectTask.project_id.in_(owned_project_ids))
    created_tasks = created_tasks_query.all()
    for task in created_tasks:
        db.delete(task)

    db.query(models.ProjectTask).filter(models.ProjectTask.assignee_id == user.id).update(
        {models.ProjectTask.assignee_id: None},
        synchronize_session=False,
    )

    memberships = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == user.id).all()
    for membership in memberships:
        if membership.project_id not in owned_project_id_set:
            db.delete(membership)

    db.query(models.AiContextChunk).filter(models.AiContextChunk.user_id == user.id).delete(synchronize_session=False)

    for project in user.owned_projects:
        db.delete(project)

    db.delete(user)
    db.commit()

    for path in file_paths:
        _remove_file(path)
