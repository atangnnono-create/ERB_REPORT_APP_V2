from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from datetime import datetime
from requests import Session

from backend.app.core.cache import cache_service
# Import from new core structure
from backend.app.core.config import settings
from backend.app.core.database import init_db, check_database_health, get_db, Base
from backend.app.core.loggings import setup_logging
from backend.app.core.exceptions import global_exception_handler
from backend.app.routers import users, auth, admin, profile, stats, review, health
from backend.app.routers import audit, reports
from backend.app.routers import password_reset
from backend.app.core.exceptions import global_exception_handler, AppException



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Engineering Report Deck API",
    description="Backend API for Engineering Report Deck Application",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)



# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(profile.router, prefix="/api/v1", tags=["profile"])
app.include_router(stats.router, prefix="/api/v1", tags=["statistics"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
app.include_router(review.router, prefix="/api/v1", tags=["review"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(password_reset.router, prefix="/api/v1", tags=["Password Reset"])


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Starting Engineering Report Deck API...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    # Create admin user
    try:
        create_admin_user()
    except Exception as e:
        logger.warning(f"Admin user creation failed: {e}")

    # Check database health
    if check_database_health():
        logger.info("✅ Database health check passed")
    else:
        logger.error("❌ Database health check failed")

    # Check cache health
    if hasattr(cache_service, 'health_check') and cache_service.health_check():
        logger.info("✅ Cache health check passed")
    else:
        logger.warning("⚠️ Cache health check failed or not configured")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Engineering Report Deck API...")


@app.get("/")
async def root():
    return {"message": "Engineering Report Deck API is running 🚀", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    db_health = check_database_health()
    cache_health = cache_service.health_check() if hasattr(cache_service, 'health_check') else False

    services = {
        "database": "healthy" if db_health else "unhealthy",
        "cache": "healthy" if cache_health else "unhealthy",
    }

    overall_health = "healthy" if all([db_health, cache_health]) else "degraded"

    return {
        "status": overall_health,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services,
        "version": "1.0.0"
    }


# ✅ Admin creation function
def create_admin_user():
    import os
    from backend.app.core.database import SessionLocal
    from backend.app.models import models
    from backend.app.utils.utilities import hash_password
    from dotenv import load_dotenv

    load_dotenv()

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
                logger.info(f"✅ Admin user '{admin_username}' created automatically")
            else:
                logger.info(f"ℹ️ Admin user '{admin_username}' already exists")
    except Exception as e:
        logger.warning(f"⚠️ Admin creation skipped: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

#################TEMPORARY DEBUG CODE##################
# Add this temporary debug endpoint to backend/main.py
@app.get("/debug/users")
def debug_users(db: Session = Depends(get_db)):
    """Debug endpoint to check all users and their roles"""
    from backend.app.crud import crud
    success, users = crud.get_all_users(db)
    if success:
        return {"users": users}
    return {"users": []}