from sqlalchemy import func, distinct, text
from datetime import timedelta, datetime
from typing import List, Any
from backend.app.models import models
from backend.app.schemas import schemas
from backend.app.crud import crud
from backend.app.core.security import require_permission, Permission
import time
from backend.app.models.models import Report
import os
import logging
import psutil
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.utils.utilities import audit_service, AuditActions


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=schemas.PaginatedUsersResponse)
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.USER_MANAGE))
):
    """List users with pagination and total count"""
    users = crud.get_users(db, skip=skip, limit=limit)
    total_count = db.query(func.count(models.User.id)).scalar()

    return {
        "users": users,
        "total_count": total_count,
        "page": skip // limit + 1,
        "page_size": limit
    }


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

############################ REPORTS #####################################################

@router.get("/reports", response_model=schemas.PaginatedReportsResponse)
def list_all_reports(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.REPORT_MANAGE))
):
    """View all reports with pagination and total count"""
    reports = crud.get_all_reports_paginated(db, skip=skip, limit=limit)
    total_count = db.query(func.count(models.Report.id)).scalar()

    return {
        "reports": reports,
        "total_count": total_count,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.get("/quick-stats")
def get_quick_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permission.REPORT_REVIEW))
):
    """Lightweight quick stats - counts only, no full data"""
    # User counts
    total_users = db.query(func.count(models.User.id)).scalar()
    active_users_today = db.query(func.count(distinct(Report.owner_id))).filter(
        Report.created_at >= datetime.now().date()
    ).scalar()
    new_users_7d = db.query(func.count(models.User.id)).filter(
        models.User.created_at >= datetime.now() - timedelta(days=7)
    ).scalar()

    # Report counts
    total_reports = db.query(func.count(models.Report.id)).scalar()
    new_reports_7d = db.query(func.count(models.Report.id)).filter(
        models.Report.created_at >= datetime.now() - timedelta(days=7)
    ).scalar()

    # Approval rate
    approved_reports = db.query(func.count(models.Report.id)).filter(
        models.Report.status == 'approved'
    ).scalar()
    reviewed_reports = db.query(func.count(models.Report.id)).filter(
        models.Report.status.in_(['approved', 'rejected'])
    ).scalar()
    approval_rate = (approved_reports / reviewed_reports * 100) if reviewed_reports > 0 else 0

    return {
        'total_users': total_users,
        'active_users_today': active_users_today,
        'new_users_7d': new_users_7d,
        'total_reports': total_reports,
        'new_reports_7d': new_reports_7d,
        'approval_rate': approval_rate,
        'avg_response_time': 2.5  # Placeholder
    }




@router.delete("/reports/{report_id}")
def delete_report_as_admin(
        report_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(require_permission(Permission.REPORT_MANAGE))
):
    """Delete any report (admin only) - bypasses ownership checks"""
    try:
        # Use the generic getter (this is the new function)
        db_report = crud.get_report_by_id(db, report_id)  # ← CHANGED TO get_report_by_id
        if not db_report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Store report info for audit log before deletion
        report_title = db_report.title
        report_owner = db_report.owner.username if db_report.owner else "Unknown"

        # Delete the report
        crud.delete_report(db, db_report)

        audit_service.log_action(
            db=db,
            action=AuditActions.REPORT_DELETE,
            user_id=current_user.id,
            username=current_user.username,
            resource_type="report",
            resource_id=report_id,
            details={
                "report_title": report_title,
                "report_owner": report_owner,
                "admin_username": current_user.username,
                "deletion_type": "admin_forced_deletion"
            },
            request=request
        )

        return {"detail": "Report deleted successfully"}

    except Exception as e:
        # Log the actual error for debugging
        logger.error(f"Error in admin report deletion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
################################# DATABASE ENDPOINTS ########################################

@router.get("/database/stats")
def get_database_stats(db: Session = Depends(get_db)):
    """Get comprehensive database statistics"""
    try:
        # Table counts
        users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        reports_count = db.execute(text("SELECT COUNT(*) FROM reports")).scalar() or 0
        audit_logs_count = db.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar() or 0
        total_records = users_count + reports_count + audit_logs_count

        # Table list
        if "sqlite" in settings.database_url:
            tables_result = db.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )).fetchall()
        else:
            tables_result = db.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )).fetchall()

        tables = [row[0] for row in tables_result]

        # Database size
        db_size_mb = 0
        if 'sqlite' in settings.database_url:
            db_path = settings.database_url.replace('sqlite:///', '')
            if os.path.exists(db_path):
                db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        else:
            # PostgreSQL
            size_result = db.execute(text("SELECT pg_database_size(current_database())")).fetchone()
            if size_result:
                db_size_mb = round(size_result[0] / (1024 * 1024), 2)

        return {
            'total_records': total_records,
            'db_size_mb': db_size_mb,
            'users_count': users_count,
            'reports_count': reports_count,
            'audit_logs_count': audit_logs_count,
            'table_count': len(tables),
            'existing_tables': sorted(tables),
            'database_type': 'sqlite' if 'sqlite' in settings.database_url else 'postgresql',
            'timestamp': datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database stats unavailable: {str(e)}")


@router.get("/database/health")
def get_database_health(db: Session = Depends(get_db)):
    """Get database health and performance metrics"""
    try:
        # Test connection and basic query
        start_time = time.time()
        db.execute(text("SELECT 1"))
        response_time = round((time.time() - start_time) * 1000, 2)  # ms

        # Get connection info
        if "postgresql" in settings.database_url:
            connections_result = db.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )).fetchone()
            active_connections = connections_result[0] if connections_result else 1

            # Get additional PostgreSQL stats
            cache_hit_result = db.execute(text(
                "SELECT round(blks_hit * 100 / (blks_hit + blks_read), 2) as cache_hit_ratio FROM pg_stat_database WHERE datname = current_database()"
            )).fetchone()
            cache_hit_ratio = cache_hit_result[0] if cache_hit_result else 0
        else:
            active_connections = 1
            cache_hit_ratio = 0

        return {
            'status': 'healthy',
            'response_time_ms': response_time,
            'active_connections': active_connections,
            'cache_hit_ratio': cache_hit_ratio,
            'timestamp': datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
        }


