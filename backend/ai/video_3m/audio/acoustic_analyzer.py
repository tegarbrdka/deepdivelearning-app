"""
AcousticAnalyzer — librosa-based energy, laughter, and applause detection.
"""
from __future__ import annotations
from typing import List, Optional

from backend.ai.video_3m.data_models import AcousticResult, DiarizationResult


class AcousticAnalyzer:
    """
    Analyzes the acoustic properties of a classroom audio track:
    - RMS energy profile (normalized to [0,1])
    - Laughter event detection (energy burst + spectral pattern)
    - Applause event detection (broadband noise burst)
    - Vocal tone features (pitch, tempo, energy variance)
    """

    # Thresholds (tunable)
    LAUGHTER_ENERGY_THRESHOLD: float = 0.6   # relative to max RMS
    APPLAUSE_ENERGY_THRESHOLD: float = 0.5
    MIN_EVENT_DURATION_SEC: float = 0.5       # ignore very short bursts

    def analyze(
        self,
        audio_path: str,
        diarization: Optional[DiarizationResult] = None,
    ) -> AcousticResult:
        """
        Full acoustic analysis of the audio file.
        Returns AcousticResult with energy level, events, and score.
        """
        try:
            import librosa
            import numpy as np

            y, sr = librosa.load(audio_path, sr=16000, mono=True)

            energy_level = self._compute_energy(y, sr)
            laughter_events = self._detect_laughter(y, sr)
            applause_events = self._detect_applause(y, sr)
            duration_min = len(y) / sr / 60.0

            laughter_freq = len(laughter_events) / max(duration_min, 0.01)
            applause_freq = len(applause_events) / max(duration_min, 0.01)

            # Acoustic score: only positive events (laughter + applause) count for Joyful
            acoustic_score = round(
                min(100.0, (laughter_freq + applause_freq) * 10.0), 2
            )

            return AcousticResult(
                energy_level=round(energy_level, 4),
                acoustic_score=acoustic_score,
                laughter_events=laughter_events,
                applause_events=applause_events,
                laughter_frequency=round(laughter_freq, 4),
                applause_frequency=round(applause_freq, 4),
            )

        except Exception as e:
            print(f"⚠ AcousticAnalyzer failed: {e}")
            return AcousticResult()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_energy(self, y, sr) -> float:
        """
        Compute normalized RMS energy level in [0, 1].
        Higher value = louder / more energetic classroom.
        """
        import librosa
        import numpy as np

        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        if rms.max() == 0:
            return 0.0
        # Normalize to [0, 1] using the 95th percentile as ceiling
        ceiling = float(np.percentile(rms, 95)) or float(rms.max())
        normalized = float(np.mean(rms)) / ceiling
        return min(1.0, max(0.0, normalized))

    def _detect_laughter(self, y, sr) -> List[float]:
        """
        Detect laughter events: short high-energy bursts with
        characteristic spectral rolloff pattern.
        Returns list of timestamps (seconds) where laughter starts.
        """
        import librosa
        import numpy as np

        hop_length = 512
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length)[0]

        rms_norm = rms / (rms.max() + 1e-9)
        rolloff_norm = rolloff / (rolloff.max() + 1e-9)

        # Laughter: high energy + high spectral rolloff (bright, bursty)
        laughter_mask = (rms_norm > self.LAUGHTER_ENERGY_THRESHOLD) & (rolloff_norm > 0.5)

        return self._mask_to_timestamps(laughter_mask, hop_length, sr)

    def _detect_applause(self, y, sr) -> List[float]:
        """
        Detect applause: sustained broadband noise bursts.
        Returns list of timestamps (seconds).
        """
        import librosa
        import numpy as np

        hop_length = 512
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
        # Spectral flatness: high flatness = noise-like (applause)
        flatness = librosa.feature.spectral_flatness(y=y, hop_length=hop_length)[0]

        rms_norm = rms / (rms.max() + 1e-9)
        # Applause: moderate-high energy + high spectral flatness
        applause_mask = (rms_norm > self.APPLAUSE_ENERGY_THRESHOLD) & (flatness > 0.1)

        return self._mask_to_timestamps(applause_mask, hop_length, sr)

    def _analyze_tone(self, y, sr) -> dict:
        """Extract pitch, tempo, and energy variance features."""
        import librosa
        import numpy as np

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[magnitudes > magnitudes.mean()]
        mean_pitch = float(np.mean(pitch_values)) if len(pitch_values) > 0 else 0.0

        rms = librosa.feature.rms(y=y)[0]
        energy_variance = float(np.var(rms))

        return {
            "tempo": float(tempo),
            "mean_pitch_hz": mean_pitch,
            "energy_variance": energy_variance,
        }

    def _mask_to_timestamps(self, mask, hop_length: int, sr: int) -> List[float]:
        """Convert a boolean frame mask to a list of event start timestamps."""
        import numpy as np

        timestamps: List[float] = []
        in_event = False
        event_start_frame = 0
        min_frames = int(self.MIN_EVENT_DURATION_SEC * sr / hop_length)

        for i, val in enumerate(mask):
            if val and not in_event:
                in_event = True
                event_start_frame = i
            elif not val and in_event:
                in_event = False
                if (i - event_start_frame) >= min_frames:
                    ts = event_start_frame * hop_length / sr
                    timestamps.append(round(ts, 2))

        # Handle event that runs to end of signal
        if in_event and (len(mask) - event_start_frame) >= min_frames:
            ts = event_start_frame * hop_length / sr
            timestamps.append(round(ts, 2))

        return timestamps
