import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi import Request
import json
from typing import Optional, Dict, Any

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
    ):
        """Log an action to the audit trail"""
        from backend.models import AuditLog  # Import here to avoid circular imports

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

        db.add(audit_log)
        db.commit()

        return audit_log

    @staticmethod
    def get_audit_logs(
            db: Session,
            user_id: Optional[int] = None,
            action: Optional[str] = None,
            resource_type: Optional[str] = None,
            limit: int = 100,
            offset: int = 0
    ):
        """Retrieve audit logs with filtering"""
        from backend.models import AuditLog

        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)

        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()


# Common audit actions
class AuditActions:
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

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


# Global audit service instance
audit_service = AuditService()