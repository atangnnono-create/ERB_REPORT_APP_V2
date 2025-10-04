from fastapi import FastAPI
from backend.database import engine, Base
from backend.routers import reports, users, auth

app = FastAPI()

# Include routers (these contain all the routes)
app.include_router(reports.router)
app.include_router(users.router)
app.include_router(auth.router)

if __name__ == "__main__":
    # Render provides $PORT
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# DB init (dev only, use Alembic in prod)
Base.metadata.create_all(bind=engine)

#----------------root route---------------------
@app.get("/")
def root():
    return {"message": "Backend is running 🚀"}