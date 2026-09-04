"""
FastAPI router for 3M Video Analysis endpoints.
"""
from __future__ import annotations

import os
import uuid
import csv
import io
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import (
    User,
    VideoAnalysisJob,
    VideoAnalysisResult,
    VideoFragment3M,
    EvidenceClip3M,
    TriangulationResult3M,
)
from backend.schemas.video_analysis_3m_schemas import (
    AnalysisResultResponse,
    EvidenceClipResponse,
    EvidenceClipsResponse,
    HistoryItemResponse,
    HistoryResponse,
    HeatmapResponse,
    JobStatusResponse,
    MindfulSubScores,
    MeaningfulSubScores,
    JoyfulSubScores,
    ScoresResponse,
    TalkTimeResponse,
    TimelineFragmentResponse,
    TimelineResponse,
    TriangulationItemResponse,
    TriangulationResponse,
    UploadResponse,
)
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/video-analysis", tags=["Video Analysis 3M"])

# Max upload size: 2 GB
MAX_VIDEO_SIZE_BYTES = 2 * 1024 * 1024 * 1024
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/mpeg"}
ALLOWED_RPP_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

UPLOAD_VIDEO_DIR = Path("backend/uploads/video_3m")
UPLOAD_RPP_DIR = Path("backend/uploads/video_3m/rpp")
EVIDENCE_DIR = Path("backend/uploads/evidence")


def _ensure_dirs():
    UPLOAD_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_RPP_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def _estimate_duration(file_size_bytes: int) -> float:
    """Rough estimate: ~1 min processing per 100 MB."""
    return max(1.0, round(file_size_bytes / (100 * 1024 * 1024), 1))


def _check_ownership(job: VideoAnalysisJob, current_user: User):
    """Raise 403 if user doesn't own the job and is not admin/principal."""
    if job.user_id != current_user.id and current_user.role not in ("admin", "principal"):
        raise HTTPException(status_code=403, detail="Akses ditolak.")


async def _save_upload(upload: UploadFile, dest: Path) -> int:
    """Save uploaded file to dest, return file size in bytes."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with open(dest, "wb") as f:
        while chunk := await upload.read(1024 * 1024):  # 1 MB chunks
            size += len(chunk)
            if size > MAX_VIDEO_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="Ukuran file melebihi batas 2 GB.",
                )
            f.write(chunk)
    return size


async def _enqueue_job(
    job_id: str,
    video_path: str,
    rpp_path: Optional[str],
    background_tasks: BackgroundTasks,
):
    """Enqueue the pipeline as a background task."""
    from backend.ai.video_3m.job_queue import job_queue
    await job_queue.enqueue(job_id, video_path, rpp_path, background_tasks)


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a video for 3M analysis (no RPP)."""
    _ensure_dirs()

    if video.content_type not in ALLOWED_VIDEO_TYPES and not (
        video.filename or ""
    ).lower().endswith(".mp4"):
        raise HTTPException(
            status_code=400,
            detail="Format video tidak didukung. Harap unggah file MP4.",
        )

    job_id = str(uuid.uuid4())
    dest = UPLOAD_VIDEO_DIR / f"{job_id}_{video.filename}"
    file_size = await _save_upload(video, dest)

    job = VideoAnalysisJob(
        job_id=job_id,
        user_id=current_user.id,
        video_path=str(dest),
        video_name=video.filename,
        status="queued",
        progress=0.0,
    )
    db.add(job)
    db.commit()

    await _enqueue_job(job_id, str(dest), None, background_tasks)

    return UploadResponse(
        job_id=job_id,
        status="queued",
        message="Video berhasil diunggah. Analisis sedang diproses.",
        estimated_duration_min=_estimate_duration(file_size),
        rpp_uploaded=False,
    )


# ---------------------------------------------------------------------------
# POST /upload-with-rpp
# ---------------------------------------------------------------------------

