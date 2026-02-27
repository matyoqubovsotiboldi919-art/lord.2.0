# backend/src/main.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.session import SessionLocal
from src.models.user import User
from src.services.security import hash_password

from src.routers import auth, users, transactions, admin, explorer, market, websocket


app = FastAPI(title="LORD 2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    # Render healthcheck uchun: endi / 404 bo'lmaydi
    return {"status": "ok", "service": "LORD 2.0"}


def seed_admin_user() -> None:
    """
    MUHIM:
    - Admin seed DEFAULT O'CHIQ (ADMIN_SEED_ENABLED=1 bo'lmasa umuman seed qilmaydi)
    - Shuning uchun deploy hech qachon seed sababli yiqilmaydi.
    """
    if os.getenv("ADMIN_SEED_ENABLED", "0") != "1":
        print("[startup] ADMIN_SEED_ENABLED!=1 -> skip admin seeding")
        return

    admin_email = os.getenv("ADMIN_EMAIL", "admin@lord.local")
    admin_password = os.getenv("ADMIN_PASSWORD", "")

    if not admin_password:
        print("[startup] ADMIN_PASSWORD not set -> skip admin seeding")
        return

    # bcrypt limit: 72 bytes
    if len(admin_password.encode("utf-8")) > 72:
        print("[startup] ADMIN_PASSWORD too long (>72 bytes) -> skip admin seeding")
        return

    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == admin_email).first()
        if exists:
            print("[startup] Admin already exists -> skip seeding")
            return

        u = User(
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
        # Hech qachon appni yiqitmaymiz:
        print(f"[startup] Admin seed failed (non-fatal): {e}")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    seed_admin_user()


# Routers (prefixlar routerlar ichida bo'lsa, bu yerda bermaymiz)
app.include_router(auth)
app.include_router(users)
app.include_router(transactions)
app.include_router(admin)
app.include_router(explorer)
app.include_router(market)
app.include_router(websocket)