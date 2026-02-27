# backend/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.db.session import SessionLocal
from src.models.user import User  # sizda User modeli bor deb hisoblayman
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


def seed_admin_user() -> None:
    """
    Admin user seed:
    - ADMIN_PASSWORD yo‘q bo‘lsa: seed qilmaydi (server yiqilmaydi)
    - ADMIN_PASSWORD 72 bytesdan uzun bo‘lsa: seed qilmaydi (server yiqilmaydi)
    """
    admin_email = getattr(settings, "ADMIN_EMAIL", "admin@lord.local")
    admin_password = getattr(settings, "ADMIN_PASSWORD", None)

    if not admin_password:
        print("[startup] ADMIN_PASSWORD not set -> skip admin seeding")
        return

    # bcrypt 72 bytes limit: ASCII ishlatsak 1 char ~ 1 byte
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
        print(f"[startup] Admin seed failed: {e}")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    seed_admin_user()


# Routers
app.include_router(auth, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users, prefix="/api/v1/users", tags=["users"])
app.include_router(transactions, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(admin, prefix="/api/v1/admin", tags=["admin"])
app.include_router(explorer, prefix="/api/v1/explorer", tags=["explorer"])
app.include_router(market, prefix="/api/v1/market", tags=["market"])
app.include_router(websocket, prefix="/api/v1/ws", tags=["websocket"])