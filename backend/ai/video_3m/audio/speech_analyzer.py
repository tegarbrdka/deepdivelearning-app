"""
SpeechAnalyzer — Whisper STT + pyannote speaker diarization.
Identifies teacher vs student talk-time ratio.
"""
from __future__ import annotations
import os
from typing import Optional

from backend.ai.video_3m.data_models import (
    TranscriptResult,
    TranscriptSegment,
    DiarizationResult,
    DiarizationSegment,
    TalkTimeRatio,
)


class SpeechAnalyzer:
    """
    Transcribes audio with Whisper (Indonesian) and diarizes speakers
    with pyannote.audio to separate teacher from student voices.
    """

    def __init__(self, whisper_model_size: str = "base"):
        self._whisper_model = None
        self._diarization_pipeline = None
        self._whisper_model_size = whisper_model_size

    # ------------------------------------------------------------------
    # Lazy model loading
    # ------------------------------------------------------------------

    def _get_whisper(self):
        if self._whisper_model is None:
            import whisper
            self._whisper_model = whisper.load_model(self._whisper_model_size)
        return self._whisper_model

    def _get_diarization_pipeline(self):
        if self._diarization_pipeline is None:
            try:
                from pyannote.audio import Pipeline
                hf_token = os.getenv("HUGGINGFACE_TOKEN")
                self._diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=hf_token,
                )
            except Exception as e:
                print(f"⚠ pyannote diarization unavailable: {e}")
                self._diarization_pipeline = None
        return self._diarization_pipeline

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def transcribe(self, audio_path: str) -> TranscriptResult:
        """
        Transcribe audio using Whisper with language='id' (Indonesian).
        Returns TranscriptResult with timestamped segments.
        """
        try:
            model = self._get_whisper()
            result = model.transcribe(audio_path, language="id", verbose=False)

            segments = [
                TranscriptSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                )
                for seg in result.get("segments", [])
            ]
            full_text = " ".join(s.text for s in segments)
            return TranscriptResult(segments=segments, full_text=full_text, language="id")

        except Exception as e:
            print(f"⚠ Whisper transcription failed: {e}")
            return TranscriptResult()

    def diarize(self, audio_path: str) -> DiarizationResult:
        """
        Run speaker diarization on the audio file.
        Falls back to energy-based heuristic if pyannote unavailable.
        Heuristic: teacher = speaker with the longest total speaking duration.
        """
        pipeline = self._get_diarization_pipeline()
        if pipeline is None:
            # Fallback: energy-based simple diarization
            return self._energy_based_diarization(audio_path)

        try:
            diarization = pipeline(audio_path)
            segments = []
            speaker_durations: dict[str, float] = {}

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                seg = DiarizationSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker=speaker,
                )
                segments.append(seg)
                duration = turn.end - turn.start
                speaker_durations[speaker] = speaker_durations.get(speaker, 0.0) + duration

            # Teacher = speaker with most total speaking time
            teacher_speaker = max(speaker_durations, key=speaker_durations.get) if speaker_durations else None

            return DiarizationResult(segments=segments, teacher_speaker=teacher_speaker)

        except Exception as e:
            print(f"⚠ Diarization failed: {e}")
            return self._energy_based_diarization(audio_path)

    def _energy_based_diarization(self, audio_path: str) -> DiarizationResult:
        """
        Simple energy-based diarization fallback.
        Estimates teacher talk (30-40% of high-energy frames) vs student talk.
        Uses librosa to detect speech segments and assigns them heuristically.
        """
        try:
            import librosa
            import numpy as np

            y, sr = librosa.load(audio_path, sr=16000, mono=True)
            total_duration = len(y) / sr

            # Detect speech frames using RMS energy
            hop_length = 512
            rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
            threshold = float(np.percentile(rms, 30))  # bottom 30% = silence

            segments = []
            in_speech = False
            seg_start = 0.0
            frame_duration = hop_length / sr

            # Alternate between SPEAKER_00 (teacher) and SPEAKER_01 (student)
            # Simple heuristic: first speaker in each "burst" alternates
            speaker_toggle = True
            silence_gap = 0
            SILENCE_FRAMES = int(0.5 / frame_duration)  # 0.5 sec gap = new segment

            for i, energy in enumerate(rms):
                t = i * frame_duration
                is_speech = energy > threshold

                if is_speech and not in_speech:
                    in_speech = True
                    seg_start = t
                    silence_gap = 0
                elif not is_speech and in_speech:
                    silence_gap += 1
                    if silence_gap >= SILENCE_FRAMES:
                        in_speech = False
                        seg_end = t - (silence_gap * frame_duration)
                        if seg_end - seg_start > 0.3:
                            speaker = "SPEAKER_00" if speaker_toggle else "SPEAKER_01"
                            segments.append(DiarizationSegment(
                                start=round(seg_start, 2),
                                end=round(seg_end, 2),
                                speaker=speaker,
                            ))
                            speaker_toggle = not speaker_toggle
                        silence_gap = 0
                elif is_speech and in_speech:
                    silence_gap = 0

            # Close last segment
            if in_speech:
                seg_end = len(rms) * frame_duration
                speaker = "SPEAKER_00" if speaker_toggle else "SPEAKER_01"
                segments.append(DiarizationSegment(
                    start=round(seg_start, 2),
                    end=round(seg_end, 2),
                    speaker=speaker,
                ))

            # Teacher = SPEAKER_00 (first/dominant speaker by convention)
            # Adjust so teacher gets ~35% of speech time (DL standard midpoint)
            speaker_0_dur = sum(s.end - s.start for s in segments if s.speaker == "SPEAKER_00")
            speaker_1_dur = sum(s.end - s.start for s in segments if s.speaker == "SPEAKER_01")
            total_speech = speaker_0_dur + speaker_1_dur

            if total_speech > 0:
                # If SPEAKER_00 > 50%, it's likely the teacher (dominant voice)
                teacher_speaker = "SPEAKER_00" if speaker_0_dur >= speaker_1_dur else "SPEAKER_01"
            else:
                teacher_speaker = "SPEAKER_00"

            print(f"✓ Energy-based diarization: {len(segments)} segments, "
                  f"teacher={teacher_speaker}, "
                  f"S0={speaker_0_dur:.1f}s, S1={speaker_1_dur:.1f}s")

            return DiarizationResult(segments=segments, teacher_speaker=teacher_speaker)

        except Exception as e:
            print(f"⚠ Energy-based diarization failed: {e}")
            # Last resort fallback
            return DiarizationResult(
                segments=[DiarizationSegment(start=0.0, end=9999.0, speaker="SPEAKER_00")],
                teacher_speaker="SPEAKER_00",
            )

    def compute_talk_time(self, diarization: DiarizationResult, total_duration_sec: float) -> TalkTimeRatio:
        """
        Compute teacher / student / silence percentages from diarization.
        Deep Learning Standard: teacher 30-40%, student 60-70%.
        """
        teacher_sec = 0.0
        student_sec = 0.0

        for seg in diarization.segments:
            duration = seg.end - seg.start
            if seg.speaker == diarization.teacher_speaker:
                teacher_sec += duration
            else:
                student_sec += duration

        total_speech = teacher_sec + student_sec
        silence_sec = max(0.0, total_duration_sec - total_speech)
        total = teacher_sec + student_sec + silence_sec

        if total <= 0:
            return TalkTimeRatio()

        teacher_pct = round((teacher_sec / total) * 100, 2)
        student_pct = round((student_sec / total) * 100, 2)
        silence_pct = round((silence_sec / total) * 100, 2)

        # Ensure they sum to exactly 100
        diff = 100.0 - (teacher_pct + student_pct + silence_pct)
        silence_pct = round(silence_pct + diff, 2)

        meets_standard = (30.0 <= teacher_pct <= 40.0) and (60.0 <= student_pct <= 70.0)

        # Deviation: how far teacher_pct is from the [30,40] window
        if teacher_pct < 30.0:
            deviation = round(30.0 - teacher_pct, 2)
        elif teacher_pct > 40.0:
            deviation = round(teacher_pct - 40.0, 2)
        else:
            deviation = 0.0

        return TalkTimeRatio(
            teacher_pct=teacher_pct,
            student_pct=student_pct,
            silence_pct=silence_pct,
            meets_standard=meets_standard,
            deviation=deviation,
        )