@router.post("/upload-with-rpp", response_model=UploadResponse, status_code=202)
async def upload_video_with_rpp(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    rpp: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a video + RPP document for 3M analysis with triangulation."""
    _ensure_dirs()

    if video.content_type not in ALLOWED_VIDEO_TYPES and not (
        video.filename or ""
    ).lower().endswith(".mp4"):
        raise HTTPException(
            status_code=400,
            detail="Format video tidak didukung. Harap unggah file MP4.",
        )

    rpp_ext = Path(rpp.filename or "").suffix.lower()
    if rpp_ext not in (".pdf", ".docx", ".doc"):
        raise HTTPException(
            status_code=400,
            detail="Format RPP tidak didukung. Harap unggah file PDF atau DOCX.",
        )

    job_id = str(uuid.uuid4())
    video_dest = UPLOAD_VIDEO_DIR / f"{job_id}_{video.filename}"
    rpp_dest = UPLOAD_RPP_DIR / f"{job_id}_{rpp.filename}"

    file_size = await _save_upload(video, video_dest)
    await _save_upload(rpp, rpp_dest)

    job = VideoAnalysisJob(
        job_id=job_id,
        user_id=current_user.id,
        video_path=str(video_dest),
        video_name=video.filename,
        rpp_path=str(rpp_dest),
        status="queued",
        progress=0.0,
    )
    db.add(job)
    db.commit()

    await _enqueue_job(job_id, str(video_dest), str(rpp_dest), background_tasks)

    return UploadResponse(
        job_id=job_id,
        status="queued",
        message="Video dan RPP berhasil diunggah. Analisis sedang diproses.",
        estimated_duration_min=_estimate_duration(file_size),
        rpp_uploaded=True,
    )


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        stage=job.stage,
        progress=job.progress or 0.0,
        video_name=job.video_name,
        error_msg=job.error_msg,
        created_at=job.created_at,
    )


# ---------------------------------------------------------------------------
# GET /results/{job_id}
# ---------------------------------------------------------------------------

@router.get("/results/{job_id}", response_model=AnalysisResultResponse)
def get_results(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    if job.status != "complete":
        raise HTTPException(
            status_code=400,
            detail=f"Analisis belum selesai. Status: {job.status}",
        )

    result = db.query(VideoAnalysisResult).filter(
        VideoAnalysisResult.job_id == job_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Hasil analisis tidak ditemukan.")

    has_triangulation = (
        db.query(TriangulationResult3M)
        .filter(TriangulationResult3M.job_id == job_id)
        .first()
    ) is not None

    # Compute deviation for talk time
    teacher_pct = result.teacher_talk_pct or 0.0
    student_pct = result.student_talk_pct or 0.0
    teacher_dev = max(0.0, teacher_pct - 40.0) if teacher_pct > 40.0 else max(0.0, 30.0 - teacher_pct)
    student_dev = max(0.0, student_pct - 70.0) if student_pct > 70.0 else max(0.0, 60.0 - student_pct)
    deviation = round((teacher_dev + student_dev) / 2, 2)

    return AnalysisResultResponse(
        job_id=job_id,
        video_name=job.video_name,
        scores=ScoresResponse(
            mindful=result.mindful_score or 0.0,
            meaningful=result.meaningful_score or 0.0,
            joyful=result.joyful_score or 0.0,
            overall=result.overall_3m_score or 0.0,
            mindful_sub=MindfulSubScores(
                gaze_score=result.gaze_score or 0.0,
                posture_score=result.posture_score or 0.0,
                silence_quality_score=result.silence_quality_score or 0.0,
            ),
            meaningful_sub=MeaningfulSubScores(
                seating_score=result.seating_score or 0.0,
                talk_time_score=result.talk_time_score or 0.0,
                question_type_score=result.question_type_score or 0.0,
                teacher_movement_score=result.teacher_movement_score or 0.0,
            ),
            joyful_sub=JoyfulSubScores(
                expression_score=result.expression_score or 0.0,
                acoustic_score=result.acoustic_score or 0.0,
                collaboration_score=result.collaboration_score or 0.0,
                risk_taking_score=result.risk_taking_score or 0.0,
            ),
        ),
        talk_time=TalkTimeResponse(
            teacher_pct=teacher_pct,
            student_pct=student_pct,
            silence_pct=result.silence_pct or 0.0,
            meets_dl_standard=result.meets_dl_standard or False,
            deviation=deviation,
        ),
        recommendations=result.recommendations or [],
        has_triangulation=has_triangulation,
        created_at=result.created_at,
        aha_moments=result.aha_moments or [],
        laughter_events=result.laughter_events or [],
        applause_events=result.applause_events or [],
        seating_transitions=result.seating_transitions or [],
    )


# ---------------------------------------------------------------------------
# GET /timeline/{job_id}
# ---------------------------------------------------------------------------

@router.get("/timeline/{job_id}", response_model=TimelineResponse)
def get_timeline(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    fragments = (
        db.query(VideoFragment3M)
        .filter(VideoFragment3M.job_id == job_id)
        .order_by(VideoFragment3M.start_sec)
        .all()
    )

    items = []
    for f in fragments:
        start_min = int(f.start_sec // 60)
        start_s = int(f.start_sec % 60)
        end_min = int(f.end_sec // 60)
        end_s = int(f.end_sec % 60)
        items.append(
            TimelineFragmentResponse(
                index=f.fragment_index,
                start_sec=f.start_sec,
                end_sec=f.end_sec,
                label=f"{start_min}:{start_s:02d} – {end_min}:{end_s:02d}",
                mindful=f.mindful_score or 0.0,
                meaningful=f.meaningful_score or 0.0,
                joyful=f.joyful_score or 0.0,
                seating_formation=f.seating_formation,
                active_zone_ratio=f.active_zone_ratio,
                teacher_talk_pct=f.teacher_talk_pct,
                student_talk_pct=f.student_talk_pct,
            )
        )

    return TimelineResponse(job_id=job_id, fragments=items)


# ---------------------------------------------------------------------------
# GET /heatmap/{job_id}
# ---------------------------------------------------------------------------

@router.get("/heatmap/{job_id}", response_model=HeatmapResponse)
def get_heatmap(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    result = db.query(VideoAnalysisResult).filter(
        VideoAnalysisResult.job_id == job_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Hasil analisis tidak ditemukan.")

    heatmap = result.heatmap_data or []
    grid_height = len(heatmap)
    grid_width = len(heatmap[0]) if heatmap else 0

    return HeatmapResponse(
        job_id=job_id,
        grid_width=grid_width,
        grid_height=grid_height,
        heatmap=heatmap,
        clusters=[],  # clusters stored separately if needed
        discussion_groups_count=result.discussion_groups_count or 0,
    )


# ---------------------------------------------------------------------------
# GET /evidence-clips/{job_id}
# ---------------------------------------------------------------------------

@router.get("/evidence-clips/{job_id}", response_model=EvidenceClipsResponse)
def get_evidence_clips(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    clips = (
        db.query(EvidenceClip3M)
        .filter(EvidenceClip3M.job_id == job_id)
        .order_by(EvidenceClip3M.clip_type, EvidenceClip3M.score.desc())
        .all()
    )

    items = []
    for c in clips:
        clip_url = f"/uploads/evidence/{job_id}/{Path(c.clip_path).name}" if c.clip_path else ""
        items.append(
            EvidenceClipResponse(
                id=c.id,
                clip_name=c.clip_name,
                clip_url=clip_url,
                start_sec=c.start_sec or 0.0,
                end_sec=c.end_sec or 0.0,
                clip_type=c.clip_type or "",
                aspect=c.aspect or "",
                description=c.description,
                score=c.score or 0.0,
            )
        )

    return EvidenceClipsResponse(job_id=job_id, clips=items)


# ---------------------------------------------------------------------------
# GET /triangulation/{job_id}
# ---------------------------------------------------------------------------

@router.get("/triangulation/{job_id}", response_model=TriangulationResponse)
def get_triangulation(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    tri = db.query(TriangulationResult3M).filter(
        TriangulationResult3M.job_id == job_id
    ).first()
    if not tri:
        raise HTTPException(
            status_code=404,
            detail="Tidak ada data triangulasi. RPP mungkin tidak diunggah.",
        )

    items = [
        TriangulationItemResponse(
            activity=it.get("activity", ""),
            planned=it.get("planned", False),
            detected=it.get("detected", False),
            status=it.get("status", "not_detected"),
            evidence=it.get("evidence"),
            recommendation=it.get("recommendation"),
        )
        for it in (tri.items or [])
    ]

    return TriangulationResponse(
        job_id=job_id,
        alignment_score=tri.alignment_score or 0.0,
        items=items,
    )


# ---------------------------------------------------------------------------
# POST /jobs/{job_id}/retry
# ---------------------------------------------------------------------------

@router.post("/jobs/{job_id}/retry", response_model=JobStatusResponse)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-queue a failed job without re-uploading the video."""
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    if job.status not in ("failed",):
        raise HTTPException(
            status_code=400,
            detail=f"Hanya job dengan status 'failed' yang bisa di-retry. Status saat ini: {job.status}",
        )

    if not job.video_path or not Path(job.video_path).exists():
        raise HTTPException(
            status_code=400,
            detail="File video tidak ditemukan di server. Silakan unggah ulang.",
        )

    # Reset job state
    job.status = "queued"
    job.stage = None
    job.progress = 0.0
    job.error_msg = None
    job.completed_at = None
    db.commit()

    await _enqueue_job(job_id, job.video_path, job.rpp_path, background_tasks)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        stage=job.stage,
        progress=0.0,
        video_name=job.video_name,
        error_msg=None,
        created_at=job.created_at,
    )


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------

