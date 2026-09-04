"""
Abstract base class for all CV detectors in the 3M pipeline.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import cv2
import numpy as np

from backend.ai.video_3m.data_models import VideoFragment


@dataclass
class DetectorConfig:
    frame_sample_fps: float = 0.5   # frames per second to sample (1 frame per 2 sec)
    device: str = "cpu"
    confidence_threshold: float = 0.5


class BaseDetector(ABC):
    """Abstract base for Mindful, Meaningful, and Joyful detectors."""

    def __init__(self, config: Optional[DetectorConfig] = None):
        self.config = config or DetectorConfig()

    @abstractmethod
    def analyze_fragment(self, fragment: VideoFragment, **kwargs):
        """Process one 5-minute fragment and return a typed result object."""

    def extract_frames(
        self,
        fragment: VideoFragment,
        fps: float = 1.0,
    ) -> List[np.ndarray]:
        """
        Sample frames from a video fragment at the given fps.
        Returns a list of BGR numpy arrays (OpenCV format).
        """
        frames: List[np.ndarray] = []
        cap = cv2.VideoCapture(fragment.path)

        if not cap.isOpened():
            return frames

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps

        # Build list of timestamps to sample
        if fps <= 0:
            fps = 1.0
        interval = 1.0 / fps
        timestamps = []
        t = 0.0
        while t <= duration:
            timestamps.append(t)
            t += interval

        for ts in timestamps:
            frame_idx = int(ts * video_fps)
            frame_idx = min(frame_idx, total_frames - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                frames.append(frame)

        cap.release()
        return frames
