"""
MindfulDetector — gaze tracking, posture analysis, silence quality.
Uses MediaPipe Face Mesh (iris landmarks) and MediaPipe Pose.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import numpy as np

from backend.ai.video_3m.cv.base_detector import BaseDetector, DetectorConfig
from backend.ai.video_3m.data_models import (
    VideoFragment,
    MindfulResult,
    AcousticResult,
)

# Mindful score weights (must sum to 1.0)
GAZE_WEIGHT = 0.40
POSTURE_WEIGHT = 0.35
SILENCE_WEIGHT = 0.25

# Gaze: fraction of students on-task threshold
ON_TASK_THRESHOLD = 0.80  # 80% of visible students must be on-task


class MindfulDetector(BaseDetector):
    """
    Detects Mindful indicators:
    - Gaze direction (MediaPipe Face Mesh iris landmarks)
    - Posture (MediaPipe Pose shoulder/spine angle)
    - Silence quality (cross-reference with acoustic energy)
    """

    def __init__(self, config: Optional[DetectorConfig] = None):
        super().__init__(config)
        self._face_mesh = None
        self._pose = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_fragment(
        self,
        fragment: VideoFragment,
        acoustic_result: Optional[AcousticResult] = None,
        **kwargs,
    ) -> MindfulResult:
        frames = self.extract_frames(fragment, fps=0.5)  # 1 frame per 2 sec

        if not frames:
            return MindfulResult()

        gaze_score = self._track_gaze(frames)
        posture_score = self._analyze_posture(frames)
        silence_quality_score, reflection_periods = self._silence_quality(
            fragment, acoustic_result, gaze_score
        )

        mindful_score = round(
            GAZE_WEIGHT * gaze_score
            + POSTURE_WEIGHT * posture_score
            + SILENCE_WEIGHT * silence_quality_score,
            2,
        )

        gaze_on_task_ratio = gaze_score / 100.0

        return MindfulResult(
            gaze_score=round(gaze_score, 2),
            posture_score=round(posture_score, 2),
            silence_quality_score=round(silence_quality_score, 2),
            mindful_score=mindful_score,
            gaze_on_task_ratio=round(gaze_on_task_ratio, 4),
            reflection_periods=reflection_periods,
        )

    # ------------------------------------------------------------------
    # Private: Gaze Tracking
    # ------------------------------------------------------------------

    def _track_gaze(self, frames: List[np.ndarray]) -> float:
        """
        Use MediaPipe Face Mesh iris landmarks to estimate gaze direction.
        Returns gaze_score (0-100): percentage of frames where ≥80% of
        visible faces are looking toward the front (on-task).
        """
        try:
            import mediapipe as mp
            mp_face_mesh = mp.solutions.face_mesh

            on_task_frames = 0
            total_frames_with_faces = 0

            with mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=30,
                refine_landmarks=True,  # enables iris landmarks
                min_detection_confidence=0.5,
            ) as face_mesh:
                for frame in frames:
                    import cv2
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(rgb)

                    if not results.multi_face_landmarks:
                        continue

                    total_frames_with_faces += 1
                    n_faces = len(results.multi_face_landmarks)
                    on_task_count = 0

                    for face_landmarks in results.multi_face_landmarks:
                        if self._is_face_on_task(face_landmarks, frame.shape):
                            on_task_count += 1

                    ratio = on_task_count / n_faces
                    if ratio >= ON_TASK_THRESHOLD:
                        on_task_frames += 1

            if total_frames_with_faces == 0:
                return 50.0  # neutral when no faces detected

            score = (on_task_frames / total_frames_with_faces) * 100.0
            return round(score, 2)

        except Exception as e:
            print(f"⚠ Gaze tracking failed: {e}")
            return 50.0

    def _is_face_on_task(self, face_landmarks, frame_shape) -> bool:
        """
        Estimate if a face is looking forward (on-task) using iris landmarks.
        Iris landmarks: left eye 468-472, right eye 473-477.
        Simple heuristic: iris center should be near the eye center.
        """
        try:
            h, w = frame_shape[:2]
            lm = face_landmarks.landmark

            # Left iris center (landmark 468) vs left eye corners (33, 133)
            iris_l = lm[468]
            eye_l_inner = lm[133]
            eye_l_outer = lm[33]
            eye_center_x = (eye_l_inner.x + eye_l_outer.x) / 2.0
            offset_l = abs(iris_l.x - eye_center_x)

            # Right iris center (landmark 473) vs right eye corners (362, 263)
            iris_r = lm[473]
            eye_r_inner = lm[362]
            eye_r_outer = lm[263]
            eye_center_x_r = (eye_r_inner.x + eye_r_outer.x) / 2.0
            offset_r = abs(iris_r.x - eye_center_x_r)

            # If both irises are close to center → looking forward
            return (offset_l < 0.05) and (offset_r < 0.05)

        except Exception:
            return True  # assume on-task if detection fails

    # ------------------------------------------------------------------
    # Private: Posture Analysis
    # ------------------------------------------------------------------

    def _analyze_posture(self, frames: List[np.ndarray]) -> float:
        """
        Use MediaPipe Pose to detect upright/forward-leaning posture.
        Returns posture_score (0-100).
        """
        try:
            import mediapipe as mp
            import cv2
            mp_pose = mp.solutions.pose

            engaged_frames = 0
            total_frames_with_pose = 0

            with mp_pose.Pose(
                static_image_mode=True,
                min_detection_confidence=0.5,
            ) as pose:
                for frame in frames:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose.process(rgb)

                    if not results.pose_landmarks:
                        continue

                    total_frames_with_pose += 1
                    if self._is_posture_engaged(results.pose_landmarks):
                        engaged_frames += 1

            if total_frames_with_pose == 0:
                return 50.0

            return round((engaged_frames / total_frames_with_pose) * 100.0, 2)

        except Exception as e:
            print(f"⚠ Posture analysis failed: {e}")
            return 50.0

    def _is_posture_engaged(self, pose_landmarks) -> bool:
        """
        Check if the detected pose indicates an engaged (upright/forward) posture.
        Uses shoulder and hip landmarks to estimate spine angle.
        """
        try:
            import mediapipe as mp
            lm = pose_landmarks.landmark
            PoseLandmark = mp.solutions.pose.PoseLandmark

            left_shoulder = lm[PoseLandmark.LEFT_SHOULDER]
            right_shoulder = lm[PoseLandmark.RIGHT_SHOULDER]
            left_hip = lm[PoseLandmark.LEFT_HIP]
            right_hip = lm[PoseLandmark.RIGHT_HIP]

            # Midpoints
            shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
            hip_y = (left_hip.y + right_hip.y) / 2.0
            shoulder_x = (left_shoulder.x + right_shoulder.x) / 2.0
            hip_x = (left_hip.x + right_hip.x) / 2.0

            # Spine vector (pointing upward in image coords means y decreases)
            dy = hip_y - shoulder_y  # positive = shoulder above hip (normal)
            dx = hip_x - shoulder_x

            if dy <= 0:
                return False  # inverted — likely detection error

            import math
            angle_deg = math.degrees(math.atan2(abs(dx), dy))
            # Upright: angle < 20°; forward lean: 20-40°; slouch: > 40°
            return angle_deg < 40.0

        except Exception:
            return True

    # ------------------------------------------------------------------
    # Private: Silence Quality
    # ------------------------------------------------------------------

    def _silence_quality(
        self,
        fragment: VideoFragment,
        acoustic_result: Optional[AcousticResult],
        gaze_score: float,
    ) -> Tuple[float, List[Tuple[float, float]]]:
        """
        Detect STOP/reflection periods: low acoustic energy + high gaze focus.
        Returns (silence_quality_score, reflection_periods).
        """
        if acoustic_result is None:
            return 50.0, []

        # Low energy = potential silence/reflection period
        energy = acoustic_result.energy_level  # [0,1]
        silence_ratio = 1.0 - energy  # higher when quieter

        # Quality silence = quiet AND students are focused (high gaze)
        gaze_ratio = gaze_score / 100.0
        quality_score = round((silence_ratio * 0.5 + gaze_ratio * 0.5) * 100.0, 2)

        # Identify reflection periods (simplified: whole fragment if quality > 60)
        reflection_periods: List[Tuple[float, float]] = []
        if quality_score > 60.0:
            reflection_periods.append((fragment.start_sec, fragment.end_sec))

        return quality_score, reflection_periods
