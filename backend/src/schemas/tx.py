from pydantic import BaseModel, Field


class TransferIn(BaseModel):
    receiver_address: str = Field(min_length=8, max_length=128)
    amount_usdt: str  # Decimal string


class TxRow(BaseModel):
    direction: str  # IN/OUT
    counterparty: str
    amount_usdt: str
    created_at: str
    status: str
    tx_hash: str