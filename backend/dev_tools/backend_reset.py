# backend/reset_db.py

from backend.app.core import Base, engine


# WARNING: This will delete all existing tables and data!
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("✅ Database reset: all tables recreated.")