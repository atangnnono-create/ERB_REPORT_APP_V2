import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from fastapi import Request
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from backend.app.core.exceptions import logger
from backend.app.models.models import AuditLog

load_dotenv()  # Load .env in dev

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # ✅ Consistent timeout

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ✅ AUDIT LOGGING SERVICE
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
    ) -> AuditLog:
        """
        Log an action to the audit trail with enhanced information
        """
        # Get request information if available
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
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
            raise

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
        """Retrieve audit logs with comprehensive filtering"""
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

    @staticmethod
    def get_audit_stats(
            db: Session,
            days: int = 30
    ) -> Dict[str, Any]:
        """Get audit statistics for dashboard"""
        since_date = datetime.now() - timedelta(days=days)

        # Total logs
        total_logs = db.query(func.count(AuditLog.id)).scalar()

        # Recent logs (last N days)
        recent_logs = db.query(func.count(AuditLog.id)).filter(
            AuditLog.created_at >= since_date
        ).scalar()

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
            date = datetime.now() - timedelta(days=6 - i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

            daily_count = db.query(func.count(AuditLog.id)).filter(
                AuditLog.created_at >= date_start,
                AuditLog.created_at <= date_end
            ).scalar()

            timeline_data.append({
                "date": date_start.date().isoformat(),
                "count": daily_count or 0
            })

        return {
            "total_logs": total_logs,
            "recent_logs": recent_logs,
            "period_days": days,
            "actions_breakdown": dict(actions_count),
            "top_users": dict(top_users),
            "timeline": timeline_data
        }

    @staticmethod
    def cleanup_old_logs(db: Session, days_to_keep: int = 365) -> int:
        """Clean up audit logs older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        try:
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


# Global audit service instance
audit_service = AuditService()