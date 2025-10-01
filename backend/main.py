from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from backend import models, schemas, crud, auth
from . database import engine, Base, get_db
from backend.routers import reports, users

app = FastAPI()

app.include_router(reports.router)
app.include_router(users.router)

if __name__ == "__main__":
    # Render provides $PORT
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)



# DB init (dev only, use Alembic in prod)
Base.metadata.create_all(bind=engine)

# -------- AUTH --------
@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db, user)

@app.post("/auth/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, form_data.username)
    if not db_user or not auth.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# -------- REPORTS --------
@app.post("/reports/", response_model=schemas.ReportResponse)
def create_or_update_report(
    report: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    return crud.create_or_update_report(db, report, user_id=current_user.id)

@app.get("/reports/", response_model=List[schemas.ReportResponse])
def get_reports(db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    return db.query(models.Report).filter_by(owner_id=current_user.id).all()

@app.get("/reports/{report_id}", response_model=schemas.ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    report = crud.get_report(db, report_id, user_id=current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@app.put("/reports/{report_id}", response_model=schemas.ReportResponse)
def update_report(report_id: int, update: schemas.ReportUpdate, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    report = crud.get_report(db, report_id, user_id=current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return crud.update_report(db, report, update)

@app.delete("/reports/{report_id}", response_model=dict)
def delete_report(report_id: int, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    report = crud.get_report(db, report_id, user_id=current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    crud.delete_report(db, report)
    return {"msg": "Report deleted"}