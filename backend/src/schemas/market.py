from pydantic import BaseModel
from typing import List


class CandleOut(BaseModel):
    t: int
    o: float
    h: float
    l: float
    c: float
    v: float


class MarketSnapshotOut(BaseModel):
    symbol: str
    price: float
    tf_sec: int
    candles: List[CandleOut]