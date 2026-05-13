from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models.transaction import Transaction
from ..models.block import Block
from ..models.user import User
from ..schemas.explorer import ExplorerTxOut, ExplorerAddressOut, ExplorerAddressTxRow
from ..services.tx import mask_address
from ..services.security import decode_token, require_active_session

router = APIRouter(prefix="/api/v1/explorer", tags=["explorer"])

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


@router.get("/address/{address}", response_model=ExplorerAddressOut)
def explorer_address(address: str, db: Session = Depends(get_db)):
    address = address.strip()
    if not address:
        raise HTTPException(status_code=400, detail="Address is required")

    user = db.query(User).filter(User.address == address).first()

    rows = (
        db.query(Transaction)
        .filter(or_(Transaction.sender_address == address, Transaction.receiver_address == address))
        .order_by(Transaction.created_at.desc())
        .limit(500)
        .all()
    )

    last_active = rows[0].created_at.isoformat() if rows else None

    return ExplorerAddressOut(
        address=address,
        exists=bool(user),
        balance_usdt=str(user.balance_usdt) if user else "0",
        last_active=last_active,
        transactions=[
            ExplorerAddressTxRow(
                from_address=t.sender_address,
                to_address=t.receiver_address,
                amount_usdt=str(t.amount_usdt),
                created_at=t.created_at.isoformat(),
                status=t.status,
                tx_hash=t.tx_hash,
            )
            for t in rows
        ],
    )