from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
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
    # Get reports without owner filter (reviewers see all reports)
    reports = db.query(models.Report).options(
        joinedload(models.Report.reviewer),
        joinedload(models.Report.owner),
        joinedload(models.Report.competencies)
    ).filter(
        models.Report.status.in_([schemas.ReportStatus.SUBMITTED, schemas.ReportStatus.UNDER_REVIEW])
    ).all()

    return reports

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


#################################TEMPORARY DEBUG########################################

@router.get("/reports/debug")
def get_reports_debug(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.REPORT_REVIEW))
):
    """Debug endpoint to see raw report data"""
    reports = db.query(models.Report).options(
        joinedload(models.Report.reviewer)
    ).filter(
        models.Report.status.in_([schemas.ReportStatus.SUBMITTED, schemas.ReportStatus.UNDER_REVIEW])
    ).all()

    debug_data = []
    for report in reports:
        debug_data.append({
            'id': report.id,
            'title': report.title,
            'status': report.status,
            'reviewed_by': report.reviewed_by,
            'reviewer_username': report.reviewer.username if report.reviewer else None,
            'reviewer_full_name': report.reviewer.full_name if report.reviewer else None,
            'has_reviewer_object': report.reviewer is not None
        })

    return debug_data


@router.post("/reports/{report_id}/progress-stage", response_model=schemas.ReportResponse)
def progress_erb_stage(
        report_id: int,
        progression: schemas.StageProgression,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.REPORT_REVIEW))
):
    """Progress a report through ERB stages"""
    db_report = crud.progress_erb_stage(db, report_id, progression, current_user.id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report


@router.get("/reports/{report_id}/stage-history")
def get_stage_history(
        report_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.REPORT_REVIEW))
):
    """Get ERB stage history for a report"""
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    stage_history = {
        "desktop_assessment_started": report.desktop_assessment_started,
        "standard_review_started": report.standard_review_started,
        "professional_assessment_started": report.professional_assessment_started,
        "professional_review_started": report.professional_review_started,
        "current_stage": report.erb_stage,
        "current_status": report.current_stage_status
    }

    return stage_history