from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from decimal import Decimal
from ..core.db import get_db
from ..models.user import User
from ..schemas.auth import RegisterIn, LoginIn, TokenOut
from ..services.security import hash_password, auth_user, create_access_token
from ..services.sessions import create_new_session
from ..services.hashers import new_public_id, hmac_address
from ..services.logs import log_event

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


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
    )
    db.add(u)
    db.flush()  # get u.id

    # Generate immutable IDs after we have UUID
    # public_id must be unique (retry if collision)
    for _ in range(5):
        pid = new_public_id()
        if not db.query(User).filter(User.public_id == pid).first():
            u.public_id = pid
            break
    u.address = hmac_address(u.id)

    # Initial mint (optional if your base already has SYSTEM_MINT logic)
    # Here we keep 0 by default - if you need 1000 USDT seed, set it here:
    # u.balance_usdt = Decimal("1000")

    db.commit()

    log_event(db, "INFO", "REGISTER", f"User registered {u.email}", actor_user_id=u.id, ip=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    db.commit()
    return {"ok": True}


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    u = auth_user(db, payload.email, payload.password)
    if not u:
        log_event(db, "WARN", "LOGIN_FAIL", f"Login failed for {payload.email}", ip=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if u.status == "LOCKED":
        raise HTTPException(status_code=403, detail="Account locked")

    sid = create_new_session(db, u.id)
    u.last_login_at = datetime.now(timezone.utc)

    token = create_access_token(u.id, sid, u.role)

    log_event(db, "INFO", "LOGIN_OK", f"Login OK for {u.email}", actor_user_id=u.id, ip=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    db.commit()

    return TokenOut(access_token=token)