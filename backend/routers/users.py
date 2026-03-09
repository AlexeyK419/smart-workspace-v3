from fastapi import APIRouter, Depends

from auth import get_current_user
import models
import schemas

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def get_current_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/me/courses", response_model=list[schemas.CourseOut])
def get_current_user_courses(current_user: models.User = Depends(get_current_user)):
    return current_user.courses
