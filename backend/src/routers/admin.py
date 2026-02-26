from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.config import settings
from src.db.session import get_db
from src.models.user import User
from src.schemas.admin import AdminLoginIn
from src.services.security import create_access_token, require_admin, hash_password, verify_password

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/login")
def admin_login(payload: AdminLoginIn):
    if payload.username != settings.ADMIN_USERNAME or payload.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    # admin token subject is literal "admin" but we won't use get_current_user for it;
    # we will protect admin routes using real admin user in DB (seeded).
    token = create_access_token(subject="admin")
    return {"access_token": token, "token_type": "bearer"}


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id.asc()).limit(500).all()
    return [{
        "id": u.id, "username": u.username, "email": u.email,
        "is_admin": u.is_admin, "is_active": u.is_active, "balance": float(u.balance)
    } for u in users]


@router.post("/users/{user_id}/freeze")
def freeze_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.is_admin:
        raise HTTPException(status_code=400, detail="Cannot freeze admin")
    u.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/unfreeze")
def unfreeze_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.is_active = True
    db.commit()
    return {"ok": True}