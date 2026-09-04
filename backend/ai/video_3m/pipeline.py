"""
VideoAnalysisPipeline — orchestrates the full 3M video analysis pipeline.
Runs asynchronously as a background task.
"""
from __future__ import annotations

import os
import traceback
from datetime import datetime, timezone
from typing import Optional, List

from backend.ai.video_3m.data_models import (
    FragmentAnalysis,
    AggregatedResult,
    EvidenceClipData,
    TriangulationResult,
)


class VideoAnalysisPipeline:
    """
    Orchestrates the full 3M analysis pipeline:
    1. Fragment video + extract audio
    2. Audio processing (once on full audio)
    3. CV processing per fragment
    4. Aggregation
    5. Evidence extraction
    6. Triangulation (optional, if RPP provided)
    7. Save results to DB
    """

    def __init__(self):
        self._db = None

    async def run(
        self,
        job_id: str,
        video_path: str,
        rpp_path: Optional[str] = None,
    ) -> None:
        """Main pipeline entry point. Updates DB status at each stage."""
        from backend.database import SessionLocal
        self._db = SessionLocal()

        try:
            await self._run_pipeline(job_id, video_path, rpp_path)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            self._set_failed(job_id, error_msg)
        finally:
            if self._db:
                self._db.close()

    # ------------------------------------------------------------------
    # Internal pipeline stages
    # ------------------------------------------------------------------

    async def _run_pipeline(
        self,
        job_id: str,
        video_path: str,
        rpp_path: Optional[str],
    ) -> None:
        import asyncio
        from pathlib import Path

        # ── Stage 1: Fragment video ──────────────────────────────────
        self._update_status(job_id, "fragmenting", 5)
        from backend.ai.video_3m.video_processor import VideoProcessor
        processor = VideoProcessor()

        output_dir = f"backend/uploads/video_3m/fragments/{job_id}"
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        fragments = processor.fragment_video(video_path, output_dir)
        metadata = processor.get_video_metadata(video_path)

        audio_path = f"backend/uploads/video_3m/audio/{job_id}.wav"
        Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
        processor.extract_audio(video_path, audio_path)

        # Update video duration in job record
        self._update_video_duration(job_id, metadata.duration_sec)

        # ── Stage 2: Audio processing (once on full audio) ───────────
        self._update_status(job_id, "audio_processing", 15)
        audio_result = await asyncio.get_event_loop().run_in_executor(
            None, self._run_audio_analysis, audio_path
        )

        # ── Stage 3: CV processing per fragment ─────────────────────
        fragment_analyses: List[FragmentAnalysis] = []
        total_fragments = len(fragments)

        from backend.ai.video_3m.cv.mindful_detector import MindfulDetector
        from backend.ai.video_3m.cv.meaningful_detector import MeaningfulDetector
        from backend.ai.video_3m.cv.joyful_detector import JoyfulDetector

        # Instantiate detectors once — reuse across all fragments
        mindful_det = MindfulDetector()
        meaningful_det = MeaningfulDetector()
        joyful_det = JoyfulDetector()

        loop = asyncio.get_event_loop()

        for i, fragment in enumerate(fragments):
            progress = 15 + int((i / total_fragments) * 60)  # 15% → 75%
            self._update_status(
                job_id,
                f"cv_processing ({i + 1}/{total_fragments})",
                progress,
            )

            try:
                # Run all 3 detectors in PARALLEL per fragment
                mindful_task = loop.run_in_executor(
                    None, mindful_det.analyze_fragment, fragment
                )
                meaningful_task = loop.run_in_executor(
                    None, meaningful_det.analyze_fragment, fragment, audio_result
                )
                joyful_task = loop.run_in_executor(
                    None, joyful_det.analyze_fragment, fragment, audio_result
                )
                mindful_result, meaningful_result, joyful_result = await asyncio.gather(
                    mindful_task, meaningful_task, joyful_task
                )
            except Exception as exc:
                # Skip failed fragment, continue with defaults
                print(f"[Pipeline] Fragment {i} failed: {exc}. Using defaults.")
                from backend.ai.video_3m.data_models import (
                    MindfulResult, MeaningfulResult, JoyfulResult
                )
                mindful_result = MindfulResult()
                meaningful_result = MeaningfulResult()
                joyful_result = JoyfulResult()

            fa = FragmentAnalysis(
                fragment=fragment,
                mindful=mindful_result,
                meaningful=meaningful_result,
                joyful=joyful_result,
            )
            fragment_analyses.append(fa)
            self._save_fragment(job_id, fa)

        # ── Stage 4: Aggregation ─────────────────────────────────────
        self._update_status(job_id, "aggregating", 80)
        from backend.ai.video_3m.aggregation.score_aggregator import ScoreAggregator
        aggregated = ScoreAggregator().aggregate(fragment_analyses)
        aggregated.video_duration_sec = metadata.duration_sec

        # ── Stage 5: Recommendations ─────────────────────────────────
        from backend.ai.video_3m.aggregation.recommendation_engine import RecommendationEngine
        recommendations = RecommendationEngine().generate(aggregated)

        # ── Stage 6: Evidence extraction ─────────────────────────────
        self._update_status(job_id, "extracting_evidence", 88)
        evidence_clips: List[EvidenceClipData] = []
        try:
            from backend.ai.video_3m.aggregation.evidence_extractor import EvidenceExtractor
            evidence_dir = f"backend/uploads/evidence/{job_id}"
            from pathlib import Path as _Path
            _Path(evidence_dir).mkdir(parents=True, exist_ok=True)
            evidence_clips = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: EvidenceExtractor().extract_clips(video_path, aggregated, evidence_dir, job_id),
            )
        except Exception as exc:
            print(f"[Pipeline] Evidence extraction failed: {exc}")

        # ── Stage 7: Triangulation (optional) ────────────────────────
        triangulation: Optional[TriangulationResult] = None
        if rpp_path and os.path.exists(rpp_path):
            self._update_status(job_id, "triangulating", 93)
            try:
                from backend.ai.video_3m.triangulation.rpp_parser import RPPParser
                from backend.ai.video_3m.triangulation.cross_reference import CrossReferenceEngine
                lesson_plan = RPPParser().parse(rpp_path)
                triangulation = CrossReferenceEngine().compare(lesson_plan, aggregated)
            except Exception as exc:
                print(f"[Pipeline] Triangulation failed: {exc}")

        # ── Stage 8: Save results ─────────────────────────────────────
        self._update_status(job_id, "complete", 100)
        self._save_results(job_id, aggregated, evidence_clips, triangulation, recommendations)
        self._mark_complete(job_id)

    # ------------------------------------------------------------------
    # Audio analysis (runs in executor)
    # ------------------------------------------------------------------

    def _run_audio_analysis(self, audio_path: str):
        """Run full audio pipeline: transcription, diarization, NLP, acoustics."""
        from backend.ai.video_3m.data_models import AudioResult

        result = AudioResult()

        try:
            from backend.ai.video_3m.audio.speech_analyzer import SpeechAnalyzer
            speech = SpeechAnalyzer()
            transcript = speech.transcribe(audio_path)
            diarization = speech.diarize(audio_path)
            # Get audio duration for silence calculation
            try:
                import librosa
                y, sr = librosa.load(audio_path, sr=16000, mono=True)
                total_dur = len(y) / sr
            except Exception:
                total_dur = 3600.0  # fallback 1 hour
            talk_time = speech.compute_talk_time(diarization, total_dur)
            result.transcript = transcript
            result.diarization = diarization
            result.talk_time = talk_time
        except Exception as exc:
            print(f"[Pipeline] Speech analysis failed: {exc}")

        try:
            from backend.ai.video_3m.audio.nlp_analyzer import NLPAnalyzer
            if result.transcript and result.diarization:
                nlp = NLPAnalyzer().analyze_transcript(result.transcript, result.diarization)
                result.nlp = nlp
        except Exception as exc:
            print(f"[Pipeline] NLP analysis failed: {exc}")

        try:
            from backend.ai.video_3m.audio.acoustic_analyzer import AcousticAnalyzer
            acoustic = AcousticAnalyzer().analyze(audio_path, result.diarization)
            result.acoustic = acoustic
        except Exception as exc:
            print(f"[Pipeline] Acoustic analysis failed: {exc}")

        return result

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _update_status(self, job_id: str, stage: str, progress: float) -> None:
        from backend.models.db_models import VideoAnalysisJob
        try:
            job = self._db.query(VideoAnalysisJob).filter(
                VideoAnalysisJob.job_id == job_id
            ).first()
            if job:
                job.stage = stage
                job.progress = progress
                if stage == "complete":
                    job.status = "complete"
                elif stage != job.status:
                    job.status = "processing"
                self._db.commit()
        except Exception as exc:
            print(f"[Pipeline] _update_status failed: {exc}")
            self._db.rollback()

    def _update_video_duration(self, job_id: str, duration_sec: float) -> None:
        from backend.models.db_models import VideoAnalysisJob
        try:
            job = self._db.query(VideoAnalysisJob).filter(
                VideoAnalysisJob.job_id == job_id
            ).first()
            if job:
                job.video_duration_sec = duration_sec
                self._db.commit()
        except Exception as exc:
            print(f"[Pipeline] _update_video_duration failed: {exc}")
            self._db.rollback()

    def _set_failed(self, job_id: str, error_msg: str) -> None:
        from backend.models.db_models import VideoAnalysisJob
        try:
            job = self._db.query(VideoAnalysisJob).filter(
                VideoAnalysisJob.job_id == job_id
            ).first()
            if job:
                job.status = "failed"
                job.stage = "failed"
                job.error_msg = error_msg[:2000]  # truncate
                self._db.commit()
        except Exception as exc:
            print(f"[Pipeline] _set_failed failed: {exc}")
            self._db.rollback()

    def _mark_complete(self, job_id: str) -> None:
        from backend.models.db_models import VideoAnalysisJob
        try:
            job = self._db.query(VideoAnalysisJob).filter(
                VideoAnalysisJob.job_id == job_id
            ).first()
            if job:
                job.status = "complete"
                job.stage = "complete"
                job.progress = 100.0
                job.completed_at = datetime.now(timezone.utc)
                self._db.commit()
        except Exception as exc:
            print(f"[Pipeline] _mark_complete failed: {exc}")
            self._db.rollback()

    def _save_fragment(self, job_id: str, fa: FragmentAnalysis) -> None:
        from backend.models.db_models import VideoFragment3M
        try:
            frag = fa.fragment
            m = fa.mindful
            mn = fa.meaningful
            j = fa.joyful

            record = VideoFragment3M(
                job_id=job_id,
                fragment_index=frag.index,
                start_sec=frag.start_sec,
                end_sec=frag.end_sec,
                mindful_score=m.mindful_score,
                meaningful_score=mn.meaningful_score,
                joyful_score=j.joyful_score,
                gaze_score=m.gaze_score,
                posture_score=m.posture_score,
                silence_quality_score=m.silence_quality_score,
                seating_score=mn.seating_score,
                talk_time_score=mn.talk_time_score,
                question_type_score=mn.question_type_score,
                teacher_movement_score=mn.teacher_movement_score,
                expression_score=j.expression_score,
                acoustic_score=j.acoustic_score,
                collaboration_score=j.collaboration_score,
                seating_formation=(
                    mn.seating_formations[-1].formation
                    if mn.seating_formations else None
                ),
                active_zone_ratio=mn.active_zone_ratio,
                teacher_talk_pct=(
                    mn.talk_time_ratio.teacher_pct if mn.talk_time_ratio else None
                ),
                student_talk_pct=(
                    mn.talk_time_ratio.student_pct if mn.talk_time_ratio else None
                ),
            )
            self._db.add(record)
            self._db.commit()
        except Exception as exc:
            print(f"[Pipeline] _save_fragment failed: {exc}")
            self._db.rollback()

    def _save_results(
        self,
        job_id: str,
        aggregated: AggregatedResult,
        clips: List[EvidenceClipData],
        triangulation: Optional[TriangulationResult],
        recommendations: list,
    ) -> None:
        from backend.models.db_models import (
            VideoAnalysisResult,
            EvidenceClip3M,
            TriangulationResult3M,
        )
        try:
            result = VideoAnalysisResult(
                job_id=job_id,
                mindful_score=aggregated.mindful_score,
                meaningful_score=aggregated.meaningful_score,
                joyful_score=aggregated.joyful_score,
                overall_3m_score=aggregated.overall_3m_score,
                gaze_score=aggregated.gaze_score,
                posture_score=aggregated.posture_score,
                silence_quality_score=aggregated.silence_quality_score,
                seating_score=aggregated.seating_score,
                talk_time_score=aggregated.talk_time_score,
                question_type_score=aggregated.question_type_score,
                teacher_movement_score=aggregated.teacher_movement_score,
                expression_score=aggregated.expression_score,
                acoustic_score=aggregated.acoustic_score,
                collaboration_score=aggregated.collaboration_score,
                risk_taking_score=aggregated.risk_taking_score,
                teacher_talk_pct=aggregated.teacher_talk_pct,
                student_talk_pct=aggregated.student_talk_pct,
                silence_pct=aggregated.silence_pct,
                meets_dl_standard=aggregated.meets_dl_standard,
                timeline_data=aggregated.timeline_data,
                heatmap_data=aggregated.heatmap_data,
                aha_moments=aggregated.aha_moments,
                laughter_events=aggregated.laughter_events,
                applause_events=aggregated.applause_events,
                seating_transitions=aggregated.seating_transitions,
                recommendations=recommendations,
                discussion_groups_count=aggregated.discussion_groups_count,
            )
            self._db.add(result)
            self._db.flush()  # get result.id

            # Save evidence clips
            for clip in clips:
                ec = EvidenceClip3M(
                    job_id=job_id,
                    result_id=result.id,
                    clip_path=clip.clip_path,
                    clip_name=clip.clip_name,
                    start_sec=clip.start_sec,
                    end_sec=clip.end_sec,
                    clip_type=clip.clip_type,
                    aspect=clip.aspect,
                    description=clip.description,
                    score=clip.score,
                )
                self._db.add(ec)

            # Save triangulation
            if triangulation is not None:
                items_data = [
                    {
                        "activity": it.activity,
                        "planned": it.planned,
                        "detected": it.detected,
                        "status": it.status,
                        "evidence": it.evidence,
                        "recommendation": it.recommendation,
                    }
                    for it in triangulation.items
                ]
                tri_record = TriangulationResult3M(
                    job_id=job_id,
                    result_id=result.id,
                    items=items_data,
                    alignment_score=triangulation.alignment_score,
                )
                self._db.add(tri_record)

            self._db.commit()
        except Exception as exc:
            print(f"[Pipeline] _save_results failed: {exc}")
            self._db.rollback()
