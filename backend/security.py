from enum import Enum
from fastapi import HTTPException, status, Depends
from backend import models
from backend.auth import get_current_user


class Permission(str, Enum):
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_MANAGE = "user:manage"

    # Report permissions
    REPORT_READ = "report:read"
    REPORT_WRITE = "report:write"
    REPORT_REVIEW = "report:review"
    REPORT_MANAGE = "report:manage"

    # System permissions
    SYSTEM_ADMIN = "system:admin"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    "admin": {  Permission.SYSTEM_ADMIN,
                Permission.USER_MANAGE,
                Permission.REPORT_MANAGE
              },
    "reviewer": {
        Permission.USER_READ,
        Permission.REPORT_READ,
        Permission.REPORT_REVIEW,
        Permission.REPORT_MANAGE
    },
    "engineer": {
        Permission.REPORT_READ,
        Permission.REPORT_WRITE,
    },
    "technologist": {
        Permission.REPORT_READ,
        Permission.REPORT_WRITE,
    },
    "technician": {
        Permission.REPORT_READ,
        Permission.REPORT_WRITE,
    },
    "candidate": {
        Permission.REPORT_READ,
    }
}


def has_permission(user: models.User, permission: Permission) -> bool:
    """Check if user has specific permission"""
    user_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return permission in user_permissions

def require_permission(permission: Permission):
    """Dependency to require specific permission"""
    def permission_dependency(current_user: models.User = Depends(get_current_user)):
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return permission_dependency


def require_active_user():
    """Dependency to require active account"""
    def active_user_dependency(current_user: models.User = Depends(get_current_user)):
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        return current_user
    return active_user_dependency