import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

from fastapi import WebSocket

# --- Candlestick data structure ---
@dataclass
class Candle:
    t: int      # bucket start epoch seconds
    o: float
    h: float
    l: float
    c: float
    v: float


def _bucket_start(ts: float, tf_sec: int) -> int:
    x = int(ts)
    return x - (x % tf_sec)


@dataclass
class MarketState:
    symbol: str = "LORDUSDT"
    price: float = 100.0
    tf_sec: int = 60           # 1m candles
    max_candles: int = 500
    candles: List[Candle] = field(default_factory=list)

    clients: Set[WebSocket] = field(default_factory=set)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    running: bool = False
    task: Optional[asyncio.Task] = None

    def snapshot(self) -> Dict:
        return {
            "symbol": self.symbol,
            "price": round(self.price, 6),
            "tf_sec": self.tf_sec,
            "candles": [c.__dict__ for c in self.candles[-200:]],
        }


market = MarketState()


def _update_candles(state: MarketState, ts: float, new_price: float, volume: float) -> None:
    b = _bucket_start(ts, state.tf_sec)
    if not state.candles or state.candles[-1].t != b:
        # new candle
        c = Candle(t=b, o=new_price, h=new_price, l=new_price, c=new_price, v=volume)
        state.candles.append(c)
        if len(state.candles) > state.max_candles:
            state.candles = state.candles[-state.max_candles:]
        return

    c = state.candles[-1]
    c.c = new_price
    c.h = max(c.h, new_price)
    c.l = min(c.l, new_price)
    c.v = c.v + volume


async def _broadcast(payload: Dict) -> None:
    # Best effort broadcast; remove dead clients
    dead = []
    for ws in list(market.clients):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            market.clients.remove(ws)
        except Exception:
            pass


async def price_loop() -> None:
    """
    Real-time price simulation + candle building.
    Replace later with real exchange feed if needed.
    """
    market.running = True
    # seed first candle
    _update_candles(market, time.time(), market.price, 0.0)

    while market.running:
        await asyncio.sleep(1.0)

        # random walk
        drift = random.uniform(-0.6, 0.6)
        market.price = max(0.1, market.price + drift)
        vol = abs(drift) * random.uniform(5, 25)

        ts = time.time()
        _update_candles(market, ts, market.price, vol)

        await _broadcast({
            "type": "tick",
            "symbol": market.symbol,
            "ts": int(ts * 1000),
            "price": round(market.price, 6),
            "last_candle": market.candles[-1].__dict__,
        })


async def ensure_market_running() -> None:
    if market.task and not market.task.done():
        return
    market.task = asyncio.create_task(price_loop())


async def stop_market() -> None:
    market.running = False
    if market.task:
        try:
            await asyncio.wait_for(market.task, timeout=2.0)
        except Exception:
            pass