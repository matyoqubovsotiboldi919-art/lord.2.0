from pydantic import BaseModel


class AdminUserRow(BaseModel):
    public_id: str
    address: str
    email: str
    balance_usdt: str
    status: str
    created_at: str
    last_login_at: str | None


class AdminTxRow(BaseModel):
    tx_hash: str
    sender: str
    receiver: str
    amount_usdt: str
    status: str
    method: str
    created_at: str


class AdminLogRow(BaseModel):
    level: str
    event_type: str
    message: str
    created_at: str
    actor: str | None