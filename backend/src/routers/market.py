from fastapi import APIRouter
from src.schemas.market import MarketSnapshotOut
from src.services.market import market, ensure_market_running

router = APIRouter(prefix="/api/v1/market", tags=["market"])


@router.get("/snapshot", response_model=MarketSnapshotOut)
async def snapshot():
    await ensure_market_running()
    return market.snapshot()