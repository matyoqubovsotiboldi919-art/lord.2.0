from datetime import datetime, timezone, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models.user import User
from ..schemas.auth import RegisterIn, LoginIn, TokenOut
from ..services.security import hash_password, verify_password, create_access_token
from ..services.sessions import create_new_session
from ..services.hashers import new_public_id, hmac_address
from ..services.logs import log_event

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

MAX_FAILED_LOGIN = 3
LOCK_MINUTES = 60


def now_utc():
    return datetime.now(timezone.utc)


def lock_user_for_1_hour(u: User):
    u.status = "LOCKED"
    u.locked_until = now_utc() + timedelta(minutes=LOCK_MINUTES)


def unlock_if_time_passed(u: User) -> bool:
    if u.status == "LOCKED" and u.locked_until:
        if u.locked_until <= now_utc():
            u.status = "ACTIVE"
            u.failed_login_count = 0
            u.locked_until = None
            return True
    return False


def locked_message(u: User) -> str:
    if u.locked_until:
        return f"Account locked until {u.locked_until.isoformat()}"
    return "Account locked"


@router.post("/register")
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    u = User(
        balance_usdt=Decimal("1000"),
        email=payload.email,
        password_hash=hash_password(payload.password),
        public_id="TEMP",
        address="TEMP",
        role="USER",
        status="ACTIVE",
        failed_login_count=0,
        locked_until=None,
    )

    db.add(u)
    db.flush()

    for _ in range(5):
        pid = new_public_id()
        if not db.query(User).filter(User.public_id == pid).first():
            u.public_id = pid
            break

    u.address = hmac_address(u.id)

    db.commit()

    log_event(
        db,
        "INFO",
        "REGISTER",
        f"User registered {u.email}",
        actor_user_id=u.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    return {"ok": True}


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == payload.email).first()

    if not u:
        log_event(
            db,
            "WARN",
            "LOGIN_FAIL",
            f"Login failed for unknown email {payload.email}",
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    unlock_if_time_passed(u)

    if u.status == "LOCKED":
        db.commit()
        raise HTTPException(status_code=403, detail=locked_message(u))

    if not verify_password(payload.password, u.password_hash):
        u.failed_login_count = int(u.failed_login_count or 0) + 1

        log_event(
            db,
            "WARN",
            "LOGIN_FAIL",
            f"Login failed for {u.email}. Attempt {u.failed_login_count}",
            actor_user_id=u.id,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        if u.failed_login_count >= MAX_FAILED_LOGIN:
            lock_user_for_1_hour(u)

            log_event(
                db,
                "WARN",
                "ACCOUNT_LOCKED",
                f"User locked for 1 hour after 3 failed login attempts: {u.email}",
                actor_user_id=u.id,
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

            db.commit()
            raise HTTPException(status_code=403, detail=locked_message(u))

        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if u.status == "FROZEN":
        raise HTTPException(status_code=403, detail="Account frozen")

    u.failed_login_count = 0
    u.locked_until = None
    u.status = "ACTIVE"

    sid = create_new_session(db, u.id)
    u.last_login_at = now_utc()

    token = create_access_token(u.id, sid, u.role)

    log_event(
        db,
        "INFO",
        "LOGIN_OK",
        f"Login OK for {u.email}",
        actor_user_id=u.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()

    return TokenOut(access_token=token)