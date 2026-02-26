import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import User
from src.models.transaction import Transaction
from src.schemas.transaction import SendTxIn, TxOut
from src.services.security import get_current_user

router = APIRouter(prefix="/api/v1/tx", tags=["transactions"])


@router.post("/send", response_model=TxOut)
def send_tx(payload: SendTxIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    receiver = db.query(User).filter(User.username == payload.to_username).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    if not current.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    if float(current.balance) < float(payload.amount):
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # atomic-ish: single transaction
    current.balance = float(current.balance) - float(payload.amount)
    receiver.balance = float(receiver.balance) + float(payload.amount)

    tx_hash = uuid.uuid4().hex
    tx = Transaction(
        sender_id=current.id,
        receiver_id=receiver.id,
        amount=payload.amount,
        tx_hash=tx_hash,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return tx