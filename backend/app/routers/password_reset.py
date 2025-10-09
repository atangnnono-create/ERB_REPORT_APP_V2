from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.app.core.database import get_db
from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.crud import crud
from backend.app.services.email_service import email_service
from backend.app.utils.utilities import audit_service, AuditActions, verify_password
from backend.app.core.security import require_active_user

router = APIRouter(prefix="/auth", tags=["Password Reset"])


@router.post("/forgot-password", response_model=schemas.PasswordResetResponse)
async def forgot_password(
        request: schemas.PasswordResetRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """Request password reset"""
    user = crud.get_user_by_email(db, request.email)

    # Always return success to prevent email enumeration
    if not user:
        return {
            "message": "If the email exists, a password reset link has been sent",
            "email": request.email
        }

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )

    # Generate reset token
    reset_token = crud.create_password_reset_token(db, user.id)

    # Send reset email in background
    background_tasks.add_task(
        email_service.send_password_reset_email,
        user.email,
        reset_token,
        user.username
    )

    # Log the action
    audit_service.log_action(
        db=db,
        action=AuditActions.PASSWORD_RESET_REQUEST,
        user_id=user.id,
        username=user.username,
        resource_type="user",
        resource_id=user.id
    )

    return {
        "message": "If the email exists, a password reset link has been sent",
        "email": request.email
    }


@router.post("/reset-password", response_model=schemas.PasswordResetResponse)
async def reset_password(
        reset_data: schemas.PasswordResetConfirm,
        db: Session = Depends(get_db)
):
    """Reset password with token"""
    user = crud.get_user_by_reset_token(db, reset_data.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Update password
    success = crud.update_user_password(db, user.id, reset_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

    # Log the action
    audit_service.log_action(
        db=db,
        action=AuditActions.PASSWORD_RESET_COMPLETE,
        user_id=user.id,
        username=user.username,
        resource_type="user",
        resource_id=user.id
    )

    return {
        "message": "Password reset successfully",
        "email": user.email
    }


@router.post("/change-password", response_model=schemas.PasswordResetResponse)
async def change_password(
        password_data: schemas.PasswordChange,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_active_user)
):
    """Change password while logged in"""
    success = crud.change_user_password(
        db,
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Log the action
    audit_service.log_action(
        db=db,
        action=AuditActions.PASSWORD_CHANGE,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=current_user.id
    )

    return {
        "message": "Password changed successfully",
        "email": current_user.email
    }


@router.get("/validate-reset-token")
async def validate_reset_token(
        token: str,
        db: Session = Depends(get_db)
):
    """Validate reset token without resetting password"""
    user = crud.get_user_by_reset_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return {"valid": True, "email": user.email}