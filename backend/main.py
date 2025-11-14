# backend/main.py

import uuid
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
from database import SessionLocal, engine


app = FastAPI(title="BlackBox Guardian API")


@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=engine)


# --- Pydantic Schemas ---

class ScanCreate(BaseModel):
    url: str

class ScanResponse(BaseModel):
    # THIS IS THE FIX: The field name 'id' now matches the SQLAlchemy model
    id: uuid.UUID
    target_url: str
    status: models.ScanStatus

    class Config:
        # 'orm_mode' is now 'from_attributes' in Pydantic V2
        from_attributes = True


# --- Dependency for getting a DB session ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "BlackBox Guardian API is running"}


@app.post("/scan/start", response_model=ScanResponse)
def start_new_scan(scan_request: ScanCreate, db: Session = Depends(get_db)):
    """
    Receives a URL, creates a new scan record in the database,
    and returns the initial scan details.
    """
    new_scan = models.Scan(target_url=scan_request.url)
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    return new_scan