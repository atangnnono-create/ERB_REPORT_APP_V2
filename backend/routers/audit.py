from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend import models, schemas
from backend.utils import audit_service, AuditActions
from backend.security import require_permission, Permission

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(
        user_id: Optional[int] = Query(None, description="Filter by user ID"),
        action: Optional[str] = Query(None, description="Filter by action"),
        resource_type: Optional[str] = Query(None, description="Filter by resource type"),
        limit: int = Query(100, le=1000),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Get audit logs (admin only)"""
    logs = audit_service.get_audit_logs(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
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


@router.get("/logs/stats")
def get_audit_stats(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Get audit statistics (admin only)"""
    from sqlalchemy import func
    from backend.models import AuditLog

    # Total logs
    total_logs = db.query(func.count(AuditLog.id)).scalar()

    # Logs by action type
    actions_count = db.query(
        AuditLog.action,
        func.count(AuditLog.id)
    ).group_by(AuditLog.action).all()

    # Recent activity (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.now() - timedelta(days=1)
    recent_logs = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= yesterday
    ).scalar()

    return {
        "total_logs": total_logs,
        "recent_activity_24h": recent_logs,
        "actions_breakdown": dict(actions_count)
    }