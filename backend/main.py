# backend/main.py

import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
from database import SessionLocal, engine
# Import the Celery task
from celery_worker import perform_scan_task


app = FastAPI(title="BlackBox Guardian API")

# Allow Streamlit frontend (localhost:8501) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=engine)


# --- Pydantic Schemas ---
class ScanCreate(BaseModel):
    url: str

class ScanResponse(BaseModel):
    id: uuid.UUID
    target_url: str
    status: models.ScanStatus

    class Config:
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
    and triggers the background scan task.
    """
    new_scan = models.Scan(target_url=scan_request.url)
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    
    # Trigger the background Celery task
    perform_scan_task.delay(str(new_scan.id), new_scan.target_url)
    
    return new_scan


# --- Additional API endpoints for frontend polling ---
@app.get("/scan/{scan_id}")
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.get("/scan/{scan_id}/findings")
def get_findings(scan_id: str, db: Session = Depends(get_db)):
    findings = db.query(models.RawFinding).filter(models.RawFinding.scan_id == scan_id).all()
    return findings


@app.get("/scan/{scan_id}/logs")
def get_scan_logs(scan_id: str, db: Session = Depends(get_db)):
    logs = db.query(models.ScanLog).filter(models.ScanLog.scan_id == scan_id).order_by(models.ScanLog.created_at).all()
    return [ {"message": l.message, "created_at": l.created_at} for l in logs ]


@app.get("/scan/{scan_id}/tools")
def get_tool_statuses(scan_id: str, db: Session = Depends(get_db)):
    tools = db.query(models.ToolStatus).filter(models.ToolStatus.scan_id == scan_id).all()
    out = []
    for t in tools:
        out.append({
            "tool_name": t.tool_name,
            "status": t.status,
            "started_at": t.started_at,
            "finished_at": t.finished_at
        })
    return out


@app.get("/scans")
def list_scans(limit: int = 20, db: Session = Depends(get_db)):
    scans = db.query(models.Scan).order_by(models.Scan.created_at.desc()).limit(limit).all()
    return scans