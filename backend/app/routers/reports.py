from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.crud import crud
from backend.app.core import database
from backend.app.services.auth import get_current_user
from backend.app.utils.utilities import audit_service, AuditActions


router = APIRouter(prefix="/reports", tags=["Reports"])
# POST /reports - create or update report + competencies
@router.post("/", response_model=schemas.ReportResponse)
def create_or_update_report(
    report: schemas.ReportCreate, request: Request,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a new report or update an existing one.
    Competencies are stored in the Competency table.
    """
    db_report = crud.create_or_update_report(db, report, current_user.id)

    # ✅ Log the report creation/update
    action = AuditActions.REPORT_CREATE if not getattr(report, 'id', None) else AuditActions.REPORT_UPDATE
    audit_service.log_action(
        db=db,
        action=action,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="report",
        resource_id=db_report.id,
        details={"title": db_report.title, "status": db_report.status},
        request=request
    )

    return db_report

# READ (all current user's reports)
@router.get("/", response_model=list[schemas.ReportResponse])
def list_reports(db: Session = Depends(database.get_db),
                 current_user: models.User =
                  Depends(get_current_user), ):
    return crud.get_reports(db, current_user.id)

# READ (single report by ID)
@router.get("/{report_id}", response_model=schemas.ReportResponse)
def get_report(report_id: int, db: Session =
                Depends(database.get_db), current_user: models.User
                = Depends(get_current_user), ):
    report = crud.get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# UPDATE (overwrite + merge)
@router.put("/{report_id}", response_model=schemas.ReportResponse)
def update_report(report_id: int, request: Request, updated: schemas.ReportCreate,
                  db: Session = Depends(database.get_db),
                  current_user: models.User =
                   Depends(get_current_user), ):
    # ✅ Log the report deletion
    audit_service.log_action(
        db=db,
        action=AuditActions.REPORT_DELETE,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="report",
        resource_id=report_id,
        request=request
    )
    # reuse the same function
    db_report = crud.create_or_update_report(db, updated, current_user.id)
    return db_report

# DELETE
@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(report_id: int, request: Request, db: Session =
    Depends(database.get_db), current_user:
    models.User = Depends(get_current_user), ):
    report = crud.get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # ✅ Log the report deletion
    audit_service.log_action(
        db=db,
        action=AuditActions.REPORT_DELETE,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="report",
        resource_id=report_id,
        request=request
    )
    crud.delete_report(db, report)
    return {"detail": "Report deleted successfully"}