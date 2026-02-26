from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.services.market import market, ensure_market_running

router = APIRouter()


@router.websocket("/ws/market")
async def ws_market(ws: WebSocket):
    await ws.accept()
    await ensure_market_running()

    market.clients.add(ws)
    try:
        # first snapshot
        await ws.send_json({"type": "snapshot", **market.snapshot()})
        while True:
            # keep alive / client messages ignored
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            market.clients.remove(ws)
        except Exception:
            pass