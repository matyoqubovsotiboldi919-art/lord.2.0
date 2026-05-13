from datetime import datetime, timezone, timedelta

import jwt
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models.user import User
from ..schemas.user import MeOut
from ..services.security import decode_token, require_active_session
from ..services.logs import log_event

auth_scheme = HTTPBearer()
router = APIRouter(prefix="/api/v1/users", tags=["users"])

LOCK_MINUTES = 60


def now_utc():
    return datetime.now(timezone.utc)


def lock_user_for_token_attack(db: Session, u: User, request: Request | None = None):
    u.status = "LOCKED"
    u.locked_until = now_utc() + timedelta(minutes=LOCK_MINUTES)

    log_event(
        db,
        "WARN",
        "TOKEN_TAMPER_LOCK",
        f"User locked for 1 hour because of invalid/tampered token: {u.email}",
        actor_user_id=u.id,
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    db.commit()


def unlock_if_time_passed(u: User) -> bool:
    if u.status == "LOCKED" and u.locked_until:
        if u.locked_until <= now_utc():
            u.status = "ACTIVE"
            u.failed_login_count = 0
            u.locked_until = None
            return True
    return False


def extract_user_id_from_invalid_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
            },
        )
        return payload.get("sub")
    except Exception:
        return None


def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        user_id = extract_user_id_from_invalid_token(creds.credentials)

        if user_id:
            u = db.query(User).filter(User.id == user_id).first()
            if u:
                lock_user_for_token_attack(db, u, request)

        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    sid = payload.get("sid")

    if not user_id or not sid:
        raise HTTPException(status_code=401, detail="Invalid token")

    u = db.query(User).filter(User.id == user_id).first()

    if not u:
        raise HTTPException(status_code=401, detail="User not found")

    unlock_if_time_passed(u)

    if u.status == "LOCKED":
        db.commit()
        raise HTTPException(status_code=403, detail="Account locked")

    if u.status == "FROZEN":
        raise HTTPException(status_code=403, detail="Account frozen")

    if not require_active_session(db, u.id, sid):
        raise HTTPException(status_code=401, detail="Session expired")

    db.commit()

    return u


@router.get("/me", response_model=MeOut)
def me(u: User = Depends(get_current_user)):
    return MeOut(
        public_id=u.public_id,
        address=u.address,
        email=u.email,
        balance_usdt=str(u.balance_usdt),
        status=u.status,
        role=u.role,
    )