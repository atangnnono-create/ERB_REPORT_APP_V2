from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.crud import crud
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets
from backend.app.core import security
from backend.app.core.database import get_db
from backend.app.services.email_service import email_service
from backend.app.utils.utilities import (audit_service, AuditActions, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, verify_password)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ✅ Enhanced token generation with expiration
def generate_verification_token():
    return secrets.token_urlsafe(32)


def is_token_expired(expires_at: datetime) -> bool:
    return datetime.now() > expires_at


@router.post("/register", response_model=schemas.UserResponse)
def register(
        user: schemas.UserCreate,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db)
):
    # Check if username or email exists
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    db_user = crud.create_user(db, user)

    # ✅ Generate verification token with expiration (24 hours)
    verification_token = generate_verification_token()
    token_expires = datetime.now() + timedelta(hours=24)

    # Store verification data
    db_user.verification_token = verification_token
    db_user.verification_token_expires = token_expires
    db_user.verification_sent_at = datetime.now()
    db.commit()
    db.refresh(db_user)

    # ✅ Send verification email in background
    background_tasks.add_task(
        email_service.send_verification_email,
        db_user.email,
        verification_token,
        db_user.username
    )

    # ✅ Log the registration
    audit_service.log_action(
        db=db,
        action=AuditActions.USER_REGISTER,
        user_id=db_user.id,
        username=db_user.username,
        resource_type="user",
        resource_id=db_user.id,
        details={"email": db_user.email, "role": db_user.role},
        request=request
    )

    return db_user


from pydantic import BaseModel
class VerifyEmailRequest(BaseModel):
    token: str
@router.post("/verify-email")
def verify_email(verify_request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify user's email address with token validation"""

    token = verify_request.token
    print(f"=== DEBUG: Received token: {token} ===")
    print(f"=== DEBUG: Token length: {len(token)} ===")

    # Check if any users have verification tokens
    all_users_with_tokens = db.query(models.User).filter(models.User.verification_token.isnot(None)).all()
    print(f"=== DEBUG: Users with tokens: {len(all_users_with_tokens)} ===")

    for user in all_users_with_tokens:
        print(f"=== DEBUG: User: {user.username}, Token: {user.verification_token} ===")
        if user.verification_token == token:
            print(f"=== DEBUG: TOKEN MATCH FOUND! ===")

    user = db.query(models.User).filter(models.User.verification_token == token).first()

    if not user:
        print("=== DEBUG: No user found with this token ===")
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token. Please request a new verification email."
        )

    print(f"=== DEBUG: Found user: {user.username} ===")

    # Check if token is expired
    if user.verification_token_expires and is_token_expired(user.verification_token_expires):
        print("=== DEBUG: Token expired ===")
        user.verification_token = None
        user.verification_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="Verification token has expired. Please request a new verification email."
        )

    # Mark user as verified
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    print("=== DEBUG: Email verified successfully ===")

    return {
        "message": "Email verified successfully! You can now login and access all features.",
        "username": user.username,
        "email": user.email
    }

@router.post("/resend-verification")
def resend_verification(
        email: str,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """Resend verification email with new token"""
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")

    # ✅ Generate new token with expiration
    new_token = generate_verification_token()
    token_expires = datetime.now() + timedelta(hours=24)

    user.verification_token = new_token
    user.verification_token_expires = token_expires
    user.verification_sent_at = datetime.now()
    db.commit()

    # ✅ Resend verification email
    background_tasks.add_task(
        email_service.send_verification_email,
        user.email,
        new_token,
        user.username
    )

    # ✅ Log the resend action
    audit_service.log_action(
        db=db,
        action=AuditActions.EMAIL_VERIFICATION_SENT,
        user_id=user.id,
        username=user.username,
        resource_type="user",
        resource_id=user.id,
        details={"resend": True}
    )

    return {
        "message": "Verification email sent! Please check your inbox.",
        "email": user.email
    }


@router.get("/verification-status/{email}")
def get_verification_status(email: str, db: Session = Depends(get_db)):
    """Check verification status of a user"""
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user.email,
        "is_verified": user.is_verified,
        "verification_sent_at": user.verification_sent_at,
        "can_resend": user.verification_sent_at is None or
                      (datetime.now() - user.verification_sent_at) > timedelta(minutes=5)
    }
@router.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, form_data.username)
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

        # ✅ Log the login
    audit_service.log_action(
        db=db,
        action=AuditActions.USER_LOGIN,
        user_id=db_user.id,
        username=db_user.username,
        request=request
    )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register/{role}", response_model=schemas.UserResponse)
def register_with_role(
    role: schemas.UserRole,
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_permission(security.Permission.USER_MANAGE))
):
    print(f"Admin {current_user.username} is creating user {user.username} with role {role}")
    """Admin-only endpoint to register users with specific roles"""
    user_data = user.model_dump()
    user_data["role"] = role
    return crud.create_user(db, schemas.UserCreate(**user_data))