@router.get("/history", response_model=HistoryResponse)
def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(VideoAnalysisJob)

    # Role-based filtering
    if current_user.role not in ("admin", "principal"):
        query = query.filter(VideoAnalysisJob.user_id == current_user.id)

    if status:
        query = query.filter(VideoAnalysisJob.status == status)

    total = query.count()
    jobs = (
        query.order_by(VideoAnalysisJob.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = []
    for job in jobs:
        result = db.query(VideoAnalysisResult).filter(
            VideoAnalysisResult.job_id == job.job_id
        ).first()
        items.append(
            HistoryItemResponse(
                job_id=job.job_id,
                video_name=job.video_name,
                status=job.status,
                mindful_score=result.mindful_score if result else None,
                meaningful_score=result.meaningful_score if result else None,
                joyful_score=result.joyful_score if result else None,
                overall_3m_score=result.overall_3m_score if result else None,
                teacher_talk_pct=result.teacher_talk_pct if result else None,
                student_talk_pct=result.student_talk_pct if result else None,
                created_at=job.created_at,
            )
        )

    return HistoryResponse(total=total, page=page, limit=limit, items=items)


# ---------------------------------------------------------------------------
# GET /export/{job_id}/csv
# ---------------------------------------------------------------------------

@router.get("/export/{job_id}/csv")
def export_csv(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    result = db.query(VideoAnalysisResult).filter(
        VideoAnalysisResult.job_id == job_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Hasil analisis tidak ditemukan.")

    tri = db.query(TriangulationResult3M).filter(
        TriangulationResult3M.job_id == job_id
    ).first()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    headers = [
        "job_id", "video_name", "mindful_score", "meaningful_score",
        "joyful_score", "overall_3m_score", "teacher_talk_pct",
        "student_talk_pct", "meets_dl_standard", "created_at",
    ]
    if tri:
        headers.append("alignment_score")
    writer.writerow(headers)

    # Data row
    row = [
        job.job_id,
        job.video_name or "",
        result.mindful_score or 0.0,
        result.meaningful_score or 0.0,
        result.joyful_score or 0.0,
        result.overall_3m_score or 0.0,
        result.teacher_talk_pct or 0.0,
        result.student_talk_pct or 0.0,
        result.meets_dl_standard or False,
        result.created_at.isoformat() if result.created_at else "",
    ]
    if tri:
        row.append(tri.alignment_score or 0.0)
    writer.writerow(row)

    output.seek(0)
    filename = f"analisis_3m_{job_id[:8]}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# GET /export/{job_id}/pdf
# ---------------------------------------------------------------------------

@router.get("/export/{job_id}/pdf")
def export_pdf(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    _check_ownership(job, current_user)

    result = db.query(VideoAnalysisResult).filter(
        VideoAnalysisResult.job_id == job_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Hasil analisis tidak ditemukan.")

    tri = db.query(TriangulationResult3M).filter(
        TriangulationResult3M.job_id == job_id
    ).first()

    try:
        from fpdf import FPDF
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Library PDF (fpdf2) tidak tersedia di server.",
        )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Laporan Analisis Video 3M", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Video: {job.video_name or job_id}", ln=True)
    pdf.cell(0, 8, f"Tanggal: {result.created_at.strftime('%d %B %Y') if result.created_at else '-'}", ln=True)
    pdf.ln(4)

    # Scores
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Skor 3M", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"  Mindful   : {result.mindful_score or 0:.1f}/100", ln=True)
    pdf.cell(0, 7, f"  Meaningful: {result.meaningful_score or 0:.1f}/100", ln=True)
    pdf.cell(0, 7, f"  Joyful    : {result.joyful_score or 0:.1f}/100", ln=True)
    pdf.cell(0, 7, f"  Overall   : {result.overall_3m_score or 0:.1f}/100", ln=True)
    pdf.ln(4)

    # Talk time
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Distribusi Waktu Bicara", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"  Guru   : {result.teacher_talk_pct or 0:.1f}%", ln=True)
    pdf.cell(0, 7, f"  Siswa  : {result.student_talk_pct or 0:.1f}%", ln=True)
    pdf.cell(0, 7, f"  Hening : {result.silence_pct or 0:.1f}%", ln=True)
    meets = "Ya" if result.meets_dl_standard else "Tidak"
    pdf.cell(0, 7, f"  Memenuhi Standar DL: {meets}", ln=True)
    pdf.ln(4)

    # Recommendations
    if result.recommendations:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Rekomendasi", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for rec in result.recommendations:
            if isinstance(rec, dict):
                title = rec.get("title")
                desc = rec.get("description") or rec.get("text")
                if title and desc:
                    text = f"{title}: {desc}"
                else:
                    text = title or desc or str(rec)
            else:
                text = str(rec)
            pdf.multi_cell(0, 6, f"  - {text}")
            pdf.set_x(10)
        pdf.ln(4)

    # Triangulation
    if tri and tri.items:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, f"Triangulasi RPP (Skor Keselarasan: {tri.alignment_score or 0:.1f}%)", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for it in tri.items:
            status_label = {"success": "Sesuai", "misalignment": "Tidak Sesuai", "not_detected": "Tidak Terdeteksi"}.get(
                it.get("status", ""), it.get("status", "")
            )
            pdf.cell(0, 6, f"  [{status_label}] {it.get('activity', '')}", ln=True)
            if it.get("recommendation"):
                pdf.multi_cell(0, 5, f"    -> {it['recommendation']}")
                pdf.set_x(10)

    pdf_bytes = pdf.output()
    filename = f"laporan_3m_{job_id[:8]}.pdf"
    return StreamingResponse(
        iter([bytes(pdf_bytes)]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
