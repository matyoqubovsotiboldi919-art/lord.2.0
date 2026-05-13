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


class ExplorerAddressTxRow(BaseModel):
    from_address: str
    to_address: str
    amount_usdt: str
    created_at: str
    status: str
    tx_hash: str


class ExplorerAddressOut(BaseModel):
    address: str
    exists: bool
    balance_usdt: str
    last_active: str | None
    transactions: list[ExplorerAddressTxRow]