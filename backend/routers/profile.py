from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models, schemas, crud
from backend.security import require_active_user

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_profile(
        current_user: models.User = Depends(require_active_user())
):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
def update_current_user_profile(
        user_update: schemas.UserUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_active_user())
):
    """Update current user's profile (limited fields)"""
    # Users can only update certain fields themselves
    allowed_fields = {"email", "full_name"}
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items()
                   if k in allowed_fields}

    if update_data:
        return crud.update_user(db, current_user.id, schemas.UserUpdate(**update_data))
    return current_user