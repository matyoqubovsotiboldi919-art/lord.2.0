import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.user import User
from .sessions import is_session_active

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _norm_password(p: str) -> str:
    """
    bcrypt has 72-byte input limit.
    We normalize password into fixed-length hex string (64 chars).
    """
    if p is None:
        p = ""
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def hash_password(p: str) -> str:
    # Always hash normalized form to avoid 72-byte issue
    return pwd.hash(_norm_password(p))


def verify_password(p: str, h: str) -> bool:
    """
    Backward compatible:
    1) try raw password (for old hashes)
    2) fallback to normalized password (new hashes)
    """
    try:
        if pwd.verify(p, h):
            return True
    except Exception:
        pass
    return pwd.verify(_norm_password(p), h)


def create_access_token(user_id: uuid.UUID, session_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.JWT_EXPIRES_MIN)
    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])


def auth_user(db: Session, email: str, password: str) -> User | None:
    u = db.query(User).filter(User.email == email).first()
    if not u:
        return None
    if not u.password_hash:
        return None
    if not verify_password(password, u.password_hash):
        return None
    return u


def require_active_session(db: Session, user_id: uuid.UUID, session_id: str) -> bool:
    return is_session_active(db, user_id, session_id)