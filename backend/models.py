from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
from sqlalchemy import DateTime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="candidate")
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # ✅ Enhanced verification fields
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    verification_sent_at = Column(DateTime(timezone=True), nullable=True)

    reports = relationship("Report", back_populates="owner")
    competencies = relationship("Competency", back_populates="owner")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ✅ Specify foreign_keys to resolve ambiguity
    reports = relationship("Report", back_populates="owner", foreign_keys="Report.owner_id")
    reviewed_reports = relationship("Report", back_populates="reviewer", foreign_keys="Report.reviewed_by")
    competencies = relationship("Competency", back_populates="owner")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # ✅ New fields for review workflow
    status = Column(String, default="draft")
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # This creates the ambiguity
    review_notes = Column(Text, nullable=True)

    # ✅ Specify foreign_keys to resolve ambiguity
    owner = relationship("User", back_populates="reports", foreign_keys=[owner_id])
    reviewer = relationship("User", back_populates="reviewed_reports", foreign_keys=[reviewed_by])
    competencies = relationship("Competency", back_populates="report")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Competency(Base):
    __tablename__ = "competencies"
    id = Column(Integer, primary_key=True, index=True)
    competency_key = Column(String, index=True)
    competency_title = Column(String, nullable=False)
    user_response = Column(Text, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"))
    report_id = Column(Integer, ForeignKey("reports.id"))
    report = relationship("Report", back_populates="competencies")
    owner = relationship("User", back_populates="competencies")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # User who performed the action
    username = Column(String, nullable=True)  # Store username for easier querying
    action = Column(String, nullable=False)  # Action performed (login, create_report, etc.)
    resource_type = Column(String, nullable=True)  # Type of resource (user, report, etc.)
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    details = Column(JSON, nullable=True)  # Additional details in JSON format
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username} at {self.created_at}>"