from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.core import security
from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.services.email_service import email_service
from backend.app.utils.utilities import audit_service, AuditActions

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("/submit")
def submit_contact_form(
        contact_data: schemas.ContactForm,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(security.get_current_user)
):
    """Submit contact form and send email to admin"""

    # Send email in background
    background_tasks.add_task(
        email_service.send_contact_form_email,
        contact_data,
        current_user  # Include user info if logged in
    )

    # Log the contact submission
    audit_service.log_action(
        db=db,
        action=AuditActions.CONTACT_SUBMISSION,
        user_id=current_user.id if current_user else None,
        username=current_user.username if current_user else "anonymous",
        resource_type="contact",
        details={
            "name": contact_data.name,
            "email": contact_data.email,
            "subject": contact_data.subject,
            "user_role": current_user.role if current_user else "guest",
            "timestamp": datetime.now().isoformat()
        },
        request=request
    )

    return {"detail": "Message sent successfully! We'll respond within 24 hours."}