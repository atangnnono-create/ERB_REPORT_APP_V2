from backend.database import SessionLocal
from backend import models, schemas, crud
from backend.utils import hash_password

db = SessionLocal()
try:
    admin_user = models.User(
        username="admin",
        email="molokwel@bpc.bw",
        hashed_password=hash_password("Molokwe123"),
        role="admin"
    )
    db.add(admin_user)
    db.commit()
    print("✅ Admin user created: username='Molokwe', password='Molokwe123'")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()