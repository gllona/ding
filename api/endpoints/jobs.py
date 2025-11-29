"""Job management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

from core.database import get_db
from core.models import DingJob, User
from api.auth import verify_api_key
from services.printer import printer_service


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# Pydantic schemas
class JobResponse(BaseModel):
    id: int
    user_id: int
    username: str
    job_type: str
    content_type: str
    text_content: Optional[str]
    image_path: Optional[str]
    font_size: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=List[JobResponse])
def get_jobs(
    username: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """
    Query printer jobs with optional filters.

    Args:
        username: Filter by username
        start_date: Filter by start date (ISO 8601)
        end_date: Filter by end date (ISO 8601)
        status: Filter by status (pending, processing, success, failed)
    """
    query = db.query(DingJob).join(User)

    # Apply filters
    if username:
        query = query.filter(User.username == username)

    if start_date:
        query = query.filter(DingJob.created_at >= start_date)

    if end_date:
        query = query.filter(DingJob.created_at <= end_date)

    if status:
        query = query.filter(DingJob.status == status)

    # Order by created_at descending
    jobs = query.order_by(DingJob.created_at.desc()).all()

    return [
        JobResponse(
            id=job.id,
            user_id=job.user_id,
            username=job.user.username,
            job_type=job.job_type,
            content_type=job.content_type,
            text_content=job.text_content,
            image_path=job.image_path,
            font_size=job.font_size,
            status=job.status,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None
        )
        for job in jobs
    ]


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get job details by ID."""
    job = db.query(DingJob).filter(DingJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return JobResponse(
        id=job.id,
        user_id=job.user_id,
        username=job.user.username,
        job_type=job.job_type,
        content_type=job.content_type,
        text_content=job.text_content,
        image_path=job.image_path,
        font_size=job.font_size,
        status=job.status,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )


@router.get("/{job_id}/image")
def download_job_image(
    job_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Download the image file associated with a job."""
    job = db.query(DingJob).filter(DingJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if not job.image_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job has no associated image"
        )

    image_path = Path(job.image_path)
    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found"
        )

    return FileResponse(
        path=str(image_path),
        media_type="image/jpeg",
        filename=image_path.name
    )


@router.post("/{job_id}/retry", response_model=JobResponse)
def retry_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Retry a failed job."""
    job = db.query(DingJob).filter(DingJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status not in ["failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry job with status '{job.status}'"
        )

    # Reset job status
    job.status = "pending"
    job.error_message = None
    job.completed_at = None
    db.commit()

    # Process job asynchronously
    printer_service.process_job_async(job_id)

    db.refresh(job)

    return JobResponse(
        id=job.id,
        user_id=job.user_id,
        username=job.user.username,
        job_type=job.job_type,
        content_type=job.content_type,
        text_content=job.text_content,
        image_path=job.image_path,
        font_size=job.font_size,
        status=job.status,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )
