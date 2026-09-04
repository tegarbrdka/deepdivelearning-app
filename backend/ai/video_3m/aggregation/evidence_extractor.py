"""
EvidenceExtractor — auto-extracts 15-second evidence clips from peak moments.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Tuple

from backend.ai.video_3m.data_models import AggregatedResult, EvidenceClipData

CLIP_DURATION_SEC = 15.0
MAX_CLIPS_PER_TYPE = 3  # max best_practice + improvement clips each


class EvidenceExtractor:
    """
    Identifies pedagogical peak moments (positive and negative) from the
    timeline data and extracts 15-second clips using moviepy.
    """

    def extract_clips(
        self,
        video_path: str,
        analysis: AggregatedResult,
        output_dir: str,
        job_id: str,
    ) -> List[EvidenceClipData]:
        """
        Extract evidence clips from the video.
        Returns list of EvidenceClipData objects.
        """
        if not analysis.timeline_data:
            return []

        clips: List[EvidenceClipData] = []
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Find best and worst moments per aspect
        best_moments = self._find_peak_moments(analysis, clip_type="best_practice")
        worst_moments = self._find_peak_moments(analysis, clip_type="improvement")

        all_moments = best_moments[:MAX_CLIPS_PER_TYPE] + worst_moments[:MAX_CLIPS_PER_TYPE]

        selected_intervals: List[Tuple[float, float]] = []

        for i, moment in enumerate(all_moments):
            clip_name = f"{job_id}_clip_{i + 1:03d}.mp4"
            clip_path = os.path.join(output_dir, clip_name)

            frag_start = moment["peak_sec"]
            frag_end = frag_start + 300.0  # standard 5-minute fragment length

            video_duration = analysis.video_duration_sec or 9999.0
            start_sec = self._find_non_overlapping_start(
                frag_start, frag_end, video_duration, selected_intervals, CLIP_DURATION_SEC
            )
            end_sec = start_sec + CLIP_DURATION_SEC

            # Ensure within video bounds
            if end_sec > video_duration:
                end_sec = video_duration
                start_sec = max(0.0, end_sec - CLIP_DURATION_SEC)

            # Track interval to prevent duplicates/overlap
            selected_intervals.append((start_sec, end_sec))

            # Extract clip
            success = self._extract_clip(video_path, clip_path, start_sec, end_sec)

            if success:
                clips.append(EvidenceClipData(
                    clip_path=clip_path,
                    clip_name=clip_name,
                    start_sec=round(start_sec, 2),
                    end_sec=round(end_sec, 2),
                    clip_type=moment["clip_type"],
                    aspect=moment["aspect"],
                    description=moment["description"],
                    score=moment["score"],
                    job_id=job_id,
                ))

        return clips

    def _find_non_overlapping_start(
        self,
        frag_start: float,
        frag_end: float,
        video_duration: float,
        selected_intervals: List[Tuple[float, float]],
        clip_duration: float = 15.0,
    ) -> float:
        """
        Finds a start time for a clip_duration segment that minimizes overlap with already
        selected clips. It first searches within [frag_start, frag_end] at 1-second steps,
        and if no completely non-overlapping window is found, it searches the entire video.
        """
        # Try to search within fragment first
        search_start = max(0.0, frag_start)
        search_end = min(video_duration, frag_end)
        
        if search_end - search_start < clip_duration:
            search_start = 0.0
            search_end = video_duration
            
        best_start = None
        min_overlap = float('inf')
        
        # Step of 1.0 second for precise positioning
        step = 1.0
        
        # Generate candidates within the preferred fragment range
        s = search_start
        candidates = []
        while s <= search_end - clip_duration:
            candidates.append(s)
            s += step
            
        # Check candidates in the preferred range
        for start in candidates:
            end = start + clip_duration
            max_overlap = 0.0
            for os, oe in selected_intervals:
                overlap = max(0.0, min(end, oe) - max(start, os))
                if overlap > max_overlap:
                    max_overlap = overlap
            
            if max_overlap == 0.0:
                return start
            if max_overlap < min_overlap:
                min_overlap = max_overlap
                best_start = start
                
        # If the preferred range has overlap, let's try searching the entire video for any 0-overlap window
        if min_overlap > 0.0:
            s = 0.0
            while s <= video_duration - clip_duration:
                end = s + clip_duration
                max_overlap = 0.0
                for os, oe in selected_intervals:
                    overlap = max(0.0, min(end, oe) - max(s, os))
                    if overlap > max_overlap:
                        max_overlap = overlap
                
                if max_overlap == 0.0:
                    return s
                if max_overlap < min_overlap:
                    min_overlap = max_overlap
                    best_start = s
                s += step
                
        return best_start if best_start is not None else frag_start


    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_peak_moments(
        self, analysis: AggregatedResult, clip_type: str
    ) -> List[dict]:
        """
        Find peak moments from timeline_data.
        clip_type='best_practice' → highest scores
        clip_type='improvement' → lowest scores
        """
        moments = []
        timeline = analysis.timeline_data

        aspects = [
            ("mindful", "mindful", "Momen Mindful terbaik — siswa sangat fokus"),
            ("meaningful", "meaningful", "Momen Meaningful terbaik — interaksi berkualitas"),
            ("joyful", "joyful", "Momen Joyful terbaik — antusiasme tinggi"),
        ]

        for key, aspect, desc_positive in aspects:
            if not timeline:
                continue

            scores = [(frag.get(key, 0.0), frag.get("start_sec", 0.0)) for frag in timeline]

            if clip_type == "best_practice":
                scores.sort(key=lambda x: x[0], reverse=True)
                score, peak_sec = scores[0]
                description = desc_positive
            else:
                scores.sort(key=lambda x: x[0])
                score, peak_sec = scores[0]
                description = f"Area perbaikan {aspect} — skor rendah terdeteksi"

            moments.append({
                "clip_type": clip_type,
                "aspect": aspect,
                "peak_sec": peak_sec,
                "score": round(score, 2),
                "description": description,
            })

        # Sort by score (best first for best_practice, worst first for improvement)
        if clip_type == "best_practice":
            moments.sort(key=lambda x: x["score"], reverse=True)
        else:
            moments.sort(key=lambda x: x["score"])

        return moments

    def _extract_clip(
        self,
        video_path: str,
        output_path: str,
        start_sec: float,
        end_sec: float,
    ) -> bool:
        """Extract a clip from video_path using moviepy. Returns True on success."""
        if os.path.exists(output_path):
            return True  # already extracted

        try:
            from moviepy.editor import VideoFileClip

            with VideoFileClip(video_path) as clip:
                duration = clip.duration
                start_sec = max(0.0, min(start_sec, duration - 1.0))
                end_sec = min(end_sec, duration)

                if end_sec <= start_sec:
                    return False

                sub = clip.subclip(start_sec, end_sec)
                sub.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    logger=None,
                )
            return True

        except Exception as e:
            print(f"⚠ Evidence clip extraction failed: {e}")
            return False
