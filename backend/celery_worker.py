# backend/celery_worker.py
import logging
from celery import Celery
from sqlalchemy.orm import Session

# Import our database and models
from database import SessionLocal
import models
from pentest_orchestrator.orchestrator import run_full_scan

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure Celery. 'redis' is the service name from docker-compose.
celery_app = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

@celery_app.task(name='tasks.perform_scan')
def perform_scan_task(scan_id: str, target_url: str):
    """The main Celery task that runs the full scan and saves results."""
    logging.info(f"Celery task started for scan_id: {scan_id} on {target_url}")
    
    db: Session = SessionLocal()
    try:
        # 1. Update scan status to RUNNING
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if not scan:
            logging.error(f"Scan with id {scan_id} not found.")
            return

        scan.status = models.ScanStatus.RUNNING
        db.commit()

        # 2. Run the actual scan by calling the orchestrator
        raw_findings = run_full_scan(scan_id, target_url) # This will take a long time

        # 3. Save the findings to the database
        for finding in raw_findings:
            new_finding = models.RawFinding(
                scan_id=scan_id,
                tool_source=finding.get("tool_source", "Unknown"),
                name=finding.get("name", "Unnamed Finding"),
                severity=finding.get("severity", "Info"),
                url=finding.get("url", target_url),
                evidence=finding.get("evidence", "")
            )
            db.add(new_finding)
        
        # 4. Update scan status to COMPLETED
        scan.status = models.ScanStatus.COMPLETED
        db.commit()
        logging.info(f"Celery task finished for scan_id: {scan_id}. {len(raw_findings)} findings saved.")

    except Exception as e:
        logging.error(f"An error occurred during scan task for scan_id {scan_id}: {e}", exc_info=True)
        # Rollback any partial changes and mark the scan as FAILED
        db.rollback()
        scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
        if scan:
            scan.status = models.ScanStatus.FAILED
            db.commit()
    finally:
        db.close()