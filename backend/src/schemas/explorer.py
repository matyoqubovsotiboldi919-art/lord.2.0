from pydantic import BaseModel


class ExplorerTxOut(BaseModel):
    tx_hash: str
    amount_usdt: str
    created_at: str
    status: str

    block_index: int
    block_hash: str
    prev_hash: str

    sender: str
    receiver: str