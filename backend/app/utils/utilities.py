import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from fastapi import Request
from sqlalchemy import func, desc
from datetime import datetime, timedelta, UTC
from backend.app.core.exceptions import logger
from backend.app.models.models import AuditLog
from backend.app.core.config import settings  # ✅ Use centralized settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ✅ Secure configuration with production validation
def get_secret_key() -> str:
    """Get secret key with production validation"""
    key = settings.SECRET_KEY
    if not key or key == "dev-key-change-in-production":
        if settings.ENVIRONMENT == "production":
            raise ValueError("SECRET_KEY must be set in production environment")
        logger.warning("⚠️ Using default secret key - not suitable for production")
    return key


def get_algorithm() -> str:
    """Get JWT algorithm"""
    return settings.ALGORITHM


def get_token_expiry() -> int:
    """Get token expiry minutes"""
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """Create secure password hash"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token with UTC expiration"""
    to_encode = data.copy()
    # ✅ Use UTC for consistency across environments
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=get_token_expiry()))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_secret_key(), algorithm=get_algorithm())


def decode_access_token(token: str) -> dict | None:
    """Decode JWT token with error handling"""
    try:
        return jwt.decode(token, get_secret_key(), algorithms=[get_algorithm()])
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


# ✅ Enhanced AUDIT LOGGING SERVICE
class AuditService:
    @staticmethod
    def log_action(
            db: Session,
            action: str,
            user_id: Optional[int] = None,
            username: Optional[str] = None,
            resource_type: Optional[str] = None,
            resource_id: Optional[int] = None,
            details: Optional[Dict[str, Any]] = None,
            request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """
        Log an action to the audit trail with enhanced information
        Returns None if logging fails (doesn't break application)
        """
        # ✅ Enhanced IP detection for proxies and cloud environments
        ip_address = None
        user_agent = None

        if request:
            # Get IP from common headers (useful behind proxies like Render, Nginx, etc.)
            ip_address = (
                    request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
                    request.headers.get("x-real-ip") or
                    (request.client.host if request.client else None)
            )
            user_agent = request.headers.get("user-agent")

        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

        try:
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            logger.info(f"Audit log created: {action} by {username or 'system'}")
            return audit_log
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit failures shouldn't break the application
            return None

    @staticmethod
    def get_audit_logs(
            db: Session,
            user_id: Optional[int] = None,
            username: Optional[str] = None,
            action: Optional[str] = None,
            resource_type: Optional[str] = None,
            resource_id: Optional[int] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            limit: int = 100,
            offset: int = 0
    ) -> List[AuditLog]:
        """Retrieve audit logs with comprehensive filtering and error handling"""
        try:
            query = db.query(AuditLog)

            # Apply filters
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if username:
                query = query.filter(AuditLog.username.ilike(f"%{username}%"))
            if action:
                query = query.filter(AuditLog.action == action)
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            if resource_id:
                query = query.filter(AuditLog.resource_id == resource_id)
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)

            return query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []

    @staticmethod
    def get_audit_stats(
            db: Session,
            days: int = 30
    ) -> Dict[str, Any]:
        """Get audit statistics for dashboard with error handling"""
        try:
            since_date = datetime.now(UTC) - timedelta(days=days)

            # Total logs
            total_logs = db.query(func.count(AuditLog.id)).scalar() or 0

            # Recent logs (last N days)
            recent_logs = db.query(func.count(AuditLog.id)).filter(
                AuditLog.created_at >= since_date
            ).scalar() or 0

            # Logs by action type
            actions_count = db.query(
                AuditLog.action,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.created_at >= since_date
            ).group_by(AuditLog.action).all()

            # Logs by user
            top_users = db.query(
                AuditLog.username,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.username.isnot(None),
                AuditLog.created_at >= since_date
            ).group_by(AuditLog.username).order_by(desc(func.count(AuditLog.id))).limit(10).all()

            # Recent activity timeline (last 7 days)
            timeline_data = []
            for i in range(7):
                date = datetime.now(UTC) - timedelta(days=6 - i)
                date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

                daily_count = db.query(func.count(AuditLog.id)).filter(
                    AuditLog.created_at >= date_start,
                    AuditLog.created_at <= date_end
                ).scalar() or 0

                timeline_data.append({
                    "date": date_start.date().isoformat(),
                    "count": daily_count
                })

            return {
                "total_logs": total_logs,
                "recent_logs": recent_logs,
                "period_days": days,
                "actions_breakdown": dict(actions_count),
                "top_users": dict(top_users),
                "timeline": timeline_data
            }
        except Exception as e:
            logger.error(f"Error getting audit stats: {e}")
            return {
                "total_logs": 0,
                "recent_logs": 0,
                "period_days": days,
                "actions_breakdown": {},
                "top_users": {},
                "timeline": []
            }

    @staticmethod
    def cleanup_old_logs(db: Session, days_to_keep: int = 365) -> int:
        """Clean up audit logs older than specified days with error handling"""
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)

            # Count logs to be deleted
            count = db.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date
            ).count()

            # Delete old logs
            db.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date
            ).delete()

            db.commit()
            logger.info(f"Cleaned up {count} audit logs older than {days_to_keep} days")
            return count

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup audit logs: {e}")
            return 0


# Common audit actions
class AuditActions:
    USER_REGISTER = "user_register"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_VERIFY_EMAIL = "user_verify_email"
    USER_RESEND_VERIFICATION = "user_resend_verification"

    REPORT_CREATE = "report_create"
    REPORT_UPDATE = "report_update"
    REPORT_DELETE = "report_delete"
    REPORT_SUBMIT = "report_submit"
    REPORT_REVIEW = "report_review"
    REPORT_APPROVE = "report_approve"
    REPORT_REJECT = "report_reject"

    EMAIL_VERIFICATION_SENT = "email_verification_sent"
    EMAIL_VERIFIED = "email_verified"

    ADMIN_USER_ROLE_UPDATE = "admin_user_role_update"
    ADMIN_USER_STATUS_UPDATE = "admin_user_status_update"
    ADMIN_VIEW_ALL_USERS = "admin_view_all_users"
    ADMIN_VIEW_ALL_REPORTS = "admin_view_all_reports"

    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    PASSWORD_CHANGE = "password_change"


    __all__ = [
        'hash_password',
        'verify_password',
        'create_access_token',
        'decode_access_token',
        'get_secret_key',
        'get_algorithm',
        'get_token_expiry',
        'AuditService',
        'AuditActions',
        'audit_service'
    ]


# Global audit service instance
audit_service = AuditService()