from enum import Enum
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import field_validator, constr


# ✅ New Report Status Enum
class ReportStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"

# ---------------- TOKEN SCHEMAS ----------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# -------- USERS --------

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    password: constr(min_length=8)
    full_name: Optional[str] = None
    role: str = "candidate"

    @field_validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v


    @field_validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')

        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')

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
    full_name: Optional[str] = None
    role: UserRole = UserRole.CANDIDATE

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

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

# ✅ FIXED: Only ONE ReportCreate class
class ReportCreate(ReportBase):
    competencies: List[CompetencyCreate]
    status: ReportStatus = ReportStatus.DRAFT  # ✅ Add status with default

# ✅ FIXED: Only ONE ReportResponse class
class ReportResponse(ReportBase):
    id: int
    owner_id: int
    status: ReportStatus  # ✅ Include status in response
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_notes: Optional[str] = None
    competencies: List[CompetencyResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    competencies: Optional[List[CompetencyCreate]] = None
    status: Optional[ReportStatus] = None  # ✅ Status can be updated

# ✅ New schema for review actions
class ReportReview(BaseModel):
    status: ReportStatus
    review_notes: Optional[str] = None


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

    @field_validator('new_password')
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

    @field_validator('new_password')
    def validate_new_password(cls, v):
        # Reuse the same validation as PasswordResetConfirm
        return PasswordResetConfirm.validate_password(v)

class StandardResponse(BaseModel):
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None

class PaginatedResponse(BaseModel):
    """Paginated API response format"""
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ListResponse(BaseModel):
    """List API response format"""
    data: List[Any]
    total: int

class DetailResponse(BaseModel):
    """Detail API response format"""
    data: Any