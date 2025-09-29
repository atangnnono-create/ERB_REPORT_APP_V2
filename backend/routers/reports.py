from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, database, crud
from ..auth import get_current_user


router = APIRouter(prefix="/reports", tags=["Reports"])
# POST /reports - create or update report + competencies
@router.post("/", response_model=schemas.ReportResponse)
def create_or_update_report(
    report: schemas.ReportCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a new report or update an existing one.
    Competencies are stored in the Competency table.
    """
    db_report = crud.create_or_update_report(db, report, current_user.id)
    return db_report

# READ (all current user's reports)
@router.get("/", response_model=list[schemas.ReportResponse])
def list_reports( db: Session = Depends(database.get_db),
                  current_user: models.User =
                  Depends(get_current_user), ):
    return crud.get_reports(db, current_user.id)

# READ (single report by ID)
@router.get("/{report_id}", response_model=schemas.ReportResponse)
def get_report( report_id: int, db: Session =
                Depends(database.get_db), current_user: models.User
                = Depends(get_current_user), ):
    report = crud.get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# UPDATE (overwrite + merge)
@router.put("/{report_id}", response_model=schemas.ReportResponse)
def update_report( report_id: int, updated: schemas.ReportCreate,
                   db: Session = Depends(database.get_db),
                   current_user: models.User =
                   Depends(get_current_user), ):
    # reuse the same function
    db_report = crud.create_or_update_report(db, updated, current_user.id)
    return db_report

# DELETE
@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report( report_id: int, db: Session =
    Depends(database.get_db), current_user:
    models.User = Depends(get_current_user), ):
    report = crud.get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    crud.delete_report(db, report)
    return {"detail": "Report deleted successfully"}