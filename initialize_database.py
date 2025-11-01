# manual_fix.py
import sys

sys.path.append('backend')

from backend.app.core.database import init_db, engine
from sqlalchemy import text

print("Manual database initialization...")
try:
    init_db()
    print("✅ Database initialized")

    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"✅ Connection test: {result.scalar()}")

    print("Now restart your FastAPI server and check the health endpoint")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()