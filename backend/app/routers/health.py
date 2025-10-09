from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
import psutil


router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    # Database health
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # System metrics
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "memory_usage": f"{memory.percent}%",
            "disk_usage": f"{disk.percent}%"
        },
        "version": "1.0.0"
    }