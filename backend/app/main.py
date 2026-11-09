from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sqlite3
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Job
from .schemas import JobCreate, JobOut, JobStatusUpdate, BatchJobCreate

Base.metadata.create_all(bind=engine)

# Auto-migrate SQLite columns if running with SQLite
with engine.connect() as conn:
    try:
        res = conn.execute(text("PRAGMA table_info(jobs)"))
        existing_cols = [r[1] for r in res.fetchall()]
        cols_to_add = [
            ("voice", "VARCHAR(50) DEFAULT 'heart'"),
            ("preview", "BOOLEAN DEFAULT 0"),
            ("logs", "TEXT"),
            ("metadata_json", "TEXT")
        ]
        for col, col_type in cols_to_add:
            if col not in existing_cols:
                conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col} {col_type}"))
                conn.commit()
    except Exception:
        pass

app = FastAPI(title="ShortForge AI API", version="0.2.0")

raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [x.strip() for x in raw_origins.split(",") if x.strip()]
if not allowed_origins:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

outputs_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
outputs_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")

def run_job_in_background(job_id: str, topic: str, style: str, duration: int, voice: str, preview: bool):
    """Background rendering worker for local/direct processing."""
    from .database import SessionLocal
    from worker.render import render

    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job or job.status == "cancelled":
            return
        job.status = "rendering_3d"
        db.commit()

        path, metadata = render(
            topic=topic,
            style=style,
            duration=duration,
            output_dir=str(outputs_dir),
            voice=voice,
            preview=preview
        )

        job = db.get(Job, job_id)
        if job and job.status != "cancelled":
            job.status = "completed"
            job.output_path = str(Path(path).resolve())
            job.error = None
            if isinstance(metadata, dict):
                import json
                job.metadata_json = json.dumps(metadata)
            db.commit()
    except Exception as exc:
        job = db.get(Job, job_id)
        if job and job.status != "cancelled":
            job.status = "failed"
            job.error = f"{type(exc).__name__}: {str(exc)}"
            db.commit()
    finally:
        db.close()

@app.get("/health")
def health():
    return {"ok": True, "service": "shortforge-api"}

@app.post("/api/jobs", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks, auto_render: bool = False, db: Session = Depends(get_db)):
    job_id = str(uuid4())
    job = Job(
        id=job_id,
        topic=payload.topic,
        style=payload.style,
        duration=payload.duration,
        voice=payload.voice,
        preview=payload.preview,
        status="queued"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if auto_render:
        background_tasks.add_task(
            run_job_in_background,
            job_id, payload.topic, payload.style, payload.duration, payload.voice, payload.preview
        )

    return job

@app.post("/api/jobs/batch", response_model=list[JobOut], status_code=201)
def create_batch_jobs(payload: BatchJobCreate, db: Session = Depends(get_db)):
    created = []
    for item in payload.jobs:
        job = Job(
            id=str(uuid4()),
            topic=item.topic,
            style=item.style,
            duration=item.duration,
            voice=item.voice,
            preview=item.preview,
            status="queued"
        )
        db.add(job)
        created.append(job)
    db.commit()
    for job in created:
        db.refresh(job)
    return created

@app.get("/api/jobs", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.created_at.desc()).limit(100).all()

@app.get("/api/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/jobs/{job_id}/retry", response_model=JobOut)
def retry_job(job_id: str, background_tasks: BackgroundTasks, auto_render: bool = False, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "queued"
    job.error = None
    db.commit()
    db.refresh(job)

    if auto_render:
        background_tasks.add_task(
            run_job_in_background,
            job.id, job.topic, job.style, job.duration, job.voice, job.preview
        )
    return job

@app.post("/api/jobs/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "cancelled"
    db.commit()
    db.refresh(job)
    return job

@app.get("/api/jobs/{job_id}/logs")
def get_job_logs(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "logs": job.logs or "No logs recorded yet.",
        "error": job.error,
        "output_path": job.output_path,
        "metadata": job.metadata_json
    }

@app.post("/api/jobs/{job_id}/status", response_model=JobOut)
def update_job_status(job_id: str, payload: JobStatusUpdate, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = payload.status
    if payload.output_path is not None:
        job.output_path = payload.output_path
    if payload.error is not None:
        job.error = payload.error
    if payload.logs is not None:
        job.logs = payload.logs
    if payload.metadata_json is not None:
        job.metadata_json = payload.metadata_json
    db.commit()
    db.refresh(job)
    return job
