from enum import Enum
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# ✅ New Report Status Enum
class ReportStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"

# ✅ NEW: ERB Stage Enums
class ERBStage(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    DESKTOP_ASSESSMENT = "desktop_assessment"
    STANDARD_REVIEW = "standard_review"
    PROFESSIONAL_ASSESSMENT = "professional_assessment"
    PROFESSIONAL_REVIEW = "professional_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class StageStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

# ---------------- TOKEN SCHEMAS ----------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# -------- USERS --------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "candidate"

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores allowed)')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

# User Roles Enum
class UserRole(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    ENGINEER = "engineer"
    TECHNOLOGIST = "technologist"
    TECHNICIAN = "technician"
    CANDIDATE = "candidate"

# Enhanced User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: str
    role: UserRole = UserRole.CANDIDATE

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

    @validator('email')
    def validate_email(cls, v):
        if v and len(v) < 5:
            raise ValueError('Email must be at least 5 characters')
        return v

# -------- COMPETENCIES --------
class CompetencyCreate(BaseModel):
    competency_key: str
    competency_title: str
    user_response: str

class CompetencyResponse(CompetencyCreate):
    id: int

    class Config:
        from_attributes = True

# -------- REPORTS --------
class ReportBase(BaseModel):
    title: str
    content: Optional[str] = None

class ReportCreate(ReportBase):
    competencies: List[CompetencyCreate]
    status: ReportStatus = ReportStatus.DRAFT

class ReportSubmit(BaseModel):
    title: str
    content: Optional[str] = None
    competencies: List[CompetencyCreate]

class ReportResponse(ReportBase):
    id: int
    owner_id: int
    status: ReportStatus
    erb_stage: ERBStage
    current_stage_status: StageStatus
    desktop_assessment_started: Optional[datetime] = None
    standard_review_started: Optional[datetime] = None
    professional_assessment_started: Optional[datetime] = None
    professional_review_started: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_notes: Optional[str] = None
    competencies: List[CompetencyResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_username: Optional[str] = None
    owner_full_name: Optional[str] = None
    owner_email: Optional[str] = None
    reviewer_username: Optional[str] = None
    reviewer_full_name: Optional[str] = None

    class Config:
        from_attributes = True

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    competencies: Optional[List[CompetencyCreate]] = None
    status: Optional[ReportStatus] = None

class ReviewerAssignment(BaseModel):
    reviewer_id: Optional[int] = None

class ReportReview(BaseModel):
    status: ReportStatus
    review_notes: Optional[str] = None

class StageProgression(BaseModel):
    next_stage: ERBStage
    notes: Optional[str] = None
    status: StageStatus = StageStatus.IN_PROGRESS

# ✅ AUDIT LOG SCHEMAS
class AuditLogBase(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogQuery(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    limit: int = 100
    offset: int = 0

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class PasswordResetResponse(BaseModel):
    message: str
    email: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None

class PaginatedResponse(BaseModel):
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ListResponse(BaseModel):
    data: List[Any]
    total: int

class DetailResponse(BaseModel):
    data: Any

class VerifyEmail(BaseModel):
    token: str

class PaginatedUsersResponse(BaseModel):
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int

class PaginatedReportsResponse(BaseModel):
    reports: List[ReportResponse]
    total_count: int
    page: int
    page_size: int