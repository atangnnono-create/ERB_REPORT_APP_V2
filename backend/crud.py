from sqlalchemy.orm import Session
from backend import models, schemas
from backend.utils import hash_password  # ✅ Import from utils instead of auth
from sqlalchemy.sql import func

# -------- USERS --------
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
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


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None

    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

# -------- REPORTS --------
def get_reports(db: Session, user_id: int):
    return db.query(models.Report).filter(models.Report.owner_id == user_id).all()

def get_all_reports(db: Session):
    """Get ALL reports (for admin/reviewer roles)"""
    return db.query(models.Report).all()

def get_report(db: Session, report_id: int, user_id: int):
    return db.query(models.Report).filter(
        models.Report.id == report_id,
        models.Report.owner_id == user_id
    ).first()

def delete_report(db: Session, report: models.Report):
    db.delete(report)
    db.commit()

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
        db_report = models.Report(title=report.title, content=report.content, owner_id=user_id,  status=report.status)
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

# ✅ New function for report review
def review_report(db: Session, report_id: int, review: schemas.ReportReview, reviewer_id: int):
    db_report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not db_report:
        return None

    db_report.status = review.status
    db_report.reviewed_at = func.now()
    db_report.reviewed_by = reviewer_id
    db_report.review_notes = review.review_notes

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