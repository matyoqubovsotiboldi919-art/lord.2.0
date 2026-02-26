from fastapi import APIRouter, Depends
from src.models.user import User
from src.schemas.user import UserOut
from src.services.security import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current