from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.user import User
from ..models.transaction import Transaction
from ..services.hashers import tx_hash as make_tx_hash, new_nonce
from ..services.blockchain import create_block_for_tx
from ..services.logs import log_event


def parse_amount(amount_str: str) -> Decimal:
    try:
        a = Decimal(amount_str)
    except InvalidOperation:
        raise ValueError("Invalid amount")
    if a <= 0:
        raise ValueError("Amount must be > 0")
    return a


def mask_address(addr: str) -> str:
    if len(addr) <= 10:
        return addr
    return addr[:6] + "..." + addr[-6:]


def transfer(db: Session, sender: User, receiver_address: str, amount_str: str, method: str = "WEB_UI"):
    if sender.status != "ACTIVE":
        raise PermissionError("Your account is not active")

    receiver = db.query(User).filter(User.address == receiver_address).first()
    if not receiver:
        raise ValueError("Receiver not found")

    if receiver.id == sender.id:
        raise ValueError("Cannot send to yourself")

    if receiver.status != "ACTIVE":
        raise ValueError("Receiver is not active")

    amount = parse_amount(amount_str)

    # Balance check
    if Decimal(str(sender.balance_usdt)) < amount:
        raise ValueError("Insufficient balance")

    ts = datetime.now(timezone.utc).isoformat()
    nonce = new_nonce()
    th = make_tx_hash(sender.address, receiver.address, str(amount), ts, nonce)

    # Atomic section: update balances + insert tx + insert block
    # We rely on outer transaction in router (db.begin())
    sender.balance_usdt = Decimal(str(sender.balance_usdt)) - amount
    receiver.balance_usdt = Decimal(str(receiver.balance_usdt)) + amount

    tx = Transaction(
        tx_hash=th,
        sender_user_id=sender.id,
        receiver_user_id=receiver.id,
        sender_address=sender.address,
        receiver_address=receiver.address,
        amount_usdt=amount,
        method=method,
        status="CONFIRMED"
    )
    db.add(tx)

    create_block_for_tx(
        db=db,
        tx_hash=th,
        sender_address=sender.address,
        receiver_address=receiver.address,
        amount_usdt=amount,
        method=method,
        status="CONFIRMED"
    )

    log_event(db, "INFO", "TX_CONFIRMED", f"TX {th} {mask_address(sender.address)} -> {mask_address(receiver.address)} {amount} USDT", actor_user_id=sender.id)

    return tx