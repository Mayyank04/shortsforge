from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import json
import sqlite3
import shutil
import subprocess
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import Base, engine, get_db, SessionLocal
from .models import Job, MinecraftProject, MinecraftCharacter, MinecraftScene, StoryHistory
from .schemas import (
    JobCreate, JobOut, JobStatusUpdate, BatchJobCreate,
    MinecraftProjectCreate, MinecraftProjectUpdate, MinecraftProjectOut,
    MinecraftCharacterCreate, MinecraftCharacterUpdate, MinecraftCharacterOut,
    MinecraftSceneOut, MinecraftSceneUpdate, StoryGenerateRequest
)

Base.metadata.create_all(bind=engine)

# Auto-seed canonical Minecraft characters if table is empty
with SessionLocal() as db:
    try:
        if db.query(MinecraftCharacter).count() == 0:
            from worker.minecraft.character_registry import get_all_canonical_characters
            chars = get_all_canonical_characters()
            for c in chars:
                row = MinecraftCharacter(
                    id=c.id,
                    name=c.name,
                    role=c.role,
                    species=c.species,
                    skin_tone=c.skin_tone,
                    clothing_primary=c.clothing_primary,
                    clothing_secondary=c.clothing_secondary,
                    hair_style=c.hair_style,
                    hair_color=c.hair_color,
                    personality=c.personality,
                    voice_preference=c.voice_preference,
                    proportions_json=json.dumps(c.proportions),
                    model_spec_json=json.dumps(c.model_spec),
                    reference_image_path=c.reference_image_path
                )
                db.add(row)
            db.commit()
    except Exception as exc:
        print("Note: Character seeding notice:", exc)

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

app = FastAPI(title="ShortForge AI API", version="0.3.0")

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

# Mount character assets static directory
char_assets_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "minecraft" / "characters"
char_assets_dir.mkdir(parents=True, exist_ok=True)
app.mount("/assets/characters", StaticFiles(directory=str(char_assets_dir)), name="character_assets")

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

def run_minecraft_project_in_background(project_id: str, preview: bool = False):
    """Background rendering worker for Minecraft story projects."""
    from worker.minecraft.pipeline import render_minecraft_video

    db = SessionLocal()
    try:
        proj = db.get(MinecraftProject, project_id)
        if not proj or proj.status == "cancelled":
            return
        proj.status = "rendering"
        db.commit()

        path, meta = render_minecraft_video(
            topic=proj.title,
            genre=proj.genre,
            duration=proj.duration,
            voice=proj.voice,
            language=proj.language,
            preview=preview,
            output_dir=str(outputs_dir)
        )

        proj = db.get(MinecraftProject, project_id)
        if proj and proj.status != "cancelled":
            proj.status = "completed"
            proj.output_path = str(Path(path).resolve())
            proj.error = None
            proj.story_json = json.dumps(meta)
            db.commit()
    except Exception as exc:
        proj = db.get(MinecraftProject, project_id)
        if proj and proj.status != "cancelled":
            proj.status = "failed"
            proj.error = f"{type(exc).__name__}: {str(exc)}"
            db.commit()
    finally:
        db.close()

@app.get("/health")
def health():
    return {"ok": True, "service": "shortforge-api"}

# -------------------------------------------------------------
# Geography / Classic Job Routes
# -------------------------------------------------------------

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

# -------------------------------------------------------------
# Minecraft Story Studio API Endpoints
# -------------------------------------------------------------

@app.post("/api/minecraft/stories/generate")
def generate_story_endpoint(payload: StoryGenerateRequest):
    from worker.minecraft.story_generator import generate_story_with_ollama_or_fallback
    story = generate_story_with_ollama_or_fallback(
        genre=payload.genre,
        idea=payload.idea,
        duration=payload.duration,
        language=payload.language,
        character_ids=payload.character_ids
    )
    return story.model_dump()

