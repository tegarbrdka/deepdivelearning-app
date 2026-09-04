# Feature: advanced-video-analysis-3m, Property 7: Indonesian Phrase Detection and Classification
# Feature: advanced-video-analysis-3m, Property 8: Question Type Score Monotonicity
"""
Property-based tests for NLPAnalyzer phrase detection and scoring.
Properties 7 and 8 from the design document.
"""
import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from backend.ai.video_3m.audio.nlp_analyzer import NLPAnalyzer
from backend.ai.video_3m.data_models import (
    TranscriptResult,
    TranscriptSegment,
    DiarizationResult,
    DiarizationSegment,
)

NON_NEGATIVE_INT = st.integers(min_value=0, max_value=50)


def make_transcript_with_text(text: str) -> TranscriptResult:
    """Build a TranscriptResult with a single segment containing the given text."""
    seg = TranscriptSegment(start=0.0, end=10.0, text=text)
    return TranscriptResult(segments=[seg], full_text=text)


def make_teacher_diarization() -> DiarizationResult:
    """Build a DiarizationResult where the entire duration is teacher speech."""
    return DiarizationResult(
        segments=[DiarizationSegment(start=0.0, end=10.0, speaker="SPEAKER_00")],
        teacher_speaker="SPEAKER_00",
    )


# ─── Property 7: Indonesian Phrase Detection and Classification ──────────────

@given(
    prompting_phrase=st.sampled_from(NLPAnalyzer.PROMPTING_PHRASES),
    filler=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu")), max_size=20),
)
@settings(max_examples=100)
def test_prompting_phrase_detected(prompting_phrase, filler):
    """
    When transcript contains a known prompting phrase, prompting_count >= 1.
    """
    text = f"{filler} {prompting_phrase} {filler}"
    analyzer = NLPAnalyzer()
    transcript = make_transcript_with_text(text)
    diarization = make_teacher_diarization()

    result = analyzer.analyze_transcript(transcript, diarization)

    assert result.prompting_count >= 1, (
        f"Expected prompting_count >= 1 for phrase '{prompting_phrase}', got {result.prompting_count}"
    )


@given(
    command_phrase=st.sampled_from(NLPAnalyzer.COMMAND_PHRASES),
    filler=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu")), max_size=20),
)
@settings(max_examples=100)
def test_command_phrase_detected(command_phrase, filler):
    """
    When transcript contains a known command phrase, command_count >= 1.
    """
    text = f"{filler} {command_phrase} {filler}"
    analyzer = NLPAnalyzer()
    transcript = make_transcript_with_text(text)
    diarization = make_teacher_diarization()

    result = analyzer.analyze_transcript(transcript, diarization)

    assert result.command_count >= 1, (
        f"Expected command_count >= 1 for phrase '{command_phrase}', got {result.command_count}"
    )


@given(
    prompting_phrase=st.sampled_from(NLPAnalyzer.PROMPTING_PHRASES),
)
@settings(max_examples=50)
def test_only_prompting_has_zero_commands(prompting_phrase):
    """
    Transcript with only prompting phrases (no command phrases) → command_count == 0.
    """
    # Use a phrase that doesn't overlap with any command phrase
    text = f"guru bertanya {prompting_phrase} kepada siswa"
    analyzer = NLPAnalyzer()
    transcript = make_transcript_with_text(text)
    diarization = make_teacher_diarization()

    result = analyzer.analyze_transcript(transcript, diarization)

    # Verify no command phrases are in the text
    text_lower = text.lower()
    has_command = any(cmd in text_lower for cmd in NLPAnalyzer.COMMAND_PHRASES)
    if not has_command:
        assert result.command_count == 0, (
            f"Expected command_count == 0 for prompting-only text, got {result.command_count}"
        )


@given(
    command_phrase=st.sampled_from(NLPAnalyzer.COMMAND_PHRASES),
)
@settings(max_examples=50)
def test_only_commands_has_zero_prompting(command_phrase):
    """
    Transcript with only command phrases (no prompting phrases) → prompting_count == 0.
    """
    text = f"guru berkata {command_phrase} kepada kelas"
    analyzer = NLPAnalyzer()
    transcript = make_transcript_with_text(text)
    diarization = make_teacher_diarization()

    result = analyzer.analyze_transcript(transcript, diarization)

    # Verify no prompting phrases are in the text
    text_lower = text.lower()
    has_prompting = any(p in text_lower for p in NLPAnalyzer.PROMPTING_PHRASES)
    if not has_prompting:
        assert result.prompting_count == 0, (
            f"Expected prompting_count == 0 for command-only text, got {result.prompting_count}"
        )


# ─── Property 8: Question Type Score Monotonicity ───────────────────────────

@given(
    prompting=NON_NEGATIVE_INT,
    commands=NON_NEGATIVE_INT,
)
@settings(max_examples=100)
def test_question_score_in_range(prompting, commands):
    """question_type_score is always in [0, 100]."""
    analyzer = NLPAnalyzer()
    score = analyzer._score_question_ratio(prompting, commands)
    assert 0.0 <= score <= 100.0, f"Score {score} out of [0, 100]"


@given(
    prompting_low=NON_NEGATIVE_INT,
    prompting_high=NON_NEGATIVE_INT,
    commands=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=100)
def test_question_score_monotonicity(prompting_low, prompting_high, commands):
    """
    Higher prompting-to-command ratio always produces higher or equal question_type_score.
    """
    assume(prompting_high >= prompting_low)

    analyzer = NLPAnalyzer()
    score_low = analyzer._score_question_ratio(prompting_low, commands)
    score_high = analyzer._score_question_ratio(prompting_high, commands)

    assert score_high >= score_low - 0.01, (
        f"score({prompting_high}/{commands})={score_high} < score({prompting_low}/{commands})={score_low}"
    )


def test_pure_prompting_scores_100():
    """All prompting, no commands → score == 100."""
    analyzer = NLPAnalyzer()
    assert analyzer._score_question_ratio(10, 0) == 100.0


def test_pure_commands_scores_0():
    """All commands, no prompting → score == 0."""
    analyzer = NLPAnalyzer()
    assert analyzer._score_question_ratio(0, 10) == 0.0


def test_no_phrases_scores_50():
    """No phrases detected → neutral score of 50."""
    analyzer = NLPAnalyzer()
    assert analyzer._score_question_ratio(0, 0) == 50.0
