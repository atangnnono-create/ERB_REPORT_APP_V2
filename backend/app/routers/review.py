from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.crud import crud
from backend.app.core.security import require_permission, Permission

router = APIRouter(prefix="/review", tags=["Review"])

@router.get("/reports", response_model=List[schemas.ReportResponse])
def get_reports_for_review(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.REPORT_REVIEW))
):
    """Get reports pending review (both submitted and under_review)"""
    return db.query(models.Report).filter(
        models.Report.status.in_([schemas.ReportStatus.SUBMITTED, schemas.ReportStatus.UNDER_REVIEW])
    ).all()

@router.post("/reports/{report_id}", response_model=schemas.ReportResponse)
def review_report(
    report_id: int,
    review: schemas.ReportReview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.REPORT_REVIEW))
):
    """Review a report (approve/reject)"""
    db_report = crud.review_report(db, report_id, review, current_user.id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report

@router.put("/reports/{report_id}/submit", response_model=schemas.ReportResponse)
def submit_report_for_review(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.REPORT_WRITE))
):
    """Submit a report for review"""
    db_report = crud.submit_report(db, report_id, current_user.id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report