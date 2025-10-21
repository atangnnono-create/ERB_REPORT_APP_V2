""" add_performance_indexes

Revision ID: 60425bcc9d40
Revises: 
Create Date: 2025-10-20 07:23:28.494750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60425bcc9d40'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== USERS TABLE INDEXES ====================
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_active_role', 'users', ['is_active', 'role'])
    op.create_index('idx_users_verified_active', 'users', ['is_verified', 'is_active'])

    # ==================== REPORTS TABLE INDEXES ====================
    op.create_index('idx_reports_owner_id', 'reports', ['owner_id'])
    op.create_index('idx_reports_status', 'reports', ['status'])
    op.create_index('idx_reports_erb_stage', 'reports', ['erb_stage'])
    op.create_index('idx_reports_current_stage_status', 'reports', ['current_stage_status'])
    op.create_index('idx_reports_reviewed_by', 'reports', ['reviewed_by'])
    op.create_index('idx_reports_submitted_at', 'reports', ['submitted_at'])
    op.create_index('idx_reports_reviewed_at', 'reports', ['reviewed_at'])
    op.create_index('idx_reports_created_at', 'reports', ['created_at'])
    op.create_index('idx_reports_updated_at', 'reports', ['updated_at'])
    op.create_index('idx_reports_owner_status', 'reports', ['owner_id', 'status'])
    op.create_index('idx_reports_status_stage', 'reports', ['status', 'erb_stage'])
    op.create_index('idx_reports_owner_created', 'reports', ['owner_id', 'created_at'])
    op.create_index('idx_reports_reviewer_status', 'reports', ['reviewed_by', 'status'])
    op.create_index('idx_reports_created_status', 'reports', ['created_at', 'status'])
    op.create_index('idx_reports_stage_status', 'reports', ['erb_stage', 'current_stage_status'])

    # ==================== AUDIT LOGS TABLE INDEXES ====================
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_username', 'audit_logs', ['username'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('idx_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('idx_audit_logs_action_resource', 'audit_logs', ['action', 'resource_type'])
    op.create_index('idx_audit_logs_created_user', 'audit_logs', ['created_at', 'user_id'])
    op.create_index('idx_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('idx_audit_logs_resource_created', 'audit_logs', ['resource_type', 'created_at'])
    op.create_index('idx_audit_logs_username_created', 'audit_logs', ['username', 'created_at'])

    # ==================== COMPETENCIES TABLE INDEXES ====================
    op.create_index('idx_competencies_owner_id', 'competencies', ['owner_id'])
    op.create_index('idx_competencies_report_id', 'competencies', ['report_id'])
    op.create_index('idx_competencies_report_owner', 'competencies', ['report_id', 'owner_id'])
    op.create_index('idx_competencies_key_owner', 'competencies', ['competency_key', 'owner_id'])
    op.create_index('idx_competencies_created_owner', 'competencies', ['created_at', 'owner_id'])

    # ==================== REPORT VERSIONS TABLE INDEXES ====================
    op.create_index('idx_report_versions_report_id', 'report_versions', ['report_id'])
    op.create_index('idx_report_versions_created_by', 'report_versions', ['created_by'])
    op.create_index('idx_report_versions_created_at', 'report_versions', ['created_at'])
    op.create_index('idx_report_versions_report_created', 'report_versions', ['report_id', 'created_at'])


def downgrade() -> None:
    # ==================== REPORT VERSIONS TABLE INDEXES ====================
    op.drop_index('idx_report_versions_report_created', 'report_versions')
    op.drop_index('idx_report_versions_created_at', 'report_versions')
    op.drop_index('idx_report_versions_created_by', 'report_versions')
    op.drop_index('idx_report_versions_report_id', 'report_versions')

    # ==================== COMPETENCIES TABLE INDEXES ====================
    op.drop_index('idx_competencies_created_owner', 'competencies')
    op.drop_index('idx_competencies_key_owner', 'competencies')
    op.drop_index('idx_competencies_report_owner', 'competencies')
    op.drop_index('idx_competencies_report_id', 'competencies')
    op.drop_index('idx_competencies_owner_id', 'competencies')

    # ==================== AUDIT LOGS TABLE INDEXES ====================
    op.drop_index('idx_audit_logs_username_created', 'audit_logs')
    op.drop_index('idx_audit_logs_resource_created', 'audit_logs')
    op.drop_index('idx_audit_logs_user_created', 'audit_logs')
    op.drop_index('idx_audit_logs_created_user', 'audit_logs')
    op.drop_index('idx_audit_logs_action_resource', 'audit_logs')
    op.drop_index('idx_audit_logs_user_action', 'audit_logs')
    op.drop_index('idx_audit_logs_created_at', 'audit_logs')
    op.drop_index('idx_audit_logs_resource_id', 'audit_logs')
    op.drop_index('idx_audit_logs_resource_type', 'audit_logs')
    op.drop_index('idx_audit_logs_action', 'audit_logs')
    op.drop_index('idx_audit_logs_username', 'audit_logs')
    op.drop_index('idx_audit_logs_user_id', 'audit_logs')

    # ==================== REPORTS TABLE INDEXES ====================
    op.drop_index('idx_reports_stage_status', 'reports')
    op.drop_index('idx_reports_created_status', 'reports')
    op.drop_index('idx_reports_reviewer_status', 'reports')
    op.drop_index('idx_reports_owner_created', 'reports')
    op.drop_index('idx_reports_status_stage', 'reports')
    op.drop_index('idx_reports_owner_status', 'reports')
    op.drop_index('idx_reports_updated_at', 'reports')
    op.drop_index('idx_reports_created_at', 'reports')
    op.drop_index('idx_reports_reviewed_at', 'reports')
    op.drop_index('idx_reports_submitted_at', 'reports')
    op.drop_index('idx_reports_reviewed_by', 'reports')
    op.drop_index('idx_reports_current_stage_status', 'reports')
    op.drop_index('idx_reports_erb_stage', 'reports')
    op.drop_index('idx_reports_status', 'reports')
    op.drop_index('idx_reports_owner_id', 'reports')

    # ==================== USERS TABLE INDEXES ====================
    op.drop_index('idx_users_verified_active', 'users')
    op.drop_index('idx_users_active_role', 'users')
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_is_active', 'users')
    op.drop_index('idx_users_role', 'users')