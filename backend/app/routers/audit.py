from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from backend.app.core.database import get_db
from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.utils.utilities import audit_service,  AuditActions
from backend.app.core.security import require_permission, Permission


router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(
        user_id: Optional[int] = Query(None, description="Filter by user ID"),
        username: Optional[str] = Query(None, description="Filter by username"),
        action: Optional[str] = Query(None, description="Filter by action"),
        resource_type: Optional[str] = Query(None, description="Filter by resource type"),
        resource_id: Optional[int] = Query(None, description="Filter by resource ID"),
        start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime] = Query(None, description="End date for filtering"),
        limit: int = Query(100, le=5000, description="Maximum number of logs to return"),
        offset: int = Query(0, ge=0, description="Number of logs to skip"),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Get audit logs with comprehensive filtering (admin only)"""
    logs = audit_service.get_audit_logs(
        db=db,
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return logs


@router.get("/logs/user/{user_id}", response_model=List[schemas.AuditLogResponse])
def get_user_audit_logs(
        user_id: int,
        limit: int = Query(100, le=1000),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.USER_MANAGE))
):
    """Get audit logs for a specific user (admin/reviewer only)"""
    logs = audit_service.get_audit_logs(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return logs


@router.get("/stats")
def get_audit_stats(
        days: int = Query(30, ge=1, le=365, description="Number of days to include in stats"),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Get audit statistics for dashboard (admin only)"""
    stats = audit_service.get_audit_stats(db, days)
    return stats


@router.get("/actions")
def get_available_actions():
    """Get list of available audit actions"""
    actions = [action for action in dir(AuditActions) if not action.startswith('_')]
    return {"available_actions": actions}


@router.delete("/cleanup")
def cleanup_audit_logs(
        days_to_keep: int = Query(365, ge=30, le=1095, description="Keep logs from last N days"),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Clean up old audit logs (admin only)"""
    deleted_count = audit_service.cleanup_old_logs(db, days_to_keep)
    return {
        "message": f"Cleaned up {deleted_count} audit logs older than {days_to_keep} days",
        "deleted_count": deleted_count
    }


@router.get("/search")
def search_audit_logs(
        q: str = Query(..., description="Search term for username, action, or details"),
        limit: int = Query(50, le=200),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Search audit logs by various fields"""
    # This would need a more sophisticated search implementation
    # For now, we'll search in username and action fields
    from sqlalchemy import or_

    logs = db.query(models.AuditLog).filter(
        or_(
            models.AuditLog.username.ilike(f"%{q}%"),
            models.AuditLog.action.ilike(f"%{q}%"),
            models.AuditLog.resource_type.ilike(f"%{q}%")
        )
    ).order_by(models.AuditLog.created_at.desc()).limit(limit).all()

    return logs