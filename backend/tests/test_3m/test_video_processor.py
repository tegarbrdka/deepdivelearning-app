# Feature: advanced-video-analysis-3m, Property 1: Video Fragmentation Completeness
"""
Property-based tests for VideoProcessor fragmentation logic.
Property 1 from the design document.

NOTE: Tests run against the pure fragmentation math (no actual video files needed).
The VideoProcessor.fragment_video() calls ffmpeg, so we test the fragment
calculation logic directly by extracting it into a helper that mirrors
the production code.
"""
import math
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


FRAGMENT_DURATION_SEC = 300  # mirrors VideoProcessor.FRAGMENT_DURATION_SEC


def compute_fragments(duration: float):
    """
    Pure Python mirror of VideoProcessor.fragment_video() fragment math.
    Returns list of (index, start_sec, end_sec, duration_sec) tuples.
    """
    if duration <= 0:
        return []
    n = math.ceil(duration / FRAGMENT_DURATION_SEC)
    fragments = []
    for i in range(n):
        start = i * FRAGMENT_DURATION_SEC
        end = min(start + FRAGMENT_DURATION_SEC, duration)
        fragments.append((i, start, end, end - start))
    return fragments


# --- Property 1: Video Fragmentation Completeness ---

@given(duration=st.floats(min_value=1.0, max_value=7200.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_every_fragment_duration_lte_300(duration):
    """Every fragment has duration_sec <= 300."""
    fragments = compute_fragments(duration)
    assert len(fragments) > 0
    for idx, start, end, frag_dur in fragments:
        assert frag_dur <= FRAGMENT_DURATION_SEC + 1e-9, (
            f"Fragment {idx} duration {frag_dur:.2f}s exceeds 300s"
        )


@given(duration=st.floats(min_value=1.0, max_value=7200.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_fragments_cover_full_duration(duration):
    """Union of [start, end] intervals covers [0, duration] without gaps."""
    fragments = compute_fragments(duration)
    assert len(fragments) > 0

    # First fragment starts at 0
    assert fragments[0][1] == 0.0, f"First fragment start={fragments[0][1]}, expected 0.0"

    # Last fragment ends at duration
    last_end = fragments[-1][2]
    assert abs(last_end - duration) < 1e-9, (
        f"Last fragment end={last_end:.4f}, expected {duration:.4f}"
    )


@given(duration=st.floats(min_value=1.0, max_value=7200.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_consecutive_fragments_are_contiguous(duration):
    """Consecutive fragments are contiguous: fragment[i].end == fragment[i+1].start."""
    fragments = compute_fragments(duration)
    for i in range(len(fragments) - 1):
        _, _, end_i, _ = fragments[i]
        _, start_next, _, _ = fragments[i + 1]
        assert abs(end_i - start_next) < 1e-9, (
            f"Gap between fragment {i} (end={end_i}) and {i+1} (start={start_next})"
        )


@given(duration=st.floats(min_value=1.0, max_value=7200.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_fragment_count_matches_ceil(duration):
    """Number of fragments == ceil(duration / 300)."""
    fragments = compute_fragments(duration)
    expected = math.ceil(duration / FRAGMENT_DURATION_SEC)
    assert len(fragments) == expected, (
        f"Expected {expected} fragments for duration={duration:.1f}s, got {len(fragments)}"
    )


@given(duration=st.floats(min_value=1.0, max_value=7200.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_fragment_indices_are_sequential(duration):
    """Fragment indices are 0, 1, 2, ... n-1."""
    fragments = compute_fragments(duration)
    for expected_idx, (idx, _, _, _) in enumerate(fragments):
        assert idx == expected_idx, f"Expected index {expected_idx}, got {idx}"


# --- Edge cases ---

def test_exactly_300s_produces_one_fragment():
    fragments = compute_fragments(300.0)
    assert len(fragments) == 1
    assert fragments[0][1] == 0.0
    assert fragments[0][2] == 300.0


def test_301s_produces_two_fragments():
    fragments = compute_fragments(301.0)
    assert len(fragments) == 2
    assert fragments[0][2] == 300.0
    assert abs(fragments[1][2] - 301.0) < 1e-9


def test_remainder_fragment_is_shorter():
    """A 450s video: first fragment 300s, second fragment 150s."""
    fragments = compute_fragments(450.0)
    assert len(fragments) == 2
    assert fragments[0][3] == 300.0
    assert fragments[1][3] == 150.0