@app.post("/api/minecraft/projects", response_model=MinecraftProjectOut, status_code=201)
def create_minecraft_project(
    payload: MinecraftProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    from worker.minecraft.story_generator import generate_story_with_ollama_or_fallback
    story = generate_story_with_ollama_or_fallback(
        genre=payload.genre,
        idea=payload.custom_idea or payload.title,
        duration=payload.duration,
        language=payload.language,
        character_ids=payload.characters
    )

    proj_id = str(uuid4())
    proj = MinecraftProject(
        id=proj_id,
        title=payload.title,
        genre=payload.genre,
        duration=payload.duration,
        language=payload.language,
        voice=payload.voice,
        visual_quality=payload.visual_quality,
        status="queued" if payload.auto_render else "draft",
        viral_title=story.viral_title,
        opening_hook=story.opening_hook,
        plot_summary=story.plot_summary,
        full_script=story.full_script,
        story_json=json.dumps(story.model_dump())
    )
    db.add(proj)

    # Add 10 scenes
    for sc in story.scenes:
        actions_json = json.dumps([a.model_dump() for a in sc.character_actions])
        cam_json = json.dumps(sc.camera.model_dump())
        scene_row = MinecraftScene(
            id=str(uuid4()),
            project_id=proj_id,
            scene_number=sc.scene_number,
            duration=sc.duration,
            narration=sc.narration,
            characters_json=json.dumps(sc.characters),
            environment=sc.environment,
            time_of_day=sc.time_of_day,
            camera_json=cam_json,
            character_actions_json=actions_json,
            lighting=sc.lighting,
            atmosphere=sc.atmosphere,
            vfx_json=json.dumps(sc.effects),
            transition=sc.transition,
            image_prompt=sc.image_prompt,
            animation_prompt=sc.animation_prompt,
            audio_cues_json=json.dumps(sc.audio_cues)
        )
        db.add(scene_row)

    db.commit()
    db.refresh(proj)

    if payload.auto_render:
        background_tasks.add_task(run_minecraft_project_in_background, proj_id, preview=(payload.visual_quality == "preview"))

    return proj

@app.get("/api/minecraft/projects", response_model=list[MinecraftProjectOut])
def list_minecraft_projects(db: Session = Depends(get_db)):
    return db.query(MinecraftProject).order_by(MinecraftProject.created_at.desc()).limit(100).all()

@app.get("/api/minecraft/projects/{project_id}", response_model=MinecraftProjectOut)
def get_minecraft_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.get(MinecraftProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@app.put("/api/minecraft/projects/{project_id}", response_model=MinecraftProjectOut)
def update_minecraft_project(project_id: str, payload: MinecraftProjectUpdate, db: Session = Depends(get_db)):
    proj = db.get(MinecraftProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(proj, k, v)
    db.commit()
    db.refresh(proj)
    return proj

@app.delete("/api/minecraft/projects/{project_id}")
def delete_minecraft_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.get(MinecraftProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(proj)
    db.commit()
    return {"ok": True, "deleted_id": project_id}

@app.post("/api/minecraft/projects/{project_id}/duplicate", response_model=MinecraftProjectOut)
def duplicate_minecraft_project(project_id: str, db: Session = Depends(get_db)):
    orig = db.get(MinecraftProject, project_id)
    if not orig:
        raise HTTPException(status_code=404, detail="Project not found")

    new_id = str(uuid4())
    clone = MinecraftProject(
        id=new_id,
        title=f"{orig.title} (Copy)",
        genre=orig.genre,
        duration=orig.duration,
        language=orig.language,
        voice=orig.voice,
        visual_quality=orig.visual_quality,
        status="draft",
        viral_title=orig.viral_title,
        opening_hook=orig.opening_hook,
        plot_summary=orig.plot_summary,
        full_script=orig.full_script,
        story_json=orig.story_json
    )
    db.add(clone)

    for sc in orig.scenes:
        sc_clone = MinecraftScene(
            id=str(uuid4()),
            project_id=new_id,
            scene_number=sc.scene_number,
            duration=sc.duration,
            narration=sc.narration,
            characters_json=sc.characters_json,
            environment=sc.environment,
            time_of_day=sc.time_of_day,
            camera_json=sc.camera_json,
            character_actions_json=sc.character_actions_json,
            lighting=sc.lighting,
            atmosphere=sc.atmosphere,
            vfx_json=sc.vfx_json,
            transition=sc.transition,
            image_prompt=sc.image_prompt,
            animation_prompt=sc.animation_prompt,
            audio_cues_json=sc.audio_cues_json
        )
        db.add(sc_clone)

    db.commit()
    db.refresh(clone)
    return clone

@app.post("/api/minecraft/projects/{project_id}/render", response_model=MinecraftProjectOut)
def render_minecraft_project_endpoint(
    project_id: str,
    background_tasks: BackgroundTasks,
    preview: bool = False,
    db: Session = Depends(get_db)
):
    proj = db.get(MinecraftProject, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    proj.status = "queued"
    proj.error = None
    db.commit()
    db.refresh(proj)

    background_tasks.add_task(run_minecraft_project_in_background, project_id, preview)
    return proj

# Characters API
@app.get("/api/minecraft/characters", response_model=list[MinecraftCharacterOut])
def list_characters(db: Session = Depends(get_db)):
    return db.query(MinecraftCharacter).order_by(MinecraftCharacter.name.asc()).all()

@app.post("/api/minecraft/characters", response_model=MinecraftCharacterOut, status_code=201)
def create_character(payload: MinecraftCharacterCreate, db: Session = Depends(get_db)):
    cid = str(uuid4())
    char_row = MinecraftCharacter(
        id=cid,
        name=payload.name,
        role=payload.role,
        species=payload.species,
        skin_tone=payload.skin_tone,
        clothing_primary=payload.clothing_primary,
        clothing_secondary=payload.clothing_secondary,
        hair_style=payload.hair_style,
        hair_color=payload.hair_color,
        personality=payload.personality,
        voice_preference=payload.voice_preference,
        proportions_json=payload.proportions_json,
        model_spec_json=payload.model_spec_json
    )
    db.add(char_row)
    db.commit()
    db.refresh(char_row)

    # Generate reference image
    try:
        from worker.minecraft.metadata import CanonicalCharacter
        from worker.minecraft.character_registry import generate_character_reference_image
        c_obj = CanonicalCharacter(
            id=cid,
            name=payload.name,
            role=payload.role,
            species=payload.species,
            skin_tone=payload.skin_tone,
            clothing_primary=payload.clothing_primary,
            clothing_secondary=payload.clothing_secondary,
            hair_style=payload.hair_style,
            hair_color=payload.hair_color
        )
        ref_path = generate_character_reference_image(c_obj)
        char_row.reference_image_path = str(ref_path.resolve())
        db.commit()
        db.refresh(char_row)
    except Exception:
        pass

    return char_row

@app.get("/api/minecraft/characters/{character_id}", response_model=MinecraftCharacterOut)
def get_character(character_id: str, db: Session = Depends(get_db)):
    c = db.get(MinecraftCharacter, character_id)
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    return c

@app.put("/api/minecraft/characters/{character_id}", response_model=MinecraftCharacterOut)
def update_character(character_id: str, payload: MinecraftCharacterUpdate, db: Session = Depends(get_db)):
    c = db.get(MinecraftCharacter, character_id)
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c

@app.delete("/api/minecraft/characters/{character_id}")
def delete_character(character_id: str, db: Session = Depends(get_db)):
    c = db.get(MinecraftCharacter, character_id)
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    db.delete(c)
    db.commit()
    return {"ok": True, "deleted_id": character_id}

# Scenes API
@app.get("/api/minecraft/projects/{project_id}/scenes", response_model=list[MinecraftSceneOut])
def get_project_scenes(project_id: str, db: Session = Depends(get_db)):
    return db.query(MinecraftScene).filter(MinecraftScene.project_id == project_id).order_by(MinecraftScene.scene_number.asc()).all()

@app.put("/api/minecraft/scenes/{scene_id}", response_model=MinecraftSceneOut)
def update_scene(scene_id: str, payload: MinecraftSceneUpdate, db: Session = Depends(get_db)):
    sc = db.get(MinecraftScene, scene_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Scene not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(sc, k, v)
    db.commit()
    db.refresh(sc)
    return sc

@app.delete("/api/minecraft/scenes/{scene_id}")
def delete_scene(scene_id: str, db: Session = Depends(get_db)):
    sc = db.get(MinecraftScene, scene_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Scene not found")
    db.delete(sc)
    db.commit()
    return {"ok": True, "deleted_scene_id": scene_id}

# Unified Renders & Dashboard Stats
@app.get("/api/renders")
def list_all_renders(db: Session = Depends(get_db)):
    geo_jobs = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
    mc_projects = db.query(MinecraftProject).order_by(MinecraftProject.created_at.desc()).limit(50).all()

    unified = []
    for g in geo_jobs:
        unified.append({
            "id": g.id,
            "type": "geography",
            "title": g.topic,
            "status": g.status,
            "duration": g.duration,
            "voice": g.voice,
            "output_path": g.output_path,
            "error": g.error,
            "created_at": g.created_at.isoformat() if g.created_at else None
        })
    for m in mc_projects:
        unified.append({
            "id": m.id,
            "type": "minecraft",
            "title": m.title,
            "status": m.status,
            "duration": m.duration,
            "voice": m.voice,
            "output_path": m.output_path,
            "error": m.error,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    return sorted(unified, key=lambda x: x["created_at"] or "", reverse=True)

@app.get("/api/renders/stats")
def get_render_stats(db: Session = Depends(get_db)):
    total_geo = db.query(Job).count()
    completed_geo = db.query(Job).filter(Job.status == "completed").count()
    running_geo = db.query(Job).filter(Job.status.in_(["running", "rendering_3d", "scripting"])).count()
    failed_geo = db.query(Job).filter(Job.status == "failed").count()

    total_mc = db.query(MinecraftProject).count()
    completed_mc = db.query(MinecraftProject).filter(MinecraftProject.status == "completed").count()
    running_mc = db.query(MinecraftProject).filter(MinecraftProject.status.in_(["queued", "rendering"])).count()
    failed_mc = db.query(MinecraftProject).filter(MinecraftProject.status == "failed").count()

    return {
        "total_projects": total_geo + total_mc,
        "completed_videos": completed_geo + completed_mc,
        "processing_jobs": running_geo + running_mc,
        "failed_jobs": failed_geo + failed_mc,
        "geography_projects": total_geo,
        "minecraft_projects": total_mc
    }

@app.get("/api/settings")
def get_system_settings():
    # Diagnostics for Blender, FFmpeg, Kokoro, Ollama, Storage
    blender_ok = False
    blender_version = "Not found"
    try:
        from worker.blender_render import verify_blender_available
        _, v = verify_blender_available()
        blender_ok = True
        blender_version = v
    except Exception as e:
        blender_version = str(e)

    ffmpeg_ok = bool(shutil.which("ffmpeg"))
    kokoro_ok = False
    try:
        import kokoro
        kokoro_ok = True
    except ImportError:
        pass

    ollama_ok = False
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.0) as resp:
            ollama_ok = (resp.status == 200)
    except Exception:
        pass

    # Storage info
    total_gb, used_gb, free_gb = 0, 0, 0
    try:
        stat = shutil.disk_usage("/")
        total_gb = round(stat.total / (1024**3), 1)
        used_gb = round(stat.used / (1024**3), 1)
        free_gb = round(stat.free / (1024**3), 1)
    except Exception:
        pass

    return {
        "blender": {"installed": blender_ok, "version": blender_version},
        "ffmpeg": {"installed": ffmpeg_ok, "path": shutil.which("ffmpeg") or "Not found"},
        "kokoro": {"installed": kokoro_ok, "status": "Ready (82M weights)" if kokoro_ok else "System voice fallback"},
        "ollama": {"available": ollama_ok, "url": "http://localhost:11434"},
        "storage": {"total_gb": total_gb, "used_gb": used_gb, "free_gb": free_gb},
        "system": {"platform": os.uname().sysname if hasattr(os, "uname") else "Windows"}
    }

