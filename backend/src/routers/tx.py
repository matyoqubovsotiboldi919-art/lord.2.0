from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models.transaction import Transaction
from ..models.user import User
from ..schemas.tx import TransferIn, TxRow
from ..services.tx import transfer, mask_address
from .users import get_current_user

router = APIRouter(prefix="/api/v1/tx", tags=["transactions"])


@router.post("/transfer")
def do_transfer(payload: TransferIn, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if me.status == "FROZEN":
        raise HTTPException(status_code=403, detail="Account frozen")

    try:
        tx = transfer(db, me, payload.receiver_address, payload.amount_usdt, method="WEB_UI")
        db.commit()
        return {"ok": True, "tx_hash": tx.tx_hash}
    except PermissionError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        db.rollback()
        raise


@router.get("/history", response_model=list[TxRow])
def history(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    rows = (
        db.query(Transaction)
        .filter((Transaction.sender_user_id == me.id) | (Transaction.receiver_user_id == me.id))
        .order_by(Transaction.created_at.desc())
        .limit(200)
        .all()
    )

    out: list[TxRow] = []
    for t in rows:
        if str(t.sender_user_id) == str(me.id):
            direction = "OUT"
            counterparty = mask_address(t.receiver_address)
        else:
            direction = "IN"
            counterparty = mask_address(t.sender_address)

        out.append(
            TxRow(
                direction=direction,
                counterparty=counterparty,
                amount_usdt=str(t.amount_usdt),
                created_at=t.created_at.isoformat(),
                status=t.status,
                tx_hash=t.tx_hash,
            )
        )
    return out