"""
MeaningfulDetector — seating arrangement detection + teacher movement tracking.
Uses YOLOv8n for person detection and DBSCAN for seating clustering.
"""
from __future__ import annotations
from typing import List, Optional
import numpy as np

from backend.ai.video_3m.cv.base_detector import BaseDetector, DetectorConfig
from backend.ai.video_3m.data_models import (
    VideoFragment,
    MeaningfulResult,
    SeatingEvent,
    MovementResult,
    AudioResult,
)

# Meaningful score weights (must sum to 1.0)
SEATING_WEIGHT = 0.30
TALK_TIME_WEIGHT = 0.40
MOVEMENT_WEIGHT = 0.30

# Teacher movement threshold
ACTIVE_ZONE_THRESHOLD = 0.60  # >60% time in active zone = high score


class MeaningfulDetector(BaseDetector):
    """
    Detects Meaningful indicators:
    - Seating arrangement (rows / circle / groups) via YOLOv8 + DBSCAN
    - Teacher movement (Active Zone vs Static Zone) via person tracking
    - Talk-time ratio and question type scores from AudioResult
    """

    def __init__(self, config: Optional[DetectorConfig] = None):
        super().__init__(config)
        self._yolo_model = None

    def _get_yolo(self):
        if self._yolo_model is None:
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO("yolov8n.pt")
            except Exception as e:
                print(f"⚠ YOLOv8 load failed: {e}")
        return self._yolo_model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_fragment(
        self,
        fragment: VideoFragment,
        audio_result: Optional[AudioResult] = None,
        **kwargs,
    ) -> MeaningfulResult:
        # Sample at 0.5 fps (1 frame per 2 seconds)
        frames = self.extract_frames(fragment, fps=0.5)

        if not frames:
            return MeaningfulResult()

        seating_score, seating_formations, discussion_groups_count = self._detect_seating(frames, fragment)
        movement_result = self._track_teacher_movement(frames)

        # Pull audio-derived scores from AudioResult
        talk_time_score = 50.0
        question_type_score = 50.0
        talk_time_ratio = None

        if audio_result:
            if audio_result.talk_time:
                tt = audio_result.talk_time
                talk_time_ratio = tt
                # Score: closer to DL standard (teacher 30-40%, student 60-70%) = higher
                if tt.meets_standard:
                    talk_time_score = 100.0
                else:
                    talk_time_score = max(0.0, 100.0 - tt.deviation * 2.0)

            if audio_result.nlp:
                question_type_score = audio_result.nlp.question_type_score

        meaningful_score = round(
            SEATING_WEIGHT * seating_score
            + TALK_TIME_WEIGHT * talk_time_score
            + MOVEMENT_WEIGHT * movement_result.teacher_movement_score,
            2,
        )

        return MeaningfulResult(
            seating_score=round(seating_score, 2),
            teacher_movement_score=round(movement_result.teacher_movement_score, 2),
            talk_time_score=round(talk_time_score, 2),
            question_type_score=round(question_type_score, 2),
            meaningful_score=meaningful_score,
            seating_formations=seating_formations,
            active_zone_ratio=round(movement_result.active_zone_ratio, 4),
            talk_time_ratio=talk_time_ratio,
            discussion_groups_count=discussion_groups_count,
        )

    # ------------------------------------------------------------------
    # Private: Seating Detection
    # ------------------------------------------------------------------

    def _detect_seating(
        self,
        frames: List[np.ndarray],
        fragment: VideoFragment,
    ) -> tuple[float, List[SeatingEvent], int]:
        """
        Detect seating formation using YOLOv8 person detection + DBSCAN clustering.
        Returns (seating_score, list_of_SeatingEvent, max_discussion_groups_count).
        """
        yolo = self._get_yolo()
        if yolo is None:
            return 50.0, [], 0

        formation_scores = []
        seating_events: List[SeatingEvent] = []
        prev_formation = None
        max_groups = 0

        for i, frame in enumerate(frames):
            centroids = self._detect_persons(yolo, frame)
            if len(centroids) < 2:
                continue

            formation, n_clusters = self._classify_formation(centroids, frame.shape)
            formation_scores.append(self._formation_to_score(formation))

            # Track max discussion groups seen
            if formation == "groups" and n_clusters > max_groups:
                max_groups = n_clusters

            # Record transition events
            if formation != prev_formation:
                ts = fragment.start_sec + i  # approx 1 frame/sec
                seating_events.append(SeatingEvent(timestamp_sec=ts, formation=formation))
                prev_formation = formation

        if not formation_scores:
            return 50.0, seating_events, 0

        avg_score = float(np.mean(formation_scores))
        return round(avg_score, 2), seating_events, max_groups

    def _detect_persons(self, yolo, frame: np.ndarray) -> List[tuple]:
        """Run YOLOv8 and return list of (cx, cy) centroids for class 'person'."""
        try:
            results = yolo(frame, classes=[0], verbose=False)  # class 0 = person
            centroids = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    centroids.append((cx, cy))
            return centroids
        except Exception:
            return []

    def _classify_formation(self, centroids: List[tuple], frame_shape) -> tuple[str, int]:
        """
        Classify seating formation using DBSCAN clustering.
        - 1 cluster → rows (all together)
        - 2-3 clusters → groups
        - circular spread → circle
        Returns (formation_name, n_clusters).
        """
        try:
            from sklearn.cluster import DBSCAN
            import numpy as np

            h, w = frame_shape[:2]
            # Normalize coordinates
            pts = np.array([[cx / w, cy / h] for cx, cy in centroids])

            db = DBSCAN(eps=0.15, min_samples=2).fit(pts)
            n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)

            if n_clusters <= 1:
                return "rows", max(1, n_clusters)
            elif n_clusters <= 4:
                return "groups", n_clusters
            else:
                return "circle", n_clusters
        except Exception:
            return "rows", 1

    def _formation_to_score(self, formation: str) -> float:
        """Higher score for collaborative formations."""
        return {"rows": 30.0, "groups": 80.0, "circle": 90.0}.get(formation, 50.0)

    # ------------------------------------------------------------------
    # Private: Teacher Movement Tracking
    # ------------------------------------------------------------------

    def _track_teacher_movement(self, frames: List[np.ndarray]) -> MovementResult:
        """
        Track teacher position across frames.
        Teacher heuristic: largest detected person (closest to camera).
        Active Zone: teacher is NOT in the front 30% of the frame.
        """
        yolo = self._get_yolo()
        if yolo is None:
            return MovementResult(active_zone_ratio=0.5, teacher_movement_score=50.0)

        active_frames = 0
        total_frames_with_teacher = 0

        for frame in frames:
            teacher_pos = self._find_teacher(yolo, frame)
            if teacher_pos is None:
                continue

            total_frames_with_teacher += 1
            h, w = frame.shape[:2]
            cx, cy = teacher_pos

            # Active Zone: teacher is in the middle/back area (cy > 30% of frame height)
            # and not stuck at the very front (cy < 85%)
            in_active_zone = (cy / h) > 0.30
            if in_active_zone:
                active_frames += 1

        if total_frames_with_teacher == 0:
            return MovementResult(active_zone_ratio=0.5, teacher_movement_score=50.0)

        active_ratio = active_frames / total_frames_with_teacher
        # Score: >60% active zone → high score
        if active_ratio >= ACTIVE_ZONE_THRESHOLD:
            score = 70.0 + (active_ratio - ACTIVE_ZONE_THRESHOLD) / (1.0 - ACTIVE_ZONE_THRESHOLD) * 30.0
        else:
            score = (active_ratio / ACTIVE_ZONE_THRESHOLD) * 70.0

        return MovementResult(
            active_zone_ratio=round(active_ratio, 4),
            teacher_movement_score=round(score, 2),
        )

    def _find_teacher(self, yolo, frame: np.ndarray) -> Optional[tuple]:
        """
        Find the teacher: the largest bounding box (assumed closest to camera).
        Returns (cx, cy) or None.
        """
        try:
            results = yolo(frame, classes=[0], verbose=False)
            largest_area = 0.0
            teacher_pos = None

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    area = (x2 - x1) * (y2 - y1)
                    if area > largest_area:
                        largest_area = area
                        teacher_pos = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

            return teacher_pos
        except Exception:
            return None