@router.get("/database/tables")
def get_database_tables(db: Session = Depends(get_db)):
    """Get list of database tables with row counts"""
    try:
        if "sqlite" in settings.database_url:
            tables_result = db.execute(text("""
                SELECT name as table_name
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)).fetchall()

            # Get row counts for each table
            tables_with_counts = []
            for table in tables_result:
                table_name = table[0]
                count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
                tables_with_counts.append({
                    'name': table_name,
                    'row_count': count_result[0] if count_result else 0
                })
        else:
            # PostgreSQL
            tables_result = db.execute(text("""
                SELECT table_name,
                       (xpath('/row/cnt/text()', xml_count))[1]::text::int as row_count
                FROM (
                    SELECT table_name, 
                           query_to_xml(format('SELECT COUNT(*) as cnt FROM %I', table_name), false, true, '') as xml_count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                ) AS counts
            """)).fetchall()

            tables_with_counts = [
                {
                    'name': row[0],
                    'row_count': row[1],
                }
                for row in tables_result
            ]

        return {'tables': tables_with_counts}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table info: {str(e)}")


@router.get("/database/size")
def get_database_size(db: Session = Depends(get_db)):
    """Get database storage metrics"""
    try:
        if 'sqlite' in settings.database_url:
            db_path = settings.database_url.replace('sqlite:///', '')
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path)
                db_size_mb = round(file_size / (1024 * 1024), 2)

                # Get disk usage for SQLite context
                disk_usage = psutil.disk_usage(os.path.dirname(db_path))
                disk_free_gb = round(disk_usage.free / (1024 ** 3), 2)

                return {
                    'db_size_mb': db_size_mb,
                    'file_size_bytes': file_size,
                    'disk_free_gb': disk_free_gb,
                    'database_type': 'sqlite',
                    'timestamp': datetime.now().isoformat(),
                }
            else:
                raise HTTPException(status_code=404, detail="SQLite database file not found")
        else:
            # PostgreSQL
            size_result = db.execute(text("""
                SELECT 
                    pg_database_size(current_database()) as db_size,
                    pg_size_pretty(pg_database_size(current_database())) as db_size_pretty,
                    (SELECT setting FROM pg_settings WHERE name = 'data_directory') as data_directory
            """)).fetchone()

            if size_result:
                db_size_bytes = size_result[0]
                db_size_mb = round(db_size_bytes / (1024 * 1024), 2)

                # Get disk usage for PostgreSQL data directory
                data_dir = size_result[2]
                if data_dir and os.path.exists(data_dir):
                    disk_usage = psutil.disk_usage(data_dir)
                    disk_free_gb = round(disk_usage.free / (1024 ** 3), 2)
                else:
                    disk_free_gb = 0

                return {
                    'db_size_mb': db_size_mb,
                    'db_size_bytes': db_size_bytes,
                    'db_size_pretty': size_result[1],
                    'disk_free_gb': disk_free_gb,
                    'database_type': 'postgresql',
                    'timestamp': datetime.now().isoformat(),
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to get database size")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database size unavailable: {str(e)}")


@router.get("/system/metrics")
def get_system_metrics():
    """Get system performance metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = round(memory.used / (1024 ** 3), 2)
        memory_total_gb = round(memory.total / (1024 ** 3), 2)

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_free_gb = round(disk.free / (1024 ** 3), 2)
        disk_total_gb = round(disk.total / (1024 ** 3), 2)

        # System info
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = round(uptime_seconds / 3600, 2)

        return {
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count(),
            },
            'memory': {
                'percent': memory_percent,
                'used_gb': memory_used_gb,
                'total_gb': memory_total_gb,
            },
            'disk': {
                'percent': disk_percent,
                'free_gb': disk_free_gb,
                'total_gb': disk_total_gb,
            },
            'system': {
                'boot_time': boot_time.isoformat(),
                'uptime_hours': uptime_hours,
                'platform': os.name,
            },
            'timestamp': datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System metrics unavailable: {str(e)}")