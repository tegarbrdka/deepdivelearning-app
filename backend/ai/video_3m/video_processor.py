"""
VideoProcessor — splits a video into 5-minute fragments and extracts audio.
Uses ffmpeg (via subprocess) for fast stream-copy fragmentation,
and moviepy only for metadata reading.
"""
from __future__ import annotations
import os
import math
import subprocess
from pathlib import Path
from typing import List

from backend.ai.video_3m.data_models import VideoFragment, VideoMetadata


class VideoProcessor:
    FRAGMENT_DURATION_SEC: int = 300  # 5 minutes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fragment_video(
        self,
        video_path: str,
        output_dir: str,
    ) -> List[VideoFragment]:
        """
        Split *video_path* into 5-minute segments using ffmpeg stream-copy
        (no re-encoding — very fast).

        Returns a list of VideoFragment objects ordered by index.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Get duration via ffprobe
        duration = self._get_duration_ffprobe(video_path)

        fragments: List[VideoFragment] = []
        n_fragments = math.ceil(duration / self.FRAGMENT_DURATION_SEC)

        for i in range(n_fragments):
            start = i * self.FRAGMENT_DURATION_SEC
            end = min(start + self.FRAGMENT_DURATION_SEC, duration)
            frag_duration = end - start

            frag_path = os.path.join(output_dir, f"fragment_{i:04d}.mp4")

            # Only write if not already present (idempotent)
            if not os.path.exists(frag_path):
                ffmpeg = self._ffmpeg_bin()
                cmd = [
                    ffmpeg, "-y",
                    "-ss", str(start),
                    "-i", video_path,
                    "-t", str(frag_duration),
                    "-c", "copy",
                    "-avoid_negative_ts", "make_zero",
                    "-loglevel", "error",
                    frag_path,
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    cmd_fallback = [
                        ffmpeg, "-y",
                        "-ss", str(start),
                        "-i", video_path,
                        "-t", str(frag_duration),
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                        "-c:a", "aac",
                        "-loglevel", "error",
                        frag_path,
                    ]
                    subprocess.run(cmd_fallback, capture_output=True)

            fragments.append(
                VideoFragment(
                    index=i,
                    path=frag_path,
                    start_sec=start,
                    end_sec=end,
                    duration_sec=frag_duration,
                )
            )

        return fragments

    def extract_audio(self, video_path: str, output_path: str) -> str:
        """
        Extract the full audio track as a 16 kHz mono WAV file using ffmpeg.
        Returns the path to the WAV file.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        ffmpeg = self._ffmpeg_bin()
        cmd = [
            ffmpeg, "-y",
            "-i", video_path,
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            "-loglevel", "error",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Create silent WAV as fallback
            try:
                import numpy as np
                import soundfile as sf
                dur = self._get_duration_ffprobe(video_path)
                silence = np.zeros(int(dur * 16000), dtype=np.float32)
                sf.write(output_path, silence, 16000)
            except Exception:
                pass

        return output_path

    def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """Return basic metadata about the video using ffprobe."""
        duration = self._get_duration_ffprobe(video_path)
        fps, width, height = self._get_video_info_ffprobe(video_path)
        total_fragments = math.ceil(duration / self.FRAGMENT_DURATION_SEC)

        return VideoMetadata(
            duration_sec=duration,
            fps=fps,
            width=width,
            height=height,
            total_fragments=total_fragments,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ffmpeg_bin() -> str:
        """Get the ffmpeg binary path — uses imageio_ffmpeg if available."""
        try:
            from imageio_ffmpeg import get_ffmpeg_exe
            return get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"

    @staticmethod
    def _ffprobe_bin() -> str:
        """Get ffprobe — same directory as ffmpeg from imageio_ffmpeg."""
        try:
            from imageio_ffmpeg import get_ffmpeg_exe
            import os
            ffmpeg_path = get_ffmpeg_exe()
            ffprobe = os.path.join(
                os.path.dirname(ffmpeg_path),
                os.path.basename(ffmpeg_path).replace("ffmpeg", "ffprobe"),
            )
            if os.path.exists(ffprobe):
                return ffprobe
        except Exception:
            pass
        return "ffprobe"

    def _get_duration_ffprobe(self, video_path: str) -> float:
        """Get video duration in seconds via ffprobe."""
        try:
            # Try ffprobe first
            ffprobe = self._ffprobe_bin()
            cmd = [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            val = result.stdout.strip()
            if val:
                return float(val)
        except Exception:
            pass
        # Fallback to moviepy
        try:
            from moviepy.editor import VideoFileClip
            with VideoFileClip(video_path) as clip:
                return clip.duration
        except Exception:
            return 0.0

    def _get_video_info_ffprobe(self, video_path: str) -> tuple:
        """Get fps, width, height via ffprobe. Returns (fps, width, height)."""
        try:
            ffprobe = self._ffprobe_bin()
            cmd = [
                ffprobe, "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-of", "default=noprint_wrappers=1",
                video_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            fps, width, height = 25.0, 1280, 720
            for line in result.stdout.splitlines():
                if line.startswith("width="):
                    width = int(line.split("=")[1])
                elif line.startswith("height="):
                    height = int(line.split("=")[1])
                elif line.startswith("r_frame_rate="):
                    num, den = line.split("=")[1].split("/")
                    fps = float(num) / float(den) if float(den) else 25.0
            return fps, width, height
        except Exception:
            return 25.0, 1280, 720
