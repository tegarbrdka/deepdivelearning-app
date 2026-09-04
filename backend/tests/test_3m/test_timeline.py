# Feature: advanced-video-analysis-3m, Property 15: Pedagogical Timeline Ordering and Completeness
"""
Property-based tests for pedagogical timeline ordering and completeness.
Property 15 from the design document.
"""
import pytest
from hypothesis import given, assume, settings
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


def make_fragment_analysis(index: int, start_sec: float, end_sec: float) -> FragmentAnalysis:
    """Build a minimal FragmentAnalysis for a given time window."""
    fragment = VideoFragment(
        index=index,
        path=f"fragment_{index}.mp4",
        start_sec=start_sec,
        end_sec=end_sec,
        duration_sec=end_sec - start_sec,
    )
    return FragmentAnalysis(
        fragment=fragment,
        mindful=MindfulResult(gaze_score=50.0, posture_score=50.0, silence_quality_score=50.0),
        meaningful=MeaningfulResult(seating_score=50.0, talk_time_score=50.0,
                                    question_type_score=50.0, teacher_movement_score=50.0),
        joyful=JoyfulResult(expression_score=50.0, acoustic_score=50.0,
                            collaboration_score=50.0, risk_taking_score=50.0),
    )


@given(
    n_fragments=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_timeline_has_exactly_n_entries(n_fragments):
    """
    Timeline contains exactly N entries for N fragments.
    """
    fragment_analyses = [
        make_fragment_analysis(i, i * 300.0, (i + 1) * 300.0)
        for i in range(n_fragments)
    ]

    aggregator = ScoreAggregator()
    result = aggregator.aggregate(fragment_analyses)

    assert len(result.timeline_data) == n_fragments, (
        f"Expected {n_fragments} timeline entries, got {len(result.timeline_data)}"
    )


@given(
    n_fragments=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_timeline_ordered_by_start_sec(n_fragments):
    """
    Timeline entries are ordered by ascending start_sec.
    """
    import random
    # Create fragments in shuffled order to test sorting
    indices = list(range(n_fragments))
    random.shuffle(indices)

    fragment_analyses = [
        make_fragment_analysis(i, i * 300.0, (i + 1) * 300.0)
        for i in indices
    ]

    aggregator = ScoreAggregator()
    result = aggregator.aggregate(fragment_analyses)

    start_secs = [entry["start_sec"] for entry in result.timeline_data]
    assert start_secs == sorted(start_secs), (
        f"Timeline not ordered by start_sec: {start_secs}"
    )


@given(
    n_fragments=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_timeline_entries_have_correct_fragment_indices(n_fragments):
    """
    Each timeline entry references the correct fragment_index.
    """
    fragment_analyses = [
        make_fragment_analysis(i, i * 300.0, (i + 1) * 300.0)
        for i in range(n_fragments)
    ]

    aggregator = ScoreAggregator()
    result = aggregator.aggregate(fragment_analyses)

    # After sorting by start_sec, indices should be 0..n-1
    for entry in result.timeline_data:
        assert "index" in entry, "Timeline entry missing 'index' field"
        assert 0 <= entry["index"] < n_fragments, (
            f"Fragment index {entry['index']} out of range [0, {n_fragments})"
        )


@given(
    n_fragments=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_timeline_entries_have_required_fields(n_fragments):
    """
    Each timeline entry has all required fields: index, start_sec, end_sec, label,
    mindful, meaningful, joyful.
    """
    fragment_analyses = [
        make_fragment_analysis(i, i * 300.0, (i + 1) * 300.0)
        for i in range(n_fragments)
    ]

    aggregator = ScoreAggregator()
    result = aggregator.aggregate(fragment_analyses)

    required_fields = {"index", "start_sec", "end_sec", "label", "mindful", "meaningful", "joyful"}
    for i, entry in enumerate(result.timeline_data):
        missing = required_fields - set(entry.keys())
        assert not missing, f"Timeline entry {i} missing fields: {missing}"


def test_empty_fragments_returns_empty_timeline():
    """Aggregating zero fragments returns empty timeline."""
    aggregator = ScoreAggregator()
    result = aggregator.aggregate([])
    assert result.timeline_data == []


def test_single_fragment_timeline():
    """Single fragment produces exactly one timeline entry."""
    fa = make_fragment_analysis(0, 0.0, 300.0)
    aggregator = ScoreAggregator()
    result = aggregator.aggregate([fa])

    assert len(result.timeline_data) == 1
    entry = result.timeline_data[0]
    assert entry["start_sec"] == 0.0
    assert entry["end_sec"] == 300.0
    assert entry["index"] == 0
