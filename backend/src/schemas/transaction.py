from pydantic import BaseModel, Field


class SendTxIn(BaseModel):
    to_username: str = Field(min_length=3, max_length=50)
    amount: float = Field(gt=0)


class TxOut(BaseModel):
    tx_hash: str
    sender_id: int
    receiver_id: int
    amount: float

    class Config:
        from_attributes = True