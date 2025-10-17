from datetime import datetime, timedelta
from typing import Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy.orm.strategy_options import joinedload

from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.core import loggings
from backend.app.services.auth import verify_password
from backend.app.utils.utilities import hash_password  # ✅ Import from utils instead of auth
from sqlalchemy.sql import func
import logging

from backend.app.core.exceptions import (
    raise_validation_error,
    raise_not_found,
    raise_business_rule,
    NotFoundException,
    BusinessRuleException
)


# Configure logging
loggings.setup_logging()
logger = logging.getLogger(__name__)

# -------- USERS --------
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise_not_found("User")
    return user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_all_users(db: Session) -> Tuple[bool, List[models.User]]:
    """Get all users with error handling"""
    try:
        users = db.query(models.User).all()
        return True, users
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return False, []


def create_user(db: Session, user: schemas.UserCreate):
    # Check if username exists
    if get_user_by_username(db, user.username):
        raise_business_rule("Username already registered", "USERNAME_EXISTS")

    # Check if email exists
    if get_user_by_email(db, user.email):
        raise_business_rule("Email already registered", "EMAIL_EXISTS")

    try:
        hashed_password = hash_password(user.password)
        db_user = models.User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=user.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)  # This will raise NotFoundException if user doesn't exist

    try:
        update_data = user_update.dict(exclude_unset=True)

        # ✅ NEW: Check for duplicate email (mirroring create_user pattern)
        if 'email' in update_data and update_data['email']:
            # Check if email is being changed to a different value
            if update_data['email'] != db_user.email:
                existing_user = get_user_by_email(db, update_data['email'])
                if existing_user:
                    raise_business_rule("Email already registered", "EMAIL_EXISTS")

        # Update fields
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    except BusinessRuleException:
        # Re-raise business rule exceptions (like duplicate email)
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user {user_id}: {e}")
        raise

# -------- REPORTS --------
def get_reports(db: Session, user_id: int):
    """Get user's reports with competencies eagerly loaded"""
    return db.query(models.Report).options(
        joinedload(models.Report.competencies),
        joinedload(models.Report.owner)
    ).filter(models.Report.owner_id == user_id).all()

def get_all_reports(db: Session):
    """Get ALL reports with competencies eagerly loaded"""
    return db.query(models.Report).options(
        joinedload(models.Report.competencies),
        joinedload(models.Report.owner)
    ).all()


def get_report(db: Session, report_id: int, user_id: int):
    report = db.query(models.Report).filter(
        models.Report.id == report_id,
        models.Report.owner_id == user_id
    ).first()

    if not report:
        raise_not_found("Report")
    return report

def delete_report(db: Session, report: models.Report):
    db.delete(report)
    db.commit()

def get_reports_with_competencies(db: Session, user_id: int):
    return db.query(models.Report).options(
        joinedload(models.Report.competencies)
    ).filter(models.Report.owner_id == user_id).all()

def get_report_with_competencies(db: Session, report_id: int, user_id: int):
    """Get single report with competencies eagerly loaded"""
    return db.query(models.Report).options(
        joinedload(models.Report.competencies)
    ).filter(
        models.Report.id == report_id,
        models.Report.owner_id == user_id
    ).first()

# -------- COMPETENCIES --------
def upsert_competency(db: Session, report_id: int, user_id: int, comp: schemas.CompetencyCreate):
    """
    Create or update a competency for a report.
    """
    existing = db.query(models.Competency).filter_by(
        competency_key=comp.competency_key,
        report_id=report_id,
        owner_id=user_id
    ).first()

    if existing:
        existing.competency_title = comp.competency_title
        existing.user_response = comp.user_response
    else:
        new_comp = models.Competency(
            competency_key=comp.competency_key,
            competency_title=comp.competency_title,
            user_response=comp.user_response,
            report_id=report_id,
            owner_id=user_id
        )
        db.add(new_comp)

def create_or_update_report(db: Session, report: schemas.ReportCreate, user_id: int):
    """
    Creates a new report or updates an existing one.
    All competencies are inserted or updated in the Competency table.
    """
    report_id = getattr(report, "id", None)
    db_report = None
    if report_id:
        db_report = db.query(models.Report).filter_by(id=report_id, owner_id=user_id).first()

    if not db_report:
        # CREATE new report
        db_report = models.Report(title=report.title, content=report.content, owner_id=user_id, status=report.status)
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
    else:
        # UPDATE existing report
        db_report.title = report.title
        db_report.content = report.content
        db_report.status = report.status
        db.commit()
        db.refresh(db_report)

    # UPSERT competencies
    for comp in report.competencies:
        upsert_competency(db, db_report.id, user_id, comp)

    db.commit()
    db.refresh(db_report)
    return db_report

def review_report(db: Session, report_id: int, review: schemas.ReportReview, reviewer_id: int):
    db_report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not db_report:
        return None

    db_report.status = review.status
    db_report.review_notes = review.review_notes

    # Only set reviewed_at and reviewed_by when review is completed (approved/rejected)
    if review.status in [schemas.ReportStatus.APPROVED, schemas.ReportStatus.REJECTED]:
        db_report.reviewed_at = func.now()
        db_report.reviewed_by = reviewer_id
    else:
        # For under_review status, clear these fields since review is not completed
        db_report.reviewed_at = None
        db_report.reviewed_by = None

    db.commit()
    db.refresh(db_report)
    return db_report

# ✅ New function to submit report for review
def submit_report(db: Session, report_id: int, user_id: int):
    db_report = db.query(models.Report).filter(
        models.Report.id == report_id,
        models.Report.owner_id == user_id
    ).first()

    if not db_report:
        return None

    db_report.status = schemas.ReportStatus.SUBMITTED
    db_report.submitted_at = func.now()

    db.commit()
    db.refresh(db_report)
    return db_report


def update_report(db: Session, db_report: models.Report, update: schemas.ReportCreate):
    """
    Overwrite report and upsert competencies.
    """
    db_report.title = update.title
    db_report.content = update.content
    db.commit()
    db.refresh(db_report)

    for comp in update.competencies:
        upsert_competency(db, db_report.id, db_report.owner_id, comp)

    db.commit()
    db.refresh(db_report)
    return db_report


# -------- PASSWORD RESET --------
def create_password_reset_token(db: Session, user_id: int) -> str:
    """Create password reset token for user"""
    import secrets
    token = secrets.token_urlsafe(32)

    # Store token in user record (you might want a separate table for production)
    user = get_user(db, user_id)
    if user:
        user.verification_token = token
        user.verification_token_expires = datetime.now() + timedelta(hours=24)
        db.commit()

    return token


def get_user_by_reset_token(db: Session, token: str):
    """Get user by valid reset token"""
    return db.query(models.User).filter(
        models.User.verification_token == token,
        models.User.verification_token_expires > datetime.now()
    ).first()


def update_user_password(db: Session, user_id: int, new_password: str) -> bool:
    """Update user password"""
    user = get_user(db, user_id)
    if not user:
        return False

    user.hashed_password = hash_password(new_password)
    user.verification_token = None  # Clear reset token
    user.verification_token_expires = None
    db.commit()
    return True


def change_user_password(db: Session, user_id: int, current_password: str, new_password: str) -> bool:
    """Change password with current password verification"""
    user = get_user(db, user_id)
    if not user or not verify_password(current_password, user.hashed_password):
        return False

    return update_user_password(db, user_id, new_password)