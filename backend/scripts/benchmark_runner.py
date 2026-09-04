"""
Benchmark Runner — CLI script for evaluating the 3M CV pipeline
against ground truth annotations.

Usage:
    # Run with ground truth annotations file:
    python -m backend.scripts.benchmark_runner --input annotations.json --output eval_results/

    # Run using DB annotations for specific jobs:
    python -m backend.scripts.benchmark_runner --job-ids job1,job2 --output eval_results/

    # Generate sample annotation template:
    python -m backend.scripts.benchmark_runner --generate-template --job-id <job_id> --output template.json

Ground Truth JSON Format:
    See generate_template() for the exact structure.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional


def main():
    parser = argparse.ArgumentParser(
        description="3M Pipeline Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # ── evaluate ──────────────────────────────────────────────────────
    eval_parser = subparsers.add_parser("evaluate", help="Run evaluation")
    eval_parser.add_argument(
        "--input", "-i",
        help="Path to ground truth annotations JSON file",
    )
    eval_parser.add_argument(
        "--job-ids",
        help="Comma-separated job IDs to evaluate (uses DB annotations)",
    )
    eval_parser.add_argument(
        "--output", "-o",
        default="backend/uploads/evaluation_reports/benchmark",
        help="Output directory for reports",
    )

    # ── template ──────────────────────────────────────────────────────
    tmpl_parser = subparsers.add_parser("template", help="Generate annotation template")
    tmpl_parser.add_argument(
        "--job-id",
        help="Job ID to generate template for (reads fragments from DB)",
    )
    tmpl_parser.add_argument(
        "--output", "-o",
        default="annotation_template.json",
        help="Output path for template file",
    )
    tmpl_parser.add_argument(
        "--csv",
        action="store_true",
        help="Also generate CSV template",
    )

    # ── benchmark-timing ──────────────────────────────────────────────
    time_parser = subparsers.add_parser("timing", help="Run timing benchmark")
    time_parser.add_argument(
        "--video", "-v",
        required=True,
        help="Path to video file for timing benchmark",
    )
    time_parser.add_argument(
        "--output", "-o",
        default="backend/uploads/evaluation_reports/timing",
        help="Output directory",
    )

    args = parser.parse_args()

    if args.command == "evaluate":
        run_evaluate(args)
    elif args.command == "template":
        run_generate_template(args)
    elif args.command == "timing":
        run_timing_benchmark(args)
    else:
        parser.print_help()


# ── Evaluate ──────────────────────────────────────────────────────────────────

def run_evaluate(args):
    """Run full evaluation against ground truth."""
    print("=" * 60)
    print("  3M Pipeline Evaluation Benchmark")
    print("=" * 60)

    if args.input:
        # Load from JSON file
        print(f"\n📂 Loading annotations from: {args.input}")
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        run_evaluate_from_file(data, args.output)

    elif args.job_ids:
        # Load from database
        job_ids = [j.strip() for j in args.job_ids.split(",")]
        print(f"\n📂 Loading annotations from DB for {len(job_ids)} job(s)")
        run_evaluate_from_db(job_ids, args.output)
    else:
        print("❌ Please provide --input (JSON file) or --job-ids")
        sys.exit(1)


def run_evaluate_from_file(data: dict, output_dir: str):
    """Evaluate using annotations from a JSON file."""
    from backend.ai.video_3m.evaluation.evaluation_engine import EvaluationEngine
    from backend.ai.video_3m.evaluation.report_generator import ReportGenerator

    annotations = data.get("annotations", [])
    if not annotations:
        print("❌ No annotations found in input file")
        return

    # Group by job_id
    job_ids = list(set(a.get("job_id", "") for a in annotations))
    print(f"   Found {len(annotations)} annotations for {len(job_ids)} job(s)")

    # Load from DB to pair with CV results
    from backend.database import SessionLocal
    db = SessionLocal()

    try:
        # First, save annotations to DB if not already there
        from backend.models.ground_truth_models import GroundTruthAnnotation

        saved = 0
        for ann_data in annotations:
            # Check if already exists
            existing = db.query(GroundTruthAnnotation).filter(
                GroundTruthAnnotation.job_id == ann_data["job_id"],
                GroundTruthAnnotation.fragment_index == ann_data["fragment_index"],
                GroundTruthAnnotation.annotator_name == ann_data["annotator_name"],
            ).first()

            if not existing:
                ann = GroundTruthAnnotation(
                    job_id=ann_data["job_id"],
                    fragment_index=ann_data["fragment_index"],
                    annotator_name=ann_data["annotator_name"],
                    gaze_on_task_ratio=ann_data.get("gaze_on_task_ratio"),
                    posture_engaged_ratio=ann_data.get("posture_engaged_ratio"),
                    mindful_score_gt=ann_data.get("mindful_score_gt"),
                    seating_formation=ann_data.get("seating_formation"),
                    teacher_in_active_zone=ann_data.get("teacher_in_active_zone"),
                    teacher_talk_pct_gt=ann_data.get("teacher_talk_pct_gt"),
                    meaningful_score_gt=ann_data.get("meaningful_score_gt"),
                    positive_expression_ratio=ann_data.get("positive_expression_ratio"),
                    hand_raise_count=ann_data.get("hand_raise_count"),
                    joyful_score_gt=ann_data.get("joyful_score_gt"),
                    overall_focus_score=ann_data.get("overall_focus_score"),
                    overall_comfort_score=ann_data.get("overall_comfort_score"),
                    overall_3m_score_gt=ann_data.get("overall_3m_score_gt"),
                    notes=ann_data.get("notes"),
                )
                db.add(ann)
                saved += 1

        if saved > 0:
            db.commit()
            print(f"   💾 Saved {saved} new annotations to database")

        # Now run evaluation
        engine = EvaluationEngine(db)
        print("\n🔄 Running evaluation...")
        start = time.perf_counter()
        report = engine.evaluate_batch(job_ids)
        elapsed = time.perf_counter() - start
        print(f"   ✅ Evaluation completed in {elapsed:.2f}s")

        # Generate reports
        print("\n📊 Generating reports...")
        generator = ReportGenerator(output_dir)
        report_id = f"eval_{int(time.time())}"
        files = generator.generate_full_report(report, report_id)

        _print_summary(report, files)

    finally:
        db.close()


def run_evaluate_from_db(job_ids: List[str], output_dir: str):
    """Evaluate using annotations already in the database."""
    from backend.database import SessionLocal
    from backend.ai.video_3m.evaluation.evaluation_engine import EvaluationEngine
    from backend.ai.video_3m.evaluation.report_generator import ReportGenerator

    db = SessionLocal()
    try:
        engine = EvaluationEngine(db)
        print("\n🔄 Running evaluation...")
        start = time.perf_counter()
        report = engine.evaluate_batch(job_ids)
        elapsed = time.perf_counter() - start
        print(f"   ✅ Evaluation completed in {elapsed:.2f}s")

        generator = ReportGenerator(output_dir)
        report_id = f"eval_{int(time.time())}"
        files = generator.generate_full_report(report, report_id)

        _print_summary(report, files)
    finally:
        db.close()


def _print_summary(report, files: dict):
    """Print evaluation summary to console."""
    print("\n" + "=" * 60)
    print("  EVALUATION SUMMARY")
    print("=" * 60)

    print(f"\n  Total fragments evaluated: {report.total_fragments}")
    print(f"  Total annotators: {report.total_annotators}")

    if report.confusion_matrices:
        print(f"\n  ── Confusion Matrix Results ──")
        for cm in report.confusion_matrices:
            print(f"    {cm.component}:")
            print(f"      Accuracy  = {cm.accuracy:.2%}")
            print(f"      F1 Score  = {cm.f1_score:.4f}")
            print(f"      Cohen's κ = {cm.cohen_kappa:.4f}")

    if report.correlations:
        print(f"\n  ── Correlation Results ──")
        for c in report.correlations:
            sig = "✓" if c.pearson_p < 0.05 else "✗"
            print(f"    {c.component} (N={c.n_samples}):")
            print(f"      Pearson r  = {c.pearson_r:.4f} (p={c.pearson_p:.4f}) [{sig}]")
            print(f"      Spearman ρ = {c.spearman_rho:.4f}")
            print(f"      MAE = {c.mae:.2f}, RMSE = {c.rmse:.2f}")

    if report.inter_rater:
        print(f"\n  ── Inter-Rater Reliability ──")
        for ir in report.inter_rater:
            if ir.icc > 0:
                print(f"    {ir.component}: ICC = {ir.icc:.4f} (N raters = {ir.n_raters})")
            else:
                print(f"    {ir.component}: κ = {ir.cohens_kappa:.4f} (N raters = {ir.n_raters})")

    print(f"\n  ── Summary ──")
    print(f"    Mean Pearson r: {report.mean_pearson_r:.4f}")
    print(f"    Mean F1 Score : {report.mean_f1:.4f}")
    print(f"    Mean Cohen's κ: {report.mean_kappa:.4f}")

    print(f"\n  📁 Generated files:")
    for name, path in files.items():
        print(f"    {name}: {path}")


# ── Generate Template ─────────────────────────────────────────────────────────

def run_generate_template(args):
    """Generate an annotation template for observers."""
    print("=" * 60)
    print("  Generating Annotation Template")
    print("=" * 60)

    if args.job_id:
        # Generate from existing job
        generate_template_from_db(args.job_id, args.output, args.csv)
    else:
        # Generate blank template
        generate_blank_template(args.output, args.csv)


def generate_template_from_db(job_id: str, output_path: str, also_csv: bool):
    """Generate annotation template from an existing job's fragments."""
    from backend.database import SessionLocal
    from backend.models.db_models import VideoAnalysisJob, VideoFragment3M

    db = SessionLocal()
    try:
        job = db.query(VideoAnalysisJob).filter(
            VideoAnalysisJob.job_id == job_id
        ).first()
        if not job:
            print(f"❌ Job '{job_id}' not found")
            return

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
                    "Gunakan skala 0.0–1.0 untuk rasio, 0–100 untuk skor. "
                    "Untuk seating_formation, pilih: 'rows', 'groups', atau 'circle'."
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

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        print(f"✅ Template saved to: {output_path}")
        print(f"   Contains {len(fragments)} fragment(s) for video: {job.video_name}")

        if also_csv:
            csv_path = output_path.rsplit(".", 1)[0] + ".csv"
            _export_template_csv(template, csv_path)
            print(f"✅ CSV template saved to: {csv_path}")

    finally:
        db.close()


