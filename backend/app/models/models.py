from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base
from sqlalchemy import DateTime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="candidate", index=True)  # ✅ Added index
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, index=True)  # ✅ Added index
    is_verified = Column(Boolean, default=False)

    # Enhanced verification fields
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    verification_sent_at = Column(DateTime(timezone=True), nullable=True)

    competencies = relationship("Competency", back_populates="owner")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # ✅ Added index
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Specify foreign_keys to resolve ambiguity
    reports = relationship("Report", back_populates="owner", foreign_keys="Report.owner_id")
    reviewed_reports = relationship("Report", back_populates="reviewer", foreign_keys="Report.reviewed_by")

    # ✅ Added composite indexes for common query patterns
    __table_args__ = (
        Index('idx_users_active_role', 'is_active', 'role'),
        Index('idx_users_verified_active', 'is_verified', 'is_active'),
    )


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)

    # ✅ CRITICAL: Added indexes on all filtered columns
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(String, default="draft", index=True)
    erb_stage = Column(String, default="draft", index=True)
    current_stage_status = Column(String, default="not_started", index=True)

    # Stage-specific timestamps
    desktop_assessment_started = Column(DateTime(timezone=True), nullable=True)
    standard_review_started = Column(DateTime(timezone=True), nullable=True)
    professional_assessment_started = Column(DateTime(timezone=True), nullable=True)
    professional_review_started = Column(DateTime(timezone=True), nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # ✅ Added index
    reviewed_at = Column(DateTime(timezone=True), nullable=True, index=True)  # ✅ Added index
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    review_notes = Column(Text, nullable=True)

    # Specify foreign_keys to resolve ambiguity
    owner = relationship("User", back_populates="reports", foreign_keys=[owner_id])
    reviewer = relationship("User", back_populates="reviewed_reports", foreign_keys=[reviewed_by])
    competencies = relationship("Competency", back_populates="report")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # ✅ Added index
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), index=True)  # ✅ Added index

    # ✅ REMOVED: Property-based relationships that cause N+1 queries
    # These are now handled through proper eager loading in queries

    # ✅ Added composite indexes for common admin query patterns
    __table_args__ = (
        Index('idx_reports_owner_status', 'owner_id', 'status'),
        Index('idx_reports_status_stage', 'status', 'erb_stage'),
        Index('idx_reports_owner_created', 'owner_id', 'created_at'),
        Index('idx_reports_reviewer_status', 'reviewed_by', 'status'),
        Index('idx_reports_created_status', 'created_at', 'status'),
        Index('idx_reports_stage_status', 'erb_stage', 'current_stage_status'),
    )


#############################################################################################
 # ✅ TEMPORARY FIX: Add properties for Pydantic serialization
    @property
    def owner_username(self):
        return self.owner.username if self.owner else None

    @property
    def owner_full_name(self):
        return self.owner.full_name if self.owner else None

    @property
    def owner_email(self):
        return self.owner.email if self.owner else None

    @property
    def reviewer_username(self):
        return self.reviewer.username if self.reviewer else None

    @property
    def reviewer_full_name(self):
        return self.reviewer.full_name if self.reviewer else None
#############################################################################################


class ReportVersion(Base):
    __tablename__ = "report_versions"

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("reports.id"), index=True)  # ✅ Added index
    version_number = Column(Integer)
    title = Column(String)
    content = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), index=True)  # ✅ Added index
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # ✅ Added index

    # ✅ Added composite index
    __table_args__ = (
        Index('idx_report_versions_report_created', 'report_id', 'created_at'),
    )


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    competency_key = Column(String, index=True)
    competency_title = Column(String, nullable=False)
    user_response = Column(Text, nullable=False)

    # ✅ CRITICAL: Added indexes on foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), index=True)

    report = relationship("Report", back_populates="competencies")
    owner = relationship("User", back_populates="competencies")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ✅ Added composite indexes for common query patterns
    __table_args__ = (
        Index('idx_competencies_report_owner', 'report_id', 'owner_id'),
        Index('idx_competencies_key_owner', 'competency_key', 'owner_id'),
        Index('idx_competencies_created_owner', 'created_at', 'owner_id'),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # ✅ CRITICAL: Added indexes on all filtered columns
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String, nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=True, index=True)
    resource_id = Column(Integer, nullable=True, index=True)

    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # ✅ Added composite indexes for common admin query patterns
    __table_args__ = (
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
        Index('idx_audit_logs_action_resource', 'action', 'resource_type'),
        Index('idx_audit_logs_created_user', 'created_at', 'user_id'),
        Index('idx_audit_logs_user_created', 'user_id', 'created_at'),
        Index('idx_audit_logs_resource_created', 'resource_type', 'created_at'),
        Index('idx_audit_logs_username_created', 'username', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username} at {self.created_at}>"