from pydantic import BaseModel, Field


class TransferIn(BaseModel):
    receiver_address: str = Field(min_length=8, max_length=128)
    amount_usdt: str


class TxRow(BaseModel):
    from_address: str
    to_address: str
    amount_usdt: str
    created_at: str
    status: str
    tx_hash: str