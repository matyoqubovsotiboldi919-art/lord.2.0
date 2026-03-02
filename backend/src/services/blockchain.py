from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.block import Block
from .hashers import block_hash as make_block_hash


def get_last_block(db: Session) -> Block | None:
    return db.query(Block).order_by(Block.block_index.desc()).first()


def create_block_for_tx(
    db: Session,
    tx_hash: str,
    sender_address: str,
    receiver_address: str,
    amount_usdt: Decimal,
    method: str,
    status: str
) -> Block:
    last = get_last_block(db)
    next_index = 1 if not last else int(last.block_index) + 1
    prev = "GENESIS" if not last else last.block_hash

    ts = datetime.now(timezone.utc).isoformat()
    blk_hash = make_block_hash(next_index, prev, tx_hash, ts)

    blk = Block(
        block_index=next_index,
        prev_hash=prev,
        block_hash=blk_hash,
        tx_hash=tx_hash,
        sender_address=sender_address,
        receiver_address=receiver_address,
        amount_usdt=amount_usdt,
        method=method,
        status=status
    )
    db.add(blk)
    return blk