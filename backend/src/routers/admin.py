from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models.user import User
from ..models.transaction import Transaction
from ..models.system_log import SystemLog
from ..schemas.admin import AdminUserRow, AdminTxRow, AdminLogRow
from ..services.tx import mask_address
from .users import get_current_user

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def require_admin(me: User = Depends(get_current_user)) -> User:
    if me.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")
    return me


@router.get("/users", response_model=list[AdminUserRow])
def admin_users(db: Session = Depends(get_db), me: User = Depends(require_admin)):
    users = db.query(User).order_by(User.created_at.desc()).limit(500).all()
    return [
        AdminUserRow(
            public_id=u.public_id,
            address=u.address,
            email=u.email,
            balance_usdt=str(u.balance_usdt),
            status=u.status,
            created_at=u.created_at.isoformat(),
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None
        )
        for u in users
    ]


@router.post("/users/{public_id}/freeze")
def freeze_user(public_id: str, db: Session = Depends(get_db), me: User = Depends(require_admin)):
    u = db.query(User).filter(User.public_id == public_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.status = "FROZEN"
    db.commit()
    return {"ok": True}


@router.post("/users/{public_id}/unfreeze")
def unfreeze_user(public_id: str, db: Session = Depends(get_db), me: User = Depends(require_admin)):
    u = db.query(User).filter(User.public_id == public_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.status = "ACTIVE"
    db.commit()
    return {"ok": True}


@router.get("/transactions", response_model=list[AdminTxRow])
def admin_txs(db: Session = Depends(get_db), me: User = Depends(require_admin)):
    txs = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(500).all()
    return [
        AdminTxRow(
            tx_hash=t.tx_hash,
            sender=mask_address(t.sender_address),
            receiver=mask_address(t.receiver_address),
            amount_usdt=str(t.amount_usdt),
            status=t.status,
            method=t.method,
            created_at=t.created_at.isoformat()
        )
        for t in txs
    ]


@router.get("/logs", response_model=list[AdminLogRow])
def admin_logs(db: Session = Depends(get_db), me: User = Depends(require_admin)):
    logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(500).all()
    # actor as public_id if possible
    user_map = {str(u.id): u.public_id for u in db.query(User).all()}
    out = []
    for l in logs:
        actor = user_map.get(str(l.actor_user_id)) if l.actor_user_id else None
        out.append(AdminLogRow(
            level=l.level,
            event_type=l.event_type,
            message=l.message,
            created_at=l.created_at.isoformat(),
            actor=actor
        ))
    return out