def generate_blank_template(output_path: str, also_csv: bool):
    """Generate a blank annotation template with sample data."""
    template = {
        "metadata": {
            "instructions": (
                "PETUNJUK PENGISIAN ANOTASI GROUND TRUTH\n"
                "=======================================\n\n"
                "1. Tonton setiap fragment video (biasanya 5 menit per fragment)\n"
                "2. Isi kolom observasi berdasarkan pengamatan visual Anda:\n\n"
                "   MINDFUL:\n"
                "   - gaze_on_task_ratio (0.0-1.0): Rasio siswa yang memperhatikan\n"
                "     pelajaran (melihat guru/papan/tugas). 0.8 = 80% siswa fokus.\n"
                "   - posture_engaged_ratio (0.0-1.0): Rasio siswa dengan postur\n"
                "     tubuh yang baik (duduk tegak/condong ke depan).\n"
                "   - mindful_score_gt (0-100): Skor keseluruhan Mindful menurut Anda.\n\n"
                "   MEANINGFUL:\n"
                "   - seating_formation: 'rows' (baris tradisional), 'groups'\n"
                "     (berkelompok), atau 'circle' (melingkar).\n"
                "   - teacher_in_active_zone (true/false): Apakah guru bergerak\n"
                "     ke tengah/belakang kelas, bukan hanya berdiri di depan.\n"
                "   - teacher_talk_pct_gt (0-100): Estimasi persentase waktu guru\n"
                "     yang digunakan untuk berbicara.\n"
                "   - meaningful_score_gt (0-100): Skor keseluruhan Meaningful.\n\n"
                "   JOYFUL:\n"
                "   - positive_expression_ratio (0.0-1.0): Rasio siswa yang\n"
                "     menunjukkan ekspresi positif (tersenyum, tertawa, antusias).\n"
                "   - hand_raise_count: Jumlah siswa mengangkat tangan dalam fragment.\n"
                "   - joyful_score_gt (0-100): Skor keseluruhan Joyful.\n\n"
                "   OVERALL:\n"
                "   - overall_focus_score (0-100): Tingkat fokus keseluruhan kelas.\n"
                "   - overall_comfort_score (0-100): Tingkat kenyamanan belajar.\n"
                "   - overall_3m_score_gt (0-100): Skor 3M keseluruhan.\n\n"
                "3. Simpan file ini dan jalankan benchmark:\n"
                "   python -m backend.scripts.benchmark_runner evaluate -i <file>.json\n"
            ),
        },
        "annotations": [
            {
                "job_id": "<masukkan job_id dari video yang sudah dianalisis>",
                "fragment_index": 0,
                "time_range": "0:00 – 5:00",
                "annotator_name": "Observer A",
                "gaze_on_task_ratio": 0.85,
                "posture_engaged_ratio": 0.70,
                "mindful_score_gt": 75.0,
                "seating_formation": "groups",
                "teacher_in_active_zone": True,
                "teacher_talk_pct_gt": 35.0,
                "meaningful_score_gt": 70.0,
                "positive_expression_ratio": 0.60,
                "hand_raise_count": 3,
                "joyful_score_gt": 65.0,
                "overall_focus_score": 78.0,
                "overall_comfort_score": 82.0,
                "overall_3m_score_gt": 72.0,
                "notes": "Siswa terlihat aktif berdiskusi kelompok",
            },
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"✅ Blank template saved to: {output_path}")
    print("   Edit the file with your observations, then run:")
    print(f"   python -m backend.scripts.benchmark_runner evaluate -i {output_path}")

    if also_csv:
        csv_path = output_path.rsplit(".", 1)[0] + ".csv"
        _export_template_csv(template, csv_path)
        print(f"✅ CSV template saved to: {csv_path}")


def _export_template_csv(template: dict, csv_path: str):
    """Export annotation template as CSV for easier editing in Excel."""
    import csv

    fieldnames = [
        "job_id", "fragment_index", "time_range", "annotator_name",
        "gaze_on_task_ratio", "posture_engaged_ratio", "mindful_score_gt",
        "seating_formation", "teacher_in_active_zone", "teacher_talk_pct_gt",
        "meaningful_score_gt",
        "positive_expression_ratio", "hand_raise_count", "joyful_score_gt",
        "overall_focus_score", "overall_comfort_score", "overall_3m_score_gt",
        "notes",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ann in template.get("annotations", []):
            row = {k: ann.get(k, "") for k in fieldnames}
            writer.writerow(row)


# ── Timing Benchmark ──────────────────────────────────────────────────────────

def run_timing_benchmark(args):
    """Run processing time benchmark on a single video."""
    print("=" * 60)
    print("  Pipeline Timing Benchmark")
    print("=" * 60)

    video_path = args.video
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    from backend.ai.video_3m.evaluation.benchmark_timer import PipelineTimer
    from backend.ai.video_3m.video_processor import VideoProcessor
    from backend.ai.video_3m.cv.mindful_detector import MindfulDetector
    from backend.ai.video_3m.cv.meaningful_detector import MeaningfulDetector
    from backend.ai.video_3m.cv.joyful_detector import JoyfulDetector
    from backend.ai.video_3m.aggregation.score_aggregator import ScoreAggregator

    timer = PipelineTimer()

    # Stage 1: Fragment video
    print("\n⏱️  Stage 1: Fragmenting video...")
    with timer.stage("fragmenting"):
        processor = VideoProcessor()
        frag_dir = os.path.join(output_dir, "fragments")
        os.makedirs(frag_dir, exist_ok=True)
        fragments = processor.fragment_video(video_path, frag_dir)
        metadata = processor.get_video_metadata(video_path)

    print(f"   ✅ {len(fragments)} fragments ({metadata.duration_sec:.0f}s video)")

    # Stage 2: Audio extraction
    print("⏱️  Stage 2: Audio extraction...")
    audio_path = os.path.join(output_dir, "audio.wav")
    with timer.stage("audio_extraction"):
        processor.extract_audio(video_path, audio_path)

    # Stage 3: Audio processing
    print("⏱️  Stage 3: Audio processing...")
    audio_result = None
    try:
        with timer.stage("audio_processing"):
            from backend.ai.video_3m.pipeline import VideoAnalysisPipeline
            pipeline = VideoAnalysisPipeline()
            audio_result = pipeline._run_audio_analysis(audio_path)
    except Exception as e:
        print(f"   ⚠ Audio processing failed: {e}")
        timer.record("audio_processing", 0)

    # Stage 4: CV processing per fragment
    print("⏱️  Stage 4: CV processing...")
    mindful_det = MindfulDetector()
    meaningful_det = MeaningfulDetector()
    joyful_det = JoyfulDetector()

    fragment_analyses = []
    from backend.ai.video_3m.data_models import FragmentAnalysis

    for i, fragment in enumerate(fragments):
        with timer.stage("cv_per_fragment"):
            try:
                m = mindful_det.analyze_fragment(fragment)
                mn = meaningful_det.analyze_fragment(fragment, audio_result)
                j = joyful_det.analyze_fragment(fragment, audio_result)
                fa = FragmentAnalysis(fragment=fragment, mindful=m, meaningful=mn, joyful=j)
                fragment_analyses.append(fa)
            except Exception as e:
                print(f"   ⚠ Fragment {i} failed: {e}")

    print(f"   ✅ Processed {len(fragment_analyses)} fragments")

    # Stage 5: Aggregation
    print("⏱️  Stage 5: Aggregation...")
    with timer.stage("aggregation"):
        aggregated = ScoreAggregator().aggregate(fragment_analyses)

    # Print results
    print("\n" + "=" * 60)
    print("  TIMING RESULTS")
    print("=" * 60)
    print(timer)
    print(f"\n  Total time: {timer.get_total_time():.2f}s")
    print(f"  Video duration: {metadata.duration_sec:.0f}s")
    ratio = timer.get_total_time() / max(metadata.duration_sec, 1)
    print(f"  Processing ratio: {ratio:.2f}x real-time")

    # Save timing report
    timing_report = timer.get_report()
    timing_path = os.path.join(output_dir, "timing_report.json")
    with open(timing_path, "w") as f:
        json.dump(timing_report, f, indent=2)
    print(f"\n  📁 Timing report saved to: {timing_path}")

    # Generate timing chart
    from backend.ai.video_3m.evaluation.report_generator import ReportGenerator
    gen = ReportGenerator(output_dir)
    chart_path = gen.plot_processing_times(
        timer.get_results(),
        os.path.join(output_dir, "timing_chart.png"),
    )
    print(f"  📊 Timing chart saved to: {chart_path}")


if __name__ == "__main__":
    main()
