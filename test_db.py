import sqlite3


def check_reports():
    conn = sqlite3.connect('reports.db')
    c = conn.cursor()

    # Check under_review reports
    print("=== UNDER REVIEW REPORTS ===")
    c.execute("SELECT id, title, status, reviewed_by FROM reports WHERE status = 'under_review'")
    rows = c.fetchall()
    print(f"Found {len(rows)} under_review reports:")
    for r in rows:
        print(f"ID: {r[0]}, Title: {r[1]}, Status: {r[2]}, Reviewed_by: {r[3]}")

    print("\n=== ALL REPORTS WITH REVIEWER INFO ===")
    c.execute("""
        SELECT r.id, r.title, r.status, r.reviewed_by, u.username, u.full_name 
        FROM reports r 
        LEFT JOIN users u ON r.reviewed_by = u.id 
        WHERE r.status IN ('submitted', 'under_review')
    """)
    rows = c.fetchall()
    print(f"Found {len(rows)} total reports:")
    for r in rows:
        print(f"ID: {r[0]}, Title: {r[1]}, Status: {r[2]}, Reviewed_by: {r[3]}, Reviewer: {r[4]} ({r[5]})")

    print("\n=== AVAILABLE REVIEWERS ===")
    c.execute("SELECT id, username, full_name, role FROM users WHERE role IN ('admin', 'reviewer')")
    rows = c.fetchall()
    print(f"Found {len(rows)} reviewers:")
    for r in rows:
        print(f"ID: {r[0]}, Username: {r[1]}, Name: {r[2]}, Role: {r[3]}")

    conn.close()


if __name__ == "__main__":
    check_reports()