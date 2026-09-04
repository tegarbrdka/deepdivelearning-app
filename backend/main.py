from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from backend.database import init_db
from backend.routers import auth, predict, admin, guest
from backend.routers import video_analysis_3m, lesson_plans
from backend.routers import evaluation


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init database
    init_db()

    # Create default admin if not exists
    from backend.database import SessionLocal
    from backend.models.db_models import User, SystemConfig, VideoAnalysisJob
    from backend.services.auth_service import hash_password
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin_user = User(
                username="admin",
                email="admin@deepdivelearning.net",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(admin_user)

        # Default system config
        defaults = {
            "confidence_threshold": "70",
            "max_video_size_mb": "500",
            "max_doc_size_mb": "50",
            "max_concurrent_jobs": "2",
        }
        for key, value in defaults.items():
            if not db.query(SystemConfig).filter(SystemConfig.key == key).first():
                db.add(SystemConfig(key=key, value=value))
        db.commit()

        # ── Startup recovery: reset stuck jobs ──────────────────────
        # Jobs left in "queued" or "processing" state from a previous
        # server run will never complete because the in-memory job_queue
        # was wiped on restart. Mark them as "failed" so users know to
        # re-submit, rather than leaving them stuck forever.
        stuck_jobs = (
            db.query(VideoAnalysisJob)
            .filter(VideoAnalysisJob.status.in_(["queued", "processing"]))
            .all()
        )
        if stuck_jobs:
            print(f"[Startup] Found {len(stuck_jobs)} stuck job(s) — marking as failed.")
            for job in stuck_jobs:
                job.status = "failed"
                job.stage = "failed"
                job.error_msg = (
                    "Server direstart saat job sedang berjalan. "
                    "Silakan unggah ulang video untuk memulai analisis baru."
                )
            db.commit()
    finally:
        db.close()

    yield


app = FastAPI(
    title="DeepDiveLearning API",
    description="Sistem Klasifikasi Video Pembelajaran & Deteksi Kualitas Dokumen",
    version="1.0.0",
    lifespan=lifespan,
)

import os
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount upload directory for static file access
Path("backend/uploads").mkdir(parents=True, exist_ok=True)
Path("backend/uploads/evidence").mkdir(parents=True, exist_ok=True)
Path("backend/uploads/video_3m").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

# Register routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(admin.router)
app.include_router(guest.router)
app.include_router(video_analysis_3m.router)
app.include_router(lesson_plans.router)
app.include_router(evaluation.router)


@app.get("/")
def root():
    return {"message": "DeepDiveLearning API v1.0.0", "docs": "/docs"}
