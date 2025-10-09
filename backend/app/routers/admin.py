from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.crud import crud
from backend.app.core.security import require_permission, Permission

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[schemas.UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.USER_MANAGE))
):
    """List all users (admin only)"""
    return crud.get_users(db, skip=skip, limit=limit)

def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.USER_MANAGE))
):
    """Get user details (admin only)"""
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.USER_MANAGE))
):
    """Update user role/status (admin only)"""
    db_user = crud.update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/reports", response_model=List[schemas.ReportResponse])
def list_all_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.REPORT_MANAGE))
):
    """View all reports (admin/reviewer only)"""
    return crud.get_all_reports(db)