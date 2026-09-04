# Feature: advanced-video-analysis-3m, Property 2: Mindful Score Weighted Formula
# Feature: advanced-video-analysis-3m, Property 3: Meaningful Score Weighted Formula
# Feature: advanced-video-analysis-3m, Property 4: Joyful Score Weighted Formula
"""
Property-based tests for ScoreAggregator weighted formulas.
Properties 2, 3, 4 from the design document.
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backend.ai.video_3m.aggregation.score_aggregator import ScoreAggregator
from backend.ai.video_3m.data_models import (
    FragmentAnalysis,
    VideoFragment,
    MindfulResult,
    MeaningfulResult,
    JoyfulResult,
)

SCORE_RANGE = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)


def make_fragment(index: int = 0, start: float = 0.0, end: float = 300.0) -> VideoFragment:
    return VideoFragment(index=index, path="", start_sec=start, end_sec=end, duration_sec=end - start)


# ─── Property 2: Mindful Score Weighted Formula ─────────────────────────────

@given(
    gaze=SCORE_RANGE,
    posture=SCORE_RANGE,
    silence=SCORE_RANGE,
)
@settings(max_examples=100)
def test_mindful_score_weighted_formula(gaze, posture, silence):
    """
    mindful_score == 0.40 * gaze + 0.35 * posture + 0.25 * silence_quality
    Result must be in [0, 100].
    """
    aggregator = ScoreAggregator()
    mindful = MindfulResult(
        gaze_score=gaze,
        posture_score=posture,
        silence_quality_score=silence,
        mindful_score=0.0,  # will be recomputed by aggregator
    )
    meaningful = MeaningfulResult()
    joyful = JoyfulResult()
    fragment = make_fragment()

    result = aggregator.aggregate([FragmentAnalysis(fragment=fragment, mindful=mindful, meaningful=meaningful, joyful=joyful)])

    expected = 0.40 * gaze + 0.35 * posture + 0.25 * silence
    assert abs(result.mindful_score - expected) < 0.1, (
        f"mindful_score={result.mindful_score} expected≈{expected}"
    )
    assert 0.0 <= result.mindful_score <= 100.0


# ─── Property 3: Meaningful Score Weighted Formula ──────────────────────────

@given(
    seating=SCORE_RANGE,
    talk_time=SCORE_RANGE,
    teacher_movement=SCORE_RANGE,
)
@settings(max_examples=100)
def test_meaningful_score_weighted_formula(seating, talk_time, teacher_movement):
    """
    meaningful_score == 0.30*seating + 0.40*talk_time + 0.30*teacher_movement
    Result must be in [0, 100].
    """
    aggregator = ScoreAggregator()
    mindful = MindfulResult()
    meaningful = MeaningfulResult(
        seating_score=seating,
        talk_time_score=talk_time,
        question_type_score=50.0,  # omitted from score but still in result
        teacher_movement_score=teacher_movement,
    )
    joyful = JoyfulResult()
    fragment = make_fragment()

    result = aggregator.aggregate([FragmentAnalysis(fragment=fragment, mindful=mindful, meaningful=meaningful, joyful=joyful)])

    expected = 0.30 * seating + 0.40 * talk_time + 0.30 * teacher_movement
    assert abs(result.meaningful_score - expected) < 0.1, (
        f"meaningful_score={result.meaningful_score} expected≈{expected}"
    )
    assert 0.0 <= result.meaningful_score <= 100.0


# ─── Property 4: Joyful Score Weighted Formula ──────────────────────────────

@given(
    expression=SCORE_RANGE,
    acoustic=SCORE_RANGE,
    collaboration=SCORE_RANGE,
    risk_taking=SCORE_RANGE,
)
@settings(max_examples=100)
def test_joyful_score_weighted_formula(expression, acoustic, collaboration, risk_taking):
    """
    joyful_score == 0.30*expression + 0.30*acoustic + 0.25*collaboration + 0.15*risk_taking
    Result must be in [0, 100].
    """
    aggregator = ScoreAggregator()
    mindful = MindfulResult()
    meaningful = MeaningfulResult()
    joyful = JoyfulResult(
        expression_score=expression,
        acoustic_score=acoustic,
        collaboration_score=collaboration,
        risk_taking_score=risk_taking,
    )
    fragment = make_fragment()

    result = aggregator.aggregate([FragmentAnalysis(fragment=fragment, mindful=mindful, meaningful=meaningful, joyful=joyful)])

    expected = 0.30 * expression + 0.30 * acoustic + 0.25 * collaboration + 0.15 * risk_taking
    assert abs(result.joyful_score - expected) < 0.1, (
        f"joyful_score={result.joyful_score} expected≈{expected}"
    )
    assert 0.0 <= result.joyful_score <= 100.0


# ─── Overall 3M score is in [0, 100] ────────────────────────────────────────

@given(
    mindful=SCORE_RANGE,
    meaningful=SCORE_RANGE,
    joyful=SCORE_RANGE,
)
@settings(max_examples=100)
def test_overall_3m_score_in_range(mindful, meaningful, joyful):
    """overall_3m_score = 0.33*mindful + 0.34*meaningful + 0.33*joyful, must be in [0, 100]."""
    aggregator = ScoreAggregator()
    fragment = make_fragment()
    fa = FragmentAnalysis(
        fragment=fragment,
        mindful=MindfulResult(gaze_score=mindful, posture_score=mindful, silence_quality_score=mindful),
        meaningful=MeaningfulResult(seating_score=meaningful, talk_time_score=meaningful,
                                    question_type_score=meaningful, teacher_movement_score=meaningful),
        joyful=JoyfulResult(expression_score=joyful, acoustic_score=joyful,
                            collaboration_score=joyful, risk_taking_score=joyful),
    )
    result = aggregator.aggregate([fa])
    assert 0.0 <= result.overall_3m_score <= 100.0
