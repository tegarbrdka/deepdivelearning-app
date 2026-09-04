"""
NLPAnalyzer — detects Indonesian pedagogical phrases in teacher speech.
Classifies utterances as prompting questions vs instructional commands.
"""
from __future__ import annotations
import re
from typing import List

from backend.ai.video_3m.data_models import (
    TranscriptResult,
    DiarizationResult,
    NLPResult,
)


class NLPAnalyzer:
    """
    Detects prompting phrases ("Mengapa", "Bagaimana jika", …) and
    instructional command phrases ("Buka halaman", "Diam", …) in the
    teacher's transcribed speech.
    """

    PROMPTING_PHRASES: List[str] = [
        "mengapa",
        "bagaimana jika",
        "karena",
        "apa yang terjadi jika",
        "menurutmu",
        "coba jelaskan",
        "bandingkan",
        "apa pendapatmu",
        "bagaimana menurut",
        "kenapa",
        "jelaskan mengapa",
        "apa alasannya",
    ]

    COMMAND_PHRASES: List[str] = [
        "buka halaman",
        "diam",
        "duduk",
        "perhatikan",
        "catat",
        "kerjakan soal",
        "tutup buku",
        "dengarkan",
        "lihat ke depan",
        "jangan bicara",
        "harap tenang",
    ]

    def analyze_transcript(
        self,
        transcript: TranscriptResult,
        diarization: DiarizationResult,
    ) -> NLPResult:
        """
        Filter transcript to teacher-only segments, then count phrase occurrences.
        Returns NLPResult with counts and a question_type_score (0-100).
        """
        teacher_text = self._extract_teacher_text(transcript, diarization)

        prompting_count, detected_prompting = self._count_phrases(
            teacher_text, self.PROMPTING_PHRASES
        )
        command_count, detected_commands = self._count_phrases(
            teacher_text, self.COMMAND_PHRASES
        )

        question_score = self._score_question_ratio(prompting_count, command_count)

        return NLPResult(
            prompting_count=prompting_count,
            command_count=command_count,
            question_type_score=question_score,
            detected_prompting=detected_prompting,
            detected_commands=detected_commands,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_teacher_text(
        self,
        transcript: TranscriptResult,
        diarization: DiarizationResult,
    ) -> str:
        """
        Return concatenated text from transcript segments that overlap
        with the teacher's diarization segments.
        """
        if not diarization.teacher_speaker or not diarization.segments:
            # No diarization info — use full transcript
            return transcript.full_text.lower()

        teacher_intervals = [
            (seg.start, seg.end)
            for seg in diarization.segments
            if seg.speaker == diarization.teacher_speaker
        ]

        teacher_texts: List[str] = []
        for t_seg in transcript.segments:
            seg_mid = (t_seg.start + t_seg.end) / 2.0
            for t_start, t_end in teacher_intervals:
                if t_start <= seg_mid <= t_end:
                    teacher_texts.append(t_seg.text)
                    break

        return " ".join(teacher_texts).lower()

    def _count_phrases(
        self,
        text: str,
        phrases: List[str],
    ) -> tuple[int, List[str]]:
        """
        Count total occurrences of all phrases in *text* (case-insensitive).
        Returns (total_count, list_of_matched_phrases).
        """
        total = 0
        matched: List[str] = []
        for phrase in phrases:
            pattern = re.compile(re.escape(phrase.lower()))
            hits = len(pattern.findall(text))
            if hits > 0:
                total += hits
                matched.append(phrase)
        return total, matched

    def _score_question_ratio(self, prompting: int, commands: int) -> float:
        """
        Score 0-100 based on prompting-to-command ratio.
        Pure prompting → 100; pure commands → 0; balanced → 50.
        """
        total = prompting + commands
        if total == 0:
            return 50.0  # neutral when no phrases detected
        ratio = prompting / total  # [0, 1]
        return round(ratio * 100.0, 2)
