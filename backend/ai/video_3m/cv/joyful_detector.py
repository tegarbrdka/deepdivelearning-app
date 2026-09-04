"""
JoyfulDetector — facial expressions, collaboration heatmap, hand gestures.
Uses DeepFace for expressions, YOLOv8 for positions, MediaPipe Hands for gestures.
"""
from __future__ import annotations
from typing import List, Optional
import numpy as np

from backend.ai.video_3m.cv.base_detector import BaseDetector, DetectorConfig
from backend.ai.video_3m.data_models import (
    VideoFragment,
    JoyfulResult,
    AudioResult,
)

# Joyful score weights (must sum to 1.0)
EXPRESSION_WEIGHT = 0.30
ACOUSTIC_WEIGHT = 0.30
COLLABORATION_WEIGHT = 0.25
RISK_TAKING_WEIGHT = 0.15

# Heatmap grid dimensions
GRID_W = 20
GRID_H = 15

# Collaboration cluster threshold (seconds of interaction)
COLLABORATION_THRESHOLD_SEC = 30.0


class JoyfulDetector(BaseDetector):
    """
    Detects Joyful indicators:
    - Facial expressions (DeepFace: happy/surprise/Aha moments, fallback ke MediaPipe)
    - Collaboration heatmap (YOLOv8 person positions → 2D density grid)
    - Hand-raise / risk-taking (MediaPipe Hands)
    - Acoustic events (laughter, applause) from AudioResult
    """

    _deepface_available: Optional[bool] = None

    def __init__(self, config: Optional[DetectorConfig] = None):
        super().__init__(config)
        self._yolo_model = None
        self._hands = None

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
    ) -> JoyfulResult:
        # Sample at 0.33 fps for expressions (1 frame per 3 sec), 0.5 fps for heatmap
        frames_expr = self.extract_frames(fragment, fps=0.33)
        frames_heatmap = self.extract_frames(fragment, fps=0.5)

        expression_result = self._detect_expressions(frames_expr, fragment)
        heatmap_result = self._build_heatmap(frames_heatmap, fragment)
        risk_taking_score = self._detect_risk_taking(frames_heatmap)

        # Acoustic score from AudioResult
        acoustic_score = 50.0
        laughter_events: List[float] = []
        applause_events: List[float] = []

        if audio_result and audio_result.acoustic:
            acoustic_score = audio_result.acoustic.acoustic_score
            laughter_events = audio_result.acoustic.laughter_events
            applause_events = audio_result.acoustic.applause_events

        joyful_score = round(
            EXPRESSION_WEIGHT * expression_result["expression_score"]
            + ACOUSTIC_WEIGHT * acoustic_score
            + COLLABORATION_WEIGHT * heatmap_result["collaboration_score"]
            + RISK_TAKING_WEIGHT * risk_taking_score,
            2,
        )

        return JoyfulResult(
            expression_score=round(expression_result["expression_score"], 2),
            acoustic_score=round(acoustic_score, 2),
            collaboration_score=round(heatmap_result["collaboration_score"], 2),
            risk_taking_score=round(risk_taking_score, 2),
            joyful_score=joyful_score,
            heatmap_data=heatmap_result["grid"],
            aha_moments=expression_result["aha_moments"],
            laughter_events=laughter_events,
            applause_events=applause_events,
        )

    # ------------------------------------------------------------------
    # Private: Facial Expression Detection
    # ------------------------------------------------------------------

    # Class-level flag: None = belum dicek, True = tersedia, False = tidak tersedia
    _deepface_available: Optional[bool] = None

    @classmethod
    def _check_deepface(cls) -> bool:
        """Cek sekali apakah DeepFace bisa diimport. Cache hasilnya."""
        if cls._deepface_available is None:
            try:
                from deepface import DeepFace  # noqa: F401
                cls._deepface_available = True
            except Exception as e:
                print(f"⚠ DeepFace tidak tersedia, skip expression analysis: {e}")
                cls._deepface_available = False
        return cls._deepface_available

    def _detect_expressions(
        self, frames: List[np.ndarray], fragment: VideoFragment
    ) -> dict:
        """
        Run DeepFace emotion analysis on sampled frames.
        Returns expression_score (0-100) and list of aha_moment timestamps.
        Falls back to MediaPipe smile detection if DeepFace unavailable.
        """
        aha_moments: List[float] = []

        # Skip DeepFace entirely if not available — avoid repeated TF load failures
        if not self._check_deepface():
            return self._detect_expressions_mediapipe(frames, fragment)

        positive_frames = 0
        total_frames_with_faces = 0

        for i, frame in enumerate(frames):
            try:
                from deepface import DeepFace
                import cv2

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                analyses = DeepFace.analyze(
                    rgb,
                    actions=["emotion"],
                    enforce_detection=False,
                    silent=True,
                )

                if not isinstance(analyses, list):
                    analyses = [analyses]

                for analysis in analyses:
                    total_frames_with_faces += 1
                    dominant = analysis.get("dominant_emotion", "neutral")
                    emotions = analysis.get("emotion", {})

                    if dominant in ("happy", "surprise"):
                        positive_frames += 1

                    surprise_conf = emotions.get("surprise", 0)
                    if surprise_conf > 50.0:
                        ts = fragment.start_sec + i * 3.0  # 0.33 fps → 3 sec intervals
                        aha_moments.append(round(ts, 2))

            except Exception:
                continue

        if total_frames_with_faces == 0:
            return {"expression_score": 50.0, "aha_moments": aha_moments}

        ratio = positive_frames / total_frames_with_faces
        expression_score = round(ratio * 100.0, 2)

        return {"expression_score": expression_score, "aha_moments": aha_moments}

    def _detect_expressions_mediapipe(
        self, frames: List[np.ndarray], fragment: VideoFragment
    ) -> dict:
        """
        Fallback: gunakan MediaPipe Face Mesh untuk deteksi senyum sederhana
        berdasarkan rasio mulut terbuka (mouth aspect ratio).
        """
        aha_moments: List[float] = []
        smile_frames = 0
        total_frames_with_faces = 0

        try:
            import mediapipe as mp
            import cv2
            mp_face_mesh = mp.solutions.face_mesh

            with mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=10,
                refine_landmarks=False,
                min_detection_confidence=0.5,
            ) as face_mesh:
                for i, frame in enumerate(frames):
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(rgb)

                    if not results.multi_face_landmarks:
                        continue

                    for face_lm in results.multi_face_landmarks:
                        total_frames_with_faces += 1
                        # Mouth landmarks: upper lip 13, lower lip 14, corners 61, 291
                        lm = face_lm.landmark
                        try:
                            mouth_open = abs(lm[13].y - lm[14].y)
                            mouth_width = abs(lm[61].x - lm[291].x)
                            # Smile heuristic: mouth open ratio > 0.02 relative to width
                            if mouth_width > 0 and (mouth_open / mouth_width) > 0.15:
                                smile_frames += 1
                        except Exception:
                            pass

        except Exception as e:
            print(f"⚠ MediaPipe expression fallback failed: {e}")
            return {"expression_score": 50.0, "aha_moments": aha_moments}

        if total_frames_with_faces == 0:
            return {"expression_score": 50.0, "aha_moments": aha_moments}

        score = round((smile_frames / total_frames_with_faces) * 100.0, 2)
        return {"expression_score": score, "aha_moments": aha_moments}

    # ------------------------------------------------------------------
    # Private: Collaboration Heatmap
    # ------------------------------------------------------------------

    def _build_heatmap(
        self, frames: List[np.ndarray], fragment: VideoFragment
    ) -> dict:
        """
        Build a 2D density grid (GRID_H × GRID_W) from person positions.
        Returns collaboration_score and heatmap grid.
        """
        yolo = self._get_yolo()
        grid = np.zeros((GRID_H, GRID_W), dtype=float)

        if yolo is None or not frames:
            return {
                "collaboration_score": 50.0,
                "grid": grid.tolist(),
                "clusters": [],
            }

        for frame in frames:
            h, w = frame.shape[:2]
            try:
                results = yolo(frame, classes=[0], verbose=False)
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        cx = (x1 + x2) / 2.0
                        cy = (y1 + y2) / 2.0
                        gx = min(int(cx / w * GRID_W), GRID_W - 1)
                        gy = min(int(cy / h * GRID_H), GRID_H - 1)
                        grid[gy][gx] += 1.0
            except Exception:
                continue

        # Collaboration score: based on number of occupied cells BEFORE normalization
        occupied_cells = float(np.sum(grid > 0))
        total_cells = GRID_W * GRID_H
        # Scale: if >20% of cells have people → good collaboration spread
        raw_ratio = occupied_cells / total_cells
        collaboration_score = round(min(100.0, raw_ratio * 300.0), 2)

        # Normalize grid to [0, 1] for display
        max_val = grid.max()
        if max_val > 0:
            grid = grid / max_val

        # Identify clusters (simplified: cells with density > 0.7)
        clusters = []
        for gy in range(GRID_H):
            for gx in range(GRID_W):
                if grid[gy][gx] > 0.7:
                    clusters.append({
                        "x": gx,
                        "y": gy,
                        "density": round(float(grid[gy][gx]), 3),
                        "label": "Active Collaboration",
                    })

        return {
            "collaboration_score": collaboration_score,
            "grid": grid.tolist(),
            "clusters": clusters,
        }

    # ------------------------------------------------------------------
    # Private: Risk-Taking (Hand Raise Detection)
    # ------------------------------------------------------------------

    def _detect_risk_taking(self, frames: List[np.ndarray]) -> float:
        """
        Detect hand-raise gestures using MediaPipe Hands.
        Returns risk_taking_score (0-100).
        """
        try:
            import mediapipe as mp
            import cv2
            mp_hands = mp.solutions.hands

            hand_raise_frames = 0
            total_frames_processed = 0

            with mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=10,
                min_detection_confidence=0.5,
            ) as hands:
                for frame in frames:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb)
                    total_frames_processed += 1

                    if not results.multi_hand_landmarks:
                        continue

                    for hand_landmarks in results.multi_hand_landmarks:
                        if self._is_hand_raised(hand_landmarks, frame.shape):
                            hand_raise_frames += 1
                            break  # count once per frame

            if total_frames_processed == 0:
                return 50.0

            ratio = hand_raise_frames / total_frames_processed
            return round(min(100.0, ratio * 200.0), 2)  # scale up since hand raises are rare

        except Exception as e:
            print(f"⚠ Hand detection failed: {e}")
            return 50.0

    def _is_hand_raised(self, hand_landmarks, frame_shape) -> bool:
        """
        Check if a hand is raised above shoulder level.
        Heuristic: wrist landmark y < 0.4 (upper 40% of frame).
        """
        try:
            import mediapipe as mp
            lm = hand_landmarks.landmark
            wrist = lm[mp.solutions.hands.HandLandmark.WRIST]
            # In normalized coords, y=0 is top, y=1 is bottom
            return wrist.y < 0.40
        except Exception:
            return False
