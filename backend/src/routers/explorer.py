from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.transaction import Transaction
from src.models.user import User

router = APIRouter(prefix="/api/v1/explorer", tags=["explorer"])


@router.get("/tx/{tx_hash}")
def tx_by_hash(tx_hash: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.tx_hash == tx_hash).first()
    return {"found": bool(tx), "tx": tx.__dict__ if tx else None}


@router.get("/address/{username}")
def user_by_username(username: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == username).first()
    if not u:
        return {"found": False}
    return {
        "found": True,
        "user": {"id": u.id, "username": u.username, "balance": float(u.balance), "is_active": u.is_active},
    }


@router.get("/latest")
def latest(db: Session = Depends(get_db), limit: int = 50):
    q = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(min(limit, 200))
    items = []
    for tx in q:
        items.append({
            "tx_hash": tx.tx_hash,
            "sender_id": tx.sender_id,
            "receiver_id": tx.receiver_id,
            "amount": float(tx.amount),
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        })
    return {"items": items}