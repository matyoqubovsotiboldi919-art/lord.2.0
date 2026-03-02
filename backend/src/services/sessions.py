import secrets
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.session import Session as DbSession


def create_new_session(db: Session, user_id: uuid.UUID) -> str:
    # Revoke all old sessions (DB time)
    db.query(DbSession).filter(
        and_(DbSession.user_id == user_id, DbSession.revoked_at.is_(None))
    ).update(
        {"revoked_at": func.now()},
        synchronize_session=False
    )

    sid = "SID_" + secrets.token_hex(24)
    db.add(DbSession(user_id=user_id, session_id=sid))
    return sid


def is_session_active(db: Session, user_id: uuid.UUID, sid: str) -> bool:
    row = db.query(DbSession).filter(
        DbSession.user_id == user_id,
        DbSession.session_id == sid,
        DbSession.revoked_at.is_(None)
    ).first()
    return row is not None