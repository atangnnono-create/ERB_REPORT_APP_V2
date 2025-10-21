# test_database_erb_stage.py
from backend.app.core.database import engine
from sqlalchemy import text


def list_all_tables():
    """List all tables in the database"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        print("All tables in database:")
        for table in tables:
            print(f" - {table}")
        return tables


def check_reports_table_schema():
    """Specifically check the reports table schema"""
    with engine.connect() as conn:
        # Check if reports table exists and get its schema
        result = conn.execute(text("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='reports'
        """))

        table_info = result.fetchone()
        if table_info:
            print("\n=== Reports table schema ===")
            print(table_info[0])

            # Get detailed column info
            print("\n=== Reports table columns ===")
            columns_result = conn.execute(text("PRAGMA table_info(reports)"))
            for col in columns_result:
                pk_indicator = " (PRIMARY KEY)" if col[5] == 1 else ""
                null_indicator = " (NULLABLE)" if not col[3] else ""
                default_indicator = f" [DEFAULT: {col[4]}]" if col[4] else ""
                print(f"  - {col[1]}: {col[2]}{pk_indicator}{null_indicator}{default_indicator}")
        else:
            print("Reports table does not exist!")


def check_erb_stage_column():
    """Check if erb_stage column exists in reports table"""
    with engine.connect() as conn:
        columns_result = conn.execute(text("PRAGMA table_info(reports)"))
        columns = [col[1] for col in columns_result]

        print("\n=== Checking required columns ===")
        if 'erb_stage' in columns:
            print("✅ erb_stage column exists in reports table")
        else:
            print("❌ erb_stage column is MISSING from reports table")

        if 'current_stage_status' in columns:
            print("✅ current_stage_status column exists in reports table")
        else:
            print("❌ current_stage_status column is MISSING from reports table")

        return 'erb_stage' in columns and 'current_stage_status' in columns


def fix_missing_columns():
    """Add missing columns to reports table"""
    with engine.connect() as conn:
        try:
            # Add erb_stage column if it doesn't exist
            conn.execute(text("ALTER TABLE reports ADD COLUMN erb_stage VARCHAR DEFAULT 'draft'"))
            print("✅ Added erb_stage column to reports table")
        except Exception as e:
            print(f"ℹ️  erb_stage column already exists or error: {e}")

        try:
            # Add current_stage_status column if it doesn't exist
            conn.execute(text("ALTER TABLE reports ADD COLUMN current_stage_status VARCHAR DEFAULT 'not_started'"))
            print("✅ Added current_stage_status column to reports table")
        except Exception as e:
            print(f"ℹ️  current_stage_status column already exists or error: {e}")

        conn.commit()


if __name__ == "__main__":
    print("Checking database structure...")
    print("=" * 50)

    # List all tables
    list_all_tables()

    # Check reports table
    check_reports_table_schema()

    # Check for required columns
    columns_exist = check_erb_stage_column()

    # Fix missing columns if needed
    if not columns_exist:
        print("\n=== Fixing missing columns ===")
        fix_missing_columns()

        # Verify the fix
        print("\n=== Verifying fix ===")
        check_erb_stage_column()

    print("\n" + "=" * 50)
    print("Database check completed!")