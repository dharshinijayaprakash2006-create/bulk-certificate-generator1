import io
import os
import zipfile
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from .database import get_db
from .models import Job, Certificate
from .schemas import JobCreate, validate_recipient
from .services.processor import process_job

router = APIRouter()


@router.post("/jobs", status_code=202)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = Job(
        event_name=payload.event_name,
        issue_date=payload.issue_date.isoformat(),
        total=len(payload.recipients),
        status="pending",
    )
    db.add(job)
    db.flush()  # get job.id

    for r in payload.recipients:
        error = validate_recipient(r)
        name, email = r.get("name"), r.get("email")
        db.add(Certificate(
            job_id=job.id,
            recipient_name=str(name) if name is not None else None,
            email=str(email) if email is not None else None,
            status="failed" if error else "pending",
            error_message=error,
        ))
    db.commit()

    background_tasks.add_task(process_job, job.id)
    return {"job_id": job.id, "status": job.status, "total": job.total,
            "status_url": f"/jobs/{job.id}"}


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    certs = job.certificates
    succeeded = sum(1 for c in certs if c.status == "success")
    failed = sum(1 for c in certs if c.status == "failed")
    pending = job.total - succeeded - failed
    progress = round((succeeded + failed) / job.total * 100, 1) if job.total else 100.0

    return {
        "job_id": job.id,
        "event_name": job.event_name,
        "status": job.status,
        "total": job.total,
        "succeeded": succeeded,
        "failed": failed,
        "pending": pending,
        "progress_percent": progress,
        "download_all_url": f"/jobs/{job.id}/download" if succeeded else None,
        "certificates": [
            {
                "id": c.id,
                "name": c.recipient_name,
                "email": c.email,
                "status": c.status,
                "error_message": c.error_message,
                "download_url": f"/certificates/{c.id}/download" if c.status == "success" else None,
            }
            for c in certs
        ],
    }


@router.get("/certificates/{cert_id}/download")
def download_certificate(cert_id: int, db: Session = Depends(get_db)):
    cert = db.get(Certificate, cert_id)
    if not cert:
        raise HTTPException(404, "Certificate not found")
    if cert.status != "success" or not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(404, "Certificate file is not available")
    return FileResponse(cert.file_path, media_type="application/pdf",
                        filename=f"certificate_{cert.id}.pdf")


@router.get("/jobs/{job_id}/download")
def download_job_zip(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for c in job.certificates:
            if c.status == "success" and c.file_path and os.path.exists(c.file_path):
                z.write(c.file_path, arcname=f"certificate_{c.id}.pdf")
                count += 1
    if count == 0:
        raise HTTPException(404, "No generated certificates available for this job")

    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="job_{job_id}.zip"'})