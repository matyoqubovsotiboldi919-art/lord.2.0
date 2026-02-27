# backend/src/main.py
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.db.session import SessionLocal
from src.models.user import User
from src.services.security import hash_password

from src.routers import auth, users, transactions, admin, explorer, market, websocket


app = FastAPI(title="LORD 2.0")


# ✅ CORS (frontend boshqa domen bo'lsa ham ishlasin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ API health (frontendni / ga ulaganimiz uchun health alohida bo'ladi)
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "LORD 2.0"}


def seed_admin_user() -> None:
    """
    Admin seed:
    - Default OFF (ADMIN_SEED_ENABLED=1 bo'lmasa seed qilmaydi)
    - Hech qachon appni yiqitmaydi
    - users.username NOT NULL bo'lgani uchun ADMIN_USERNAME ham beradi
    """
    if os.getenv("ADMIN_SEED_ENABLED", "0") != "1":
        print("[startup] ADMIN_SEED_ENABLED!=1 -> skip admin seeding")
        return

    admin_email = os.getenv("ADMIN_EMAIL", "admin@lord.local").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip()

    if not admin_password:
        print("[startup] ADMIN_PASSWORD not set -> skip admin seeding")
        return

    # bcrypt limit: 72 bytes
    if len(admin_password.encode("utf-8")) > 72:
        print("[startup] ADMIN_PASSWORD too long (>72 bytes) -> skip admin seeding")
        return

    if not admin_username:
        admin_username = "admin"

    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == admin_email).first()
        if exists:
            print("[startup] Admin already exists -> skip seeding")
            return

        u = User(
            username=admin_username,
            email=admin_email,
            hashed_password=hash_password(admin_password),
            is_admin=True,
            is_active=True,
        )
        db.add(u)
        db.commit()
        print("[startup] Admin seeded successfully")
    except Exception as e:
        db.rollback()
        print(f"[startup] Admin seed failed (non-fatal): {e}")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    seed_admin_user()


# ✅ Routers
app.include_router(auth)
app.include_router(users)
app.include_router(transactions)
app.include_router(admin)
app.include_router(explorer)
app.include_router(market)
app.include_router(websocket)


# ✅ FRONTEND (LORD/frontend) ni / ga chiqaramiz
# /docs, /openapi.json, /api/... route'lar ishlayveradi
BASE_DIR = Path(__file__).resolve().parents[2]   # .../backend/src/main.py -> LORD/
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
    print(f"[startup] Frontend mounted from: {FRONTEND_DIR}")
else:
    print(f"[startup] Frontend folder not found: {FRONTEND_DIR}")