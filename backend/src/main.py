from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .routers import auth, users, tx, explorer, admin
from .core.db import SessionLocal
from .models.user import User
from .services.security import hash_password
from .core.config import settings
from .services.hashers import new_public_id, hmac_address

app = FastAPI(title="LORD 2.0", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tx.router)
app.include_router(explorer.router)
app.include_router(admin.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.on_event("startup")
def startup():
    if settings.ADMIN_SEED_ENABLED and settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
        db: Session = SessionLocal()
        try:
            existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
            if existing:
                return

            u = User(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                public_id="TEMP",
                address="TEMP",
                role="ADMIN",
                status="ACTIVE",
            )
            db.add(u)
            db.flush()  # u.id

            # unique public_id retry
            for _ in range(10):
                pid = new_public_id()
                if not db.query(User).filter(User.public_id == pid).first():
                    u.public_id = pid
                    break

            u.address = hmac_address(u.id)

            db.commit()
        finally:
            db.close()