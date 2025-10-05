from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend import models, schemas, crud
from backend.security import require_permission, Permission

router = APIRouter(prefix="/review", tags=["Review"])

@router.get("/reports", response_model=List[schemas.ReportResponse])
def get_reports_for_review(
    status: schemas.ReportStatus = schemas.ReportStatus.SUBMITTED,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.REPORT_REVIEW))
):
    """Get reports pending review"""
    return db.query(models.Report).filter(models.Report.status == status).all()

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