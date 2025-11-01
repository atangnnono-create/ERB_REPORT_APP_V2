# improved_health_check.py
import sys

sys.path.append('backend')

from backend.app.core.database import engine, Base
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detailed_database_health_check():
    """Detailed database health check with more information"""
    try:
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT 1"))
            basic_test = result.scalar()

            # Check tables
            tables = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )).fetchall()

            # Check if key tables exist
            table_names = [table[0] for table in tables]
            key_tables = ['users', 'reports', 'audit_logs', 'competencies']
            missing_tables = [table for table in key_tables if table not in table_names]

            return {
                'basic_connection': basic_test == 1,
                'tables_found': len(tables),
                'table_names': table_names,
                'missing_key_tables': missing_tables,
                'overall_health': basic_test == 1 and len(missing_tables) == 0
            }

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            'basic_connection': False,
            'tables_found': 0,
            'table_names': [],
            'missing_key_tables': [],
            'overall_health': False,
            'error': str(e)
        }


print("=== Detailed Database Health Check ===")
result = detailed_database_health_check()
print("Health Check Results:")
for key, value in result.items():
    print(f"  {key}: {value}")

# Test the original function too
from backend.app.core.database import check_database_health

print(f"\nOriginal check_database_health(): {check_database_health()}")