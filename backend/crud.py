from sqlalchemy.orm import Session
from backend import models, schemas



# -------- USERS --------
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    from .auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# -------- REPORTS --------
def get_reports(db: Session, user_id: int):
    return db.query(models.Report).filter(models.Report.owner_id == user_id).all()

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
        db_report = models.Report(title=report.title, content=report.content, owner_id=user_id)
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
    else:
        # UPDATE existing report
        db_report.title = report.title
        db_report.content = report.content
        db.commit()
        db.refresh(db_report)

    # UPSERT competencies
    for comp in report.competencies:
        upsert_competency(db, db_report.id, user_id, comp)

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