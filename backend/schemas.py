from typing import Optional, List
from pydantic import BaseModel


# ---------------- TOKEN SCHEMAS ----------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# -------- USERS --------
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "user"  # ✅ Add role field with default

class UserResponse(UserBase):
    id: int
    role: str  # ✅ Add role to response

    class Config:
        from_attributes = True

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
class ReportCreate(BaseModel):
    title: str
    content: Optional[str] = None
    competencies: List[CompetencyCreate]

class ReportResponse(ReportCreate):
    id: int
    owner_id: int
    competencies: List[CompetencyResponse] = []

    class Config:
        from_attributes = True

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    competencies: Optional[List[CompetencyCreate]] = None