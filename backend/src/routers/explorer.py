from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models.transaction import Transaction
from ..models.block import Block
from ..models.user import User
from ..schemas.explorer import ExplorerTxOut
from ..services.tx import mask_address
from ..services.security import decode_token, require_active_session

router = APIRouter(prefix="/api/v1/explorer", tags=["explorer"])

# OPTIONAL auth (token bo‘lmasa ham ishlaydi)
auth_optional = HTTPBearer(auto_error=False)


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None,
    db: Session
) -> User | None:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
        user_id = payload.get("sub")
        sid = payload.get("sid")
        if not user_id or not sid:
            return None

        u = db.query(User).filter(User.id == user_id).first()
        if not u:
            return None

        if not require_active_session(db, u.id, sid):
            return None

        return u
    except Exception:
        return None


@router.get("/tx/{tx_hash}", response_model=ExplorerTxOut)
def explorer_tx(
    tx_hash: str,
    db: Session = Depends(get_db),
    creds: HTTPAuthorizationCredentials | None = Depends(auth_optional),
):
    tx = db.query(Transaction).filter(Transaction.tx_hash == tx_hash).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    blk = db.query(Block).filter(Block.tx_hash == tx_hash).first()
    if not blk:
        raise HTTPException(status_code=404, detail="Block not found")

    me = get_optional_user(creds, db)
    is_admin = bool(me and me.role == "ADMIN")

    sender = tx.sender_address if is_admin else mask_address(tx.sender_address)
    receiver = tx.receiver_address if is_admin else mask_address(tx.receiver_address)

    return ExplorerTxOut(
        tx_hash=tx.tx_hash,
        amount_usdt=str(tx.amount_usdt),
        created_at=tx.created_at.isoformat(),
        status=tx.status,
        block_index=int(blk.block_index),
        block_hash=blk.block_hash,
        prev_hash=blk.prev_hash,
        sender=sender,
        receiver=receiver,
    )