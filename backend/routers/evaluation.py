"""
FastAPI router for evaluation endpoints.
Admin-only: upload ground truth, run benchmarks, view reports.
"""
from __future__ import annotations

import json
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import (
    User,
    VideoAnalysisJob,
    VideoFragment3M,
)
from backend.models.ground_truth_models import (
    EvaluationReport as EvaluationReportModel,
    GroundTruthAnnotation,
)
from backend.schemas.annotation_schemas import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationsListResponse,
    BulkAnnotationUpload,
    EvaluationReportResponse,
)
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


def _require_admin(user: User):
    if user.role not in ("admin", "principal"):
        raise HTTPException(status_code=403, detail="Hanya admin yang dapat mengakses fitur evaluasi.")


# ---------------------------------------------------------------------------
# POST /annotations  — upload single annotation
# ---------------------------------------------------------------------------

@router.post("/annotations", response_model=AnnotationResponse)
def create_annotation(
    data: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a ground truth annotation for a specific fragment."""
    _require_admin(current_user)

    # Verify job exists
    job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.job_id == data.job_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{data.job_id}' tidak ditemukan.")

    ann = GroundTruthAnnotation(
        job_id=data.job_id,
        fragment_index=data.fragment_index,
        annotator_name=data.annotator_name,
        gaze_on_task_ratio=data.gaze_on_task_ratio,
        posture_engaged_ratio=data.posture_engaged_ratio,
        mindful_score_gt=data.mindful_score_gt,
        seating_formation=data.seating_formation,
        teacher_in_active_zone=data.teacher_in_active_zone,
        teacher_talk_pct_gt=data.teacher_talk_pct_gt,
        meaningful_score_gt=data.meaningful_score_gt,
        positive_expression_ratio=data.positive_expression_ratio,
        hand_raise_count=data.hand_raise_count,
        joyful_score_gt=data.joyful_score_gt,
        overall_focus_score=data.overall_focus_score,
        overall_comfort_score=data.overall_comfort_score,
        overall_3m_score_gt=data.overall_3m_score_gt,
        notes=data.notes,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ann


# ---------------------------------------------------------------------------
# POST /annotations/bulk  — upload multiple annotations (JSON)
# ---------------------------------------------------------------------------

@router.post("/annotations/bulk")
def create_bulk_annotations(
    data: BulkAnnotationUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload multiple ground truth annotations at once."""
    _require_admin(current_user)

    saved = 0
    errors = []

    for i, ann_data in enumerate(data.annotations):
        try:
            job = db.query(VideoAnalysisJob).filter(
                VideoAnalysisJob.job_id == ann_data.job_id
            ).first()
            if not job:
                errors.append(f"[{i}] Job '{ann_data.job_id}' tidak ditemukan.")
                continue

            ann = GroundTruthAnnotation(
                job_id=ann_data.job_id,
                fragment_index=ann_data.fragment_index,
                annotator_name=ann_data.annotator_name,
                gaze_on_task_ratio=ann_data.gaze_on_task_ratio,
                posture_engaged_ratio=ann_data.posture_engaged_ratio,
                mindful_score_gt=ann_data.mindful_score_gt,
                seating_formation=ann_data.seating_formation,
                teacher_in_active_zone=ann_data.teacher_in_active_zone,
                teacher_talk_pct_gt=ann_data.teacher_talk_pct_gt,
                meaningful_score_gt=ann_data.meaningful_score_gt,
                positive_expression_ratio=ann_data.positive_expression_ratio,
                hand_raise_count=ann_data.hand_raise_count,
                joyful_score_gt=ann_data.joyful_score_gt,
                overall_focus_score=ann_data.overall_focus_score,
                overall_comfort_score=ann_data.overall_comfort_score,
                overall_3m_score_gt=ann_data.overall_3m_score_gt,
                notes=ann_data.notes,
            )
            db.add(ann)
            saved += 1
        except Exception as e:
            errors.append(f"[{i}] Error: {str(e)}")

    db.commit()

    return {
        "message": f"Berhasil menyimpan {saved} anotasi.",
        "saved": saved,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# POST /annotations/csv  — upload CSV file
# ---------------------------------------------------------------------------

@router.post("/annotations/csv")
async def upload_annotations_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload ground truth annotations from a CSV file."""
    _require_admin(current_user)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat CSV.")

    import csv
    import io

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    saved = 0
    errors = []

    for i, row in enumerate(reader):
        try:
            ann = GroundTruthAnnotation(
                job_id=row.get("job_id", "").strip(),
                fragment_index=int(row.get("fragment_index", 0)),
                annotator_name=row.get("annotator_name", "").strip(),
                gaze_on_task_ratio=_parse_float(row.get("gaze_on_task_ratio")),
                posture_engaged_ratio=_parse_float(row.get("posture_engaged_ratio")),
                mindful_score_gt=_parse_float(row.get("mindful_score_gt")),
                seating_formation=row.get("seating_formation", "").strip() or None,
                teacher_in_active_zone=_parse_bool(row.get("teacher_in_active_zone")),
                teacher_talk_pct_gt=_parse_float(row.get("teacher_talk_pct_gt")),
                meaningful_score_gt=_parse_float(row.get("meaningful_score_gt")),
                positive_expression_ratio=_parse_float(row.get("positive_expression_ratio")),
                hand_raise_count=_parse_int(row.get("hand_raise_count")),
                joyful_score_gt=_parse_float(row.get("joyful_score_gt")),
                overall_focus_score=_parse_float(row.get("overall_focus_score")),
                overall_comfort_score=_parse_float(row.get("overall_comfort_score")),
                overall_3m_score_gt=_parse_float(row.get("overall_3m_score_gt")),
                notes=row.get("notes", "").strip() or None,
            )

            if not ann.job_id or not ann.annotator_name:
                errors.append(f"[Row {i+2}] job_id dan annotator_name wajib diisi.")
                continue

            db.add(ann)
            saved += 1
        except Exception as e:
            errors.append(f"[Row {i+2}] Error: {str(e)}")

    db.commit()

    return {
        "message": f"Berhasil menyimpan {saved} anotasi dari CSV.",
        "saved": saved,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# GET /annotations/{job_id}
# ---------------------------------------------------------------------------

@router.get("/annotations/{job_id}", response_model=AnnotationsListResponse)
def get_annotations(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all ground truth annotations for a job."""
    _require_admin(current_user)

    annotations = (
        db.query(GroundTruthAnnotation)
        .filter(GroundTruthAnnotation.job_id == job_id)
        .order_by(GroundTruthAnnotation.fragment_index, GroundTruthAnnotation.annotator_name)
        .all()
    )

    return AnnotationsListResponse(
        job_id=job_id,
        total=len(annotations),
        annotations=[AnnotationResponse.model_validate(a) for a in annotations],
    )


# ---------------------------------------------------------------------------
# POST /benchmark/{job_id}  — run evaluation for a single job
# ---------------------------------------------------------------------------

@router.post("/benchmark/{job_id}")
def run_benchmark(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run evaluation benchmark for a completed job with ground truth annotations."""
    _require_admin(current_user)

    # Verify job exists and is complete
    job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.job_id == job_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    if job.status != "complete":
        raise HTTPException(status_code=400, detail="Job belum selesai diproses.")

    # Check annotations exist
    ann_count = db.query(GroundTruthAnnotation).filter(
        GroundTruthAnnotation.job_id == job_id
    ).count()
    if ann_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Belum ada anotasi ground truth untuk job ini. Silakan upload terlebih dahulu.",
        )

    # Run evaluation
    from backend.ai.video_3m.evaluation.evaluation_engine import EvaluationEngine
    from backend.ai.video_3m.evaluation.report_generator import ReportGenerator

    engine = EvaluationEngine(db)
    report = engine.evaluate_job(job_id)

    # Generate visualizations
    generator = ReportGenerator()
    report_id = f"{job_id[:8]}_{int(time.time())}"
    files = generator.generate_full_report(report, report_id)

    # Save to DB
    report_record = EvaluationReportModel(
        job_id=job_id,
        report_type="single",
        confusion_matrices=[
            {
                "component": cm.component,
                "labels": cm.labels,
                "matrix": cm.matrix,
                "accuracy": cm.accuracy,
                "precision": cm.precision,
                "recall": cm.recall,
                "f1_score": cm.f1_score,
                "cohen_kappa": cm.cohen_kappa,
            }
            for cm in report.confusion_matrices
        ],
        classification_reports=[
            {"component": cm.component, "report": cm.classification_report}
            for cm in report.confusion_matrices
        ],
        correlation_metrics=[
            {
                "component": c.component,
                "pearson_r": c.pearson_r,
                "pearson_p": c.pearson_p,
                "spearman_rho": c.spearman_rho,
                "mae": c.mae,
                "rmse": c.rmse,
                "n_samples": c.n_samples,
            }
            for c in report.correlations
        ],
        inter_rater_metrics=[
            {
                "component": ir.component,
                "n_raters": ir.n_raters,
                "cohens_kappa": ir.cohens_kappa,
                "icc": ir.icc,
            }
            for ir in report.inter_rater
        ],
        total_fragments_evaluated=report.total_fragments,
        total_annotators=report.total_annotators,
        full_report=report.to_dict(),
    )
    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    return {
        "id": report_record.id,
        "job_id": job_id,
        "total_fragments": report.total_fragments,
        "total_annotators": report.total_annotators,
        "summary": {
            "mean_pearson_r": report.mean_pearson_r,
            "mean_f1": report.mean_f1,
            "mean_kappa": report.mean_kappa,
        },
        "confusion_matrices": len(report.confusion_matrices),
        "correlations": len(report.correlations),
        "files": files,
    }


# ---------------------------------------------------------------------------
# POST /benchmark/batch  — run evaluation for multiple jobs
# ---------------------------------------------------------------------------

@router.post("/benchmark/batch")
def run_batch_benchmark(
    job_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run evaluation benchmark across multiple completed jobs."""
    _require_admin(current_user)

    from backend.ai.video_3m.evaluation.evaluation_engine import EvaluationEngine
    from backend.ai.video_3m.evaluation.report_generator import ReportGenerator

    engine = EvaluationEngine(db)
    report = engine.evaluate_batch(job_ids)

    generator = ReportGenerator()
    report_id = f"batch_{int(time.time())}"
    files = generator.generate_full_report(report, report_id)

    # Save to DB
    report_record = EvaluationReportModel(
        report_type="batch",
        total_fragments_evaluated=report.total_fragments,
        total_annotators=report.total_annotators,
        full_report=report.to_dict(),
    )
    db.add(report_record)
    db.commit()

    return {
        "id": report_record.id,
        "total_fragments": report.total_fragments,
        "total_annotators": report.total_annotators,
        "summary": {
            "mean_pearson_r": report.mean_pearson_r,
            "mean_f1": report.mean_f1,
            "mean_kappa": report.mean_kappa,
        },
        "files": files,
    }


# ---------------------------------------------------------------------------
# GET /report/{job_id}  — get saved evaluation report
# ---------------------------------------------------------------------------

@router.get("/report/{job_id}")
def get_evaluation_report(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the most recent evaluation report for a job."""
    _require_admin(current_user)

    report = (
        db.query(EvaluationReportModel)
        .filter(EvaluationReportModel.job_id == job_id)
        .order_by(EvaluationReportModel.created_at.desc())
        .first()
    )

    if not report:
        raise HTTPException(status_code=404, detail="Laporan evaluasi belum tersedia untuk job ini.")

    return {
        "id": report.id,
        "job_id": report.job_id,
        "report_type": report.report_type,
        "total_fragments": report.total_fragments_evaluated,
        "total_annotators": report.total_annotators,
        "confusion_matrices": report.confusion_matrices,
        "correlation_metrics": report.correlation_metrics,
        "inter_rater_metrics": report.inter_rater_metrics,
        "processing_times": report.processing_times,
        "created_at": report.created_at,
    }


# ---------------------------------------------------------------------------
# GET /template/{job_id}  — download annotation template
# ---------------------------------------------------------------------------

@router.get("/template/{job_id}")
def download_template(
    job_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download an annotation template for a specific job."""
    _require_admin(current_user)

    job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.job_id == job_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")

    fragments = (
        db.query(VideoFragment3M)
        .filter(VideoFragment3M.job_id == job_id)
        .order_by(VideoFragment3M.fragment_index)
        .all()
    )

    template = {
        "metadata": {
            "job_id": job_id,
            "video_name": job.video_name,
            "total_fragments": len(fragments),
            "instructions": (
                "Isi setiap fragment dengan observasi Anda. "
                "Gunakan skala 0.0-1.0 untuk rasio, 0-100 untuk skor. "
                "Untuk seating_formation, pilih: rows / groups / circle."
            ),
        },
        "annotations": [],
    }

    for frag in fragments:
        start_min = int(frag.start_sec // 60)
        start_s = int(frag.start_sec % 60)
        end_min = int(frag.end_sec // 60)
        end_s = int(frag.end_sec % 60)

        template["annotations"].append({
            "job_id": job_id,
            "fragment_index": frag.fragment_index,
            "time_range": f"{start_min}:{start_s:02d} – {end_min}:{end_s:02d}",
            "annotator_name": "Observer A",
            "gaze_on_task_ratio": None,
            "posture_engaged_ratio": None,
            "mindful_score_gt": None,
            "seating_formation": None,
            "teacher_in_active_zone": None,
            "teacher_talk_pct_gt": None,
            "meaningful_score_gt": None,
            "positive_expression_ratio": None,
            "hand_raise_count": None,
            "joyful_score_gt": None,
            "overall_focus_score": None,
            "overall_comfort_score": None,
            "overall_3m_score_gt": None,
            "notes": "",
        })

    if format == "csv":
        import csv
        import io
        from fastapi.responses import StreamingResponse

        output = io.StringIO()
        fieldnames = list(template["annotations"][0].keys()) if template["annotations"] else []
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for ann in template["annotations"]:
            writer.writerow(ann)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=template_{job_id[:8]}.csv"
            },
        )

    return template


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_float(val) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _parse_int(val) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _parse_bool(val) -> Optional[bool]:
    if val is None or val == "":
        return None
    if isinstance(val, bool):
        return val
    val_str = str(val).lower().strip()
    if val_str in ("true", "1", "yes"):
        return True
    if val_str in ("false", "0", "no"):
        return False
    return None
