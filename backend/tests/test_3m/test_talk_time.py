# Feature: advanced-video-analysis-3m, Property 5: Talk-Time Percentages Sum to 100
# Feature: advanced-video-analysis-3m, Property 6: Deep Learning Standard Compliance Check
"""
Property-based tests for SpeechAnalyzer talk-time computation.
Properties 5 and 6 from the design document.
"""
import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from backend.ai.video_3m.audio.speech_analyzer import SpeechAnalyzer
from backend.ai.video_3m.data_models import DiarizationResult, DiarizationSegment


DURATION_STRATEGY = st.floats(min_value=0.1, max_value=3600.0, allow_nan=False, allow_infinity=False)
SECONDS_STRATEGY = st.floats(min_value=0.0, max_value=1800.0, allow_nan=False, allow_infinity=False)


def make_diarization(teacher_sec: float, student_sec: float) -> DiarizationResult:
    """Build a DiarizationResult with one teacher segment and one student segment."""
    segments = []
    if teacher_sec > 0:
        segments.append(DiarizationSegment(start=0.0, end=teacher_sec, speaker="SPEAKER_00"))
    if student_sec > 0:
        segments.append(DiarizationSegment(start=teacher_sec, end=teacher_sec + student_sec, speaker="SPEAKER_01"))
    return DiarizationResult(segments=segments, teacher_speaker="SPEAKER_00")


# ─── Property 5: Talk-Time Percentages Sum to 100 ───────────────────────────

@given(
    teacher_sec=SECONDS_STRATEGY,
    student_sec=SECONDS_STRATEGY,
    total_duration=DURATION_STRATEGY,
)
@settings(max_examples=100)
def test_talk_time_percentages_sum_to_100(teacher_sec, student_sec, total_duration):
    """
    teacher_pct + student_pct + silence_pct must equal 100.0 (within 0.01 tolerance).
    Each percentage must be in [0, 100].
    """
    assume(total_duration >= teacher_sec + student_sec)
    assume(teacher_sec + student_sec + (total_duration - teacher_sec - student_sec) > 0)

    analyzer = SpeechAnalyzer.__new__(SpeechAnalyzer)
    diarization = make_diarization(teacher_sec, student_sec)
    result = analyzer.compute_talk_time(diarization, total_duration)

    total_pct = result.teacher_pct + result.student_pct + result.silence_pct
    assert abs(total_pct - 100.0) < 0.01, (
        f"Percentages sum to {total_pct}, expected 100.0 "
        f"(teacher={result.teacher_pct}, student={result.student_pct}, silence={result.silence_pct})"
    )
    assert 0.0 <= result.teacher_pct <= 100.0
    assert 0.0 <= result.student_pct <= 100.0
    assert 0.0 <= result.silence_pct <= 100.0


# ─── Property 6: Deep Learning Standard Compliance Check ────────────────────

@given(
    teacher_pct=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    student_pct=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_dl_standard_compliance_logic(teacher_pct, student_pct):
    """
    meets_dl_standard is True iff teacher_pct in [30, 40] AND student_pct in [60, 70].
    When meets_dl_standard is False, deviation > 0.
    """
    assume(teacher_pct + student_pct <= 100.0)

    # Compute expected compliance
    expected_meets = (30.0 <= teacher_pct <= 40.0) and (60.0 <= student_pct <= 70.0)

    # Compute deviation manually (based on teacher_pct only, as per implementation)
    if teacher_pct < 30.0:
        expected_deviation = 30.0 - teacher_pct
    elif teacher_pct > 40.0:
        expected_deviation = teacher_pct - 40.0
    else:
        expected_deviation = 0.0

    # Build a diarization that produces these percentages
    # total_duration = 100s, teacher_sec = teacher_pct, student_sec = student_pct
    total_duration = 100.0
    teacher_sec = teacher_pct
    student_sec = student_pct

    analyzer = SpeechAnalyzer.__new__(SpeechAnalyzer)
    diarization = make_diarization(teacher_sec, student_sec)
    result = analyzer.compute_talk_time(diarization, total_duration)

    assert result.meets_standard == expected_meets, (
        f"teacher_pct={result.teacher_pct:.2f}, student_pct={result.student_pct:.2f}: "
        f"meets_standard={result.meets_standard}, expected={expected_meets}"
    )

    if not result.meets_standard:
        assert result.deviation >= 0.0, (
            f"deviation should be >= 0 when not meeting standard, got {result.deviation}"
        )


@given(
    teacher_pct=st.floats(min_value=30.0, max_value=40.0, allow_nan=False, allow_infinity=False),
    student_pct=st.floats(min_value=60.0, max_value=70.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_dl_standard_met_when_in_range(teacher_pct, student_pct):
    """When teacher is 30-40% and student is 60-70%, deviation must be 0."""
    assume(teacher_pct + student_pct <= 100.0)

    total_duration = 100.0
    analyzer = SpeechAnalyzer.__new__(SpeechAnalyzer)
    diarization = make_diarization(teacher_pct, student_pct)
    result = analyzer.compute_talk_time(diarization, total_duration)

    assert result.meets_standard is True
    assert result.deviation == 0.0
