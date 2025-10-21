# test_reports_operation.py
from backend.app.core.database import SessionLocal
from sqlalchemy import text


def test_reports_operation():
    """Test that we can query reports with the new columns"""
    db = SessionLocal()
    try:
        # Test querying reports
        result = db.execute(text("""
            SELECT id, title, status, erb_stage, current_stage_status 
            FROM reports 
            LIMIT 5
        """))

        reports = result.fetchall()
        print("✅ Successfully queried reports with new columns!")
        print(f"Found {len(reports)} reports")

        for report in reports:
            print(f" - Report {report[0]}: {report[1]}")
            print(f"   Status: {report[2]}, ERB Stage: {report[3]}, Stage Status: {report[4]}")

        # Test creating a new report (if you have data)
        test_new_report = db.execute(text("""
            INSERT INTO reports (title, content, owner_id, status, erb_stage, current_stage_status)
            VALUES ('Test Report', 'Test content', 1, 'draft', 'draft', 'not_started')
        """))
        db.commit()
        print("✅ Successfully created test report with new columns!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    test_reports_operation()