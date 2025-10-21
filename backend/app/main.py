from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
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



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Engineering Report Deck API...")

    # ✅ Run debug first to check and fix existing admin
    debug_admin_creation()

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


    yield


    logger.info("Shutting down Engineering Report Deck API...")




app = FastAPI(
    title="Engineering Report Deck API",
    description="Backend API for Engineering Report Deck Application",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
lifespan=lifespan,
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


def debug_admin_creation():
    """Debug function to check admin creation variables"""
    from backend.app.core.database import SessionLocal
    from backend.app.models import models

    db = SessionLocal()
    try:
        logger.info("🔍 DEBUG: Checking admin creation variables...")
        logger.info(f"🔍 DEBUG: ADMIN_USERNAME = {settings.ADMIN_USERNAME}")
        logger.info(f"🔍 DEBUG: ADMIN_FULL_NAME = '{settings.ADMIN_FULL_NAME}'")
        logger.info(f"🔍 DEBUG: ADMIN_EMAIL = {settings.ADMIN_EMAIL}")

        # Check if admin exists and what their full_name is
        admin_user = db.query(models.User).filter(models.User.username == settings.ADMIN_USERNAME).first()
        if admin_user:
            logger.info(f"🔍 DEBUG: Existing admin user found!")
            logger.info(f"🔍 DEBUG: Current full_name = '{admin_user.full_name}'")
            logger.info(f"🔍 DEBUG: Current email = '{admin_user.email}'")
            logger.info(f"🔍 DEBUG: Current role = '{admin_user.role}'")

            # ✅ FIX: Update the existing admin's full_name if it's None
            if admin_user.full_name is None:
                logger.info("🔧 FIX: Updating admin user with missing full_name...")
                admin_user.full_name = settings.ADMIN_FULL_NAME
                db.commit()
                logger.info(f"🔧 FIX: Updated admin full_name to '{settings.ADMIN_FULL_NAME}'")
        else:
            logger.info("🔍 DEBUG: No admin user found - will create new one")

    except Exception as e:
        logger.error(f"🔍 DEBUG: Error in debug function: {e}")
        db.rollback()
    finally:
        db.close()


def create_admin_user():
    from backend.app.core.database import SessionLocal
    from backend.app.models import models
    from backend.app.utils.utilities import hash_password

    db = SessionLocal()
    try:
        admin_username = settings.ADMIN_USERNAME
        admin_full_name = settings.ADMIN_FULL_NAME
        admin_password = settings.ADMIN_PASSWORD
        admin_email = settings.ADMIN_EMAIL

        if admin_username and admin_password:
            existing_admin = db.query(models.User).filter(models.User.username == admin_username).first()
            if not existing_admin:
                admin_user = models.User(
                    username=admin_username,
                    full_name=admin_full_name,
                    email=admin_email,
                    hashed_password=hash_password(admin_password),
                    role="admin",
                    is_verified=True
                )
                db.add(admin_user)
                db.commit()
                logger.info(f"✅ Admin user '{admin_username}' created with full_name: '{admin_full_name}'")
            else:
                # ✅ FIX: Update existing admin if full_name is missing
                if existing_admin.full_name is None:
                    existing_admin.full_name = admin_full_name
                    db.commit()
                    logger.info(f"🔧 Updated existing admin user with full_name: '{admin_full_name}'")
                else:
                    logger.info(
                        f"ℹ️ Admin user '{admin_username}' already exists with full_name: '{existing_admin.full_name}'")
    except Exception as e:
        logger.error(f"❌ Admin user creation failed: {e}")
        db.rollback()
    finally:
        db.close()







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
        "timestamp": datetime.now(UTC).isoformat(),
        "services": services,
        "version": "1.0.0"
    }


#################TEMPORARY DEBUG CODE##################
@app.get("/debug/users")
def debug_users(db: Session = Depends(get_db)):
    """Debug endpoint to check all users and their roles"""
    from backend.app.crud import crud
    success, users = crud.get_all_users(db)
    if success:
        return {"users": users}
    return {"users": []}


@app.get("/debug/user/{email}")
def debug_user(email: str, db: Session = Depends(get_db)):
    """Debug endpoint to check user password hash"""
    from backend.app.models import models
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "hashed_password_length": len(user.hashed_password),
            "verification_token": user.verification_token,
            "is_active": user.is_active
        }
    return {"error": "User not found"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)