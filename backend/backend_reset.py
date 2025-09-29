# backend/reset_db.py

from backend.database import Base, engine
from backend import models

# WARNING: This will delete all existing tables and data!
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("✅ Database reset: all tables recreated.")