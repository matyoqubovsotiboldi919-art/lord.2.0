from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from src.core.logging import setup_logging
from src.core.config import settings
from src.db.base import Base
from src.db.session import engine, SessionLocal
from src.models.user import User
from src.services.security import hash_password
from src.routers import auth, users, transactions, admin, explorer, market, websocket
from src.services.market import ensure_market_running, stop_market

setup_logging()

app = FastAPI(title="LORD 2.0", version="2.0.0")


def _parse_origins(raw: str):
    raw = (raw or "").strip()
    if raw == "*" or raw == "":
        return ["*"]
    return [x.strip() for x in raw.split(",") if x.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(settings.ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB tables
Base.metadata.create_all(bind=engine)


def seed_admin_user():
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not existing:
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                email="admin@lord.local",
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
                is_active=True,
                balance=0,
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
async def on_startup():
    seed_admin_user()
    await ensure_market_running()


@app.on_event("shutdown")
async def on_shutdown():
    await stop_market()


@app.get("/health")
def health():
    return {"ok": True, "service": "lord-2.0"}


# Routers
app.include_router(auth)
app.include_router(users)
app.include_router(transactions)
app.include_router(admin)
app.include_router(explorer)
app.include_router(market)
app.include_router(websocket)  # websocket endpoints

# ---- Frontend mount (/ui) ----
# IMPORTANT: resolve path safely
frontend_path = (Path(__file__).parent / settings.FRONTEND_DIR).resolve()

if frontend_path.exists():
    app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="ui")
else:
    # If not found, still keep backend running; UI can be hosted separately
    pass


# Redirect root to /ui
from fastapi.responses import RedirectResponse

@app.get("/")
def root():
    return RedirectResponse(url="/ui/")