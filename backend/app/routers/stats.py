from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models import models
from backend.app.core.security import require_permission, Permission

router = APIRouter(prefix="/admin", tags=["Statistics"])


@router.get("/system-stats")
def get_system_stats(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Get system statistics"""

    # User statistics
    total_users = db.query(func.count(models.User.id)).scalar()
    verified_users = db.query(func.count(models.User.id)).filter(models.User.is_verified == True).scalar()
    active_users = db.query(func.count(models.User.id)).filter(models.User.is_active == True).scalar()

    # Report statistics
    total_reports = db.query(func.count(models.Report.id)).scalar()

    # Status breakdown
    status_counts = db.query(
        models.Report.status,
        func.count(models.Report.id)
    ).group_by(models.Report.status).all()

    status_breakdown = {status: count for status, count in status_counts}

    # Recent activity (last 7 days)
    # This would need a date filter in a real implementation

    return {
        "users": {
            "total": total_users,
            "verified": verified_users,
            "active": active_users,
            "verification_rate": round((verified_users / total_users * 100), 2) if total_users > 0 else 0
        },
        "reports": {
            "total": total_reports,
            "status_breakdown": status_breakdown
        },
        "system": {
            "database": "SQLite",
            "authentication": "JWT",
            "email_service": "Ethereal"
        }
    }