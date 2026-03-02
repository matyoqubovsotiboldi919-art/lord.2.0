import base64
import hashlib
import hmac
import os
import secrets
import uuid

from ..core.config import settings


def new_public_id() -> str:
    # LORD- + 10 hex chars (unik bo‘lishi uchun DB UNIQUE bilan tekshiriladi)
    return "LORD-" + secrets.token_hex(5).upper()


def hmac_address(user_id: uuid.UUID) -> str:
    key = settings.ADDRESS_SECRET.encode("utf-8")
    msg = str(user_id).encode("utf-8")
    digest = hmac.new(key, msg, hashlib.sha256).digest()
    # base32, padding yo‘q
    addr = base64.b32encode(digest).decode("utf-8").rstrip("=")
    return "LORD_" + addr[:42]


def tx_hash(sender_addr: str, receiver_addr: str, amount_str: str, ts_iso: str, nonce: str) -> str:
    raw = f"{sender_addr}|{receiver_addr}|{amount_str}|{ts_iso}|{nonce}".encode("utf-8")
    return "TX_" + hashlib.sha256(raw).hexdigest()


def block_hash(block_index: int, prev_hash: str, tx_hash_value: str, ts_iso: str) -> str:
    raw = f"{block_index}|{prev_hash}|{tx_hash_value}|{ts_iso}".encode("utf-8")
    return "BLK_" + hashlib.sha256(raw).hexdigest()


def new_nonce() -> str:
    return secrets.token_hex(16)