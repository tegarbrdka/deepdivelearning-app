"""
FastAPI router for lesson plan (RPP) upload and parsing.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import LessonPlan3M, User
from backend.schemas.video_analysis_3m_schemas import (
    LessonPlanUploadResponse,
    PlannedActivityResponse,
)
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/lesson-plans", tags=["Lesson Plans"])

UPLOAD_RPP_DIR = Path("backend/uploads/video_3m/rpp")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


@router.post("/upload", response_model=LessonPlanUploadResponse)
async def upload_lesson_plan(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and parse an RPP (lesson plan) document.
    Returns the list of detected planned activities.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format file tidak didukung: {ext}. Harap unggah file PDF atau DOCX.",
        )

    UPLOAD_RPP_DIR.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    dest = UPLOAD_RPP_DIR / f"{file_id}_{file.filename}"

    # Save file
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File kosong atau tidak dapat dibaca.")

    with open(dest, "wb") as f:
        f.write(content)

    # Parse RPP
    try:
        from backend.ai.video_3m.triangulation.rpp_parser import RPPParser
        lesson_plan = RPPParser().parse(str(dest))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Dokumen tidak dapat diproses: {exc}",
        )

    # Persist to DB
    parsed_data = {
        "activities": [
            {
                "activity_type": a.activity_type,
                "description": a.description,
                "planned_duration_min": a.planned_duration_min,
            }
            for a in lesson_plan.activities
        ],
        "raw_text_length": len(lesson_plan.raw_text),
    }

    record = LessonPlan3M(
        user_id=current_user.id,
        file_path=str(dest),
        file_name=file.filename,
        parsed_data=parsed_data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    activities = [
        PlannedActivityResponse(
            activity_type=a.activity_type,
            description=a.description,
            planned_duration_min=a.planned_duration_min,
        )
        for a in lesson_plan.activities
    ]

    return LessonPlanUploadResponse(
        lesson_plan_id=record.id,
        file_name=file.filename or "",
        activities=activities,
    )
