import os
from ..database import SessionLocal
from ..models import Job, Certificate
from .generator import generate_certificate


def output_dir() -> str:
    return os.getenv("OUTPUT_DIR", "generated")


def process_job(job_id: int) -> None:
    # A fresh session: the request's session is closed by the time this runs.
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        job.status = "processing"
        db.commit()

        pending = db.query(Certificate).filter_by(job_id=job_id, status="pending").all()
        for cert in pending:
            path = os.path.join(output_dir(), f"job_{job_id}", f"cert_{cert.id}.pdf")
            try:
                generate_certificate(cert.recipient_name, job.event_name, job.issue_date, path)
                cert.status = "success"
                cert.file_path = path
            except Exception as e:  # one failure must not stop the others
                cert.status = "failed"
                cert.error_message = f"generation failed: {e}"
            db.commit()

        certs = db.query(Certificate).filter_by(job_id=job_id).all()
        failed = sum(1 for c in certs if c.status == "failed")
        succeeded = sum(1 for c in certs if c.status == "success")
        if failed == 0:
            job.status = "completed"
        elif succeeded == 0:
            job.status = "failed"
        else:
            job.status = "completed_with_errors"
        db.commit()
    finally:
        db.close()
