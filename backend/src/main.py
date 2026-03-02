@app.on_event("startup")
def startup():
    if settings.ADMIN_SEED_ENABLED and settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
        db: Session = SessionLocal()
        try:
            existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()

            if existing:
                # 🔥 BOR BO'LSA HAM PAROLNI YANGILAYMIZ
                existing.password_hash = hash_password(settings.ADMIN_PASSWORD)
                existing.role = "ADMIN"
                existing.status = "ACTIVE"
                db.commit()
                print("[startup] Admin updated (password synced)")
                return

            # Agar umuman yo'q bo'lsa — yaratamiz
            u = User(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                public_id="TEMP",
                address="TEMP",
                role="ADMIN",
                status="ACTIVE",
            )
            db.add(u)
            db.flush()

            for _ in range(10):
                pid = new_public_id()
                if not db.query(User).filter(User.public_id == pid).first():
                    u.public_id = pid
                    break

            u.address = hmac_address(u.id)

            db.commit()
            print("[startup] Admin created")

        finally:
            db.close()