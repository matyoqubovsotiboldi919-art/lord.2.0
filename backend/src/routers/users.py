from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models.user import User
from ..schemas.user import MeOut
from ..services.security import decode_token, require_active_session

auth_scheme = HTTPBearer()
router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    sid = payload.get("sid")
    if not user_id or not sid:
        raise HTTPException(status_code=401, detail="Invalid token")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=401, detail="User not found")

    if not require_active_session(db, u.id, sid):
        raise HTTPException(status_code=401, detail="Session expired")

    return u


@router.get("/me", response_model=MeOut)
def me(u: User = Depends(get_current_user)):
    return MeOut(
        public_id=u.public_id,
        address=u.address,
        email=u.email,
        balance_usdt=str(u.balance_usdt),
        status=u.status,
        role=u.role
    )