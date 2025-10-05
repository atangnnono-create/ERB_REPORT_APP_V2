from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
from enum import Enum
from datetime import datetime

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