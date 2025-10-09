from fastapi import FastAPI
import os  # ✅ Add this import
from backend.database import engine, Base
from backend.routers import reports, users, auth, admin, profile, stats, audit, review

app = FastAPI()

# Include all routers
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(profile.router)
app.include_router(stats.router)
app.include_router(audit.router)
app.include_router(review.router)

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# DB init
Base.metadata.create_all(bind=engine)


# ✅ Fix the admin creation function
def create_admin_user():
    import os  # ✅ Import os here too
    from backend.database import SessionLocal
    from backend import models
    from backend.utils import hash_password

    db = SessionLocal()
    try:
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")
        admin_email = os.getenv("ADMIN_EMAIL")

        if admin_username and admin_password:
            existing_admin = db.query(models.User).filter(models.User.username == admin_username).first()
            if not existing_admin:
                admin_user = models.User(
                    username=admin_username,
                    email=admin_email,
                    hashed_password=hash_password(admin_password),
                    role="admin",
                    is_verified=True
                )
                db.add(admin_user)
                db.commit()
                print(f"✅ Admin user '{admin_username}' created automatically")
            else:
                print(f"ℹ️ Admin user '{admin_username}' already exists")
    except Exception as e:
        print(f"⚠️ Admin creation skipped: {e}")
    finally:
        db.close()


# Call this after database initialization
create_admin_user()  # ✅ This will now work


@app.get("/")
def root():
    return {"message": "Backend is running 🚀"}
