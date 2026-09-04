import pytest
from unittest.mock import MagicMock
from backend.ai.video_3m.aggregation.evidence_extractor import EvidenceExtractor
from backend.ai.video_3m.data_models import AggregatedResult

class MockEvidenceExtractor(EvidenceExtractor):
    """Subclass to bypass moviepy file operations and return success."""
    def _extract_clip(self, video_path: str, output_path: str, start_sec: float, end_sec: float) -> bool:
        return True

def test_evidence_extractor_short_video():
    """
    Test that for a short video (< 90 seconds) where multiple clips must overlap,
    clips do not start at the exact same second.
    """
    extractor = MockEvidenceExtractor()
    
    # 1 fragment, total duration 60 seconds
    analysis = AggregatedResult(
        video_duration_sec=60.0,
        timeline_data=[
            {
                "index": 0,
                "start_sec": 0.0,
                "end_sec": 60.0,
                "mindful": 80.0,
                "meaningful": 75.0,
                "joyful": 90.0,
            }
        ]
    )
    
    clips = extractor.extract_clips(
        video_path="dummy.mp4",
        analysis=analysis,
        output_dir="dummy_out",
        job_id="test_job"
    )
    
    # We expect 6 clips (3 best_practice + 3 improvement)
    assert len(clips) == 6
    
    # Check that start times are distinct (e.g. no two clips have the exact same start_sec)
    start_times = [c.start_sec for c in clips]
    unique_start_times = set(start_times)
    
    # Since video is 60 seconds long and we extract 6 clips of 15 seconds,
    # they must be spaced out and start at different positions.
    assert len(unique_start_times) == 6
    
    # Assert all start times are within valid bounds (0.0 to 45.0)
    for c in clips:
        assert 0.0 <= c.start_sec <= 45.0
        assert c.end_sec == c.start_sec + 15.0

def test_evidence_extractor_long_video():
    """
    Test that for a long video (e.g., 30 minutes), clips targeting different fragments
    or the same fragment are chosen with zero overlap if possible.
    """
    extractor = MockEvidenceExtractor()
    
    # 6 fragments of 5 minutes each (30 minutes total)
    timeline_data = []
    for i in range(6):
        timeline_data.append({
            "index": i,
            "start_sec": i * 300.0,
            "end_sec": (i + 1) * 300.0,
            # Force peak moments in different fragments
            "mindful": 99.0 if i == 0 else (10.0 if i == 1 else 50.0),
            "meaningful": 99.0 if i == 2 else (10.0 if i == 3 else 50.0),
            "joyful": 99.0 if i == 4 else (10.0 if i == 5 else 50.0),
        })
        
    analysis = AggregatedResult(
        video_duration_sec=1800.0,
        timeline_data=timeline_data
    )
    
    clips = extractor.extract_clips(
        video_path="dummy.mp4",
        analysis=analysis,
        output_dir="dummy_out",
        job_id="test_job"
    )
    
    assert len(clips) == 6
    
    # Verify no two clips overlap at all (absolute difference between start times >= 15.0)
    sorted_clips = sorted(clips, key=lambda c: c.start_sec)
    for idx in range(len(sorted_clips) - 1):
        c1 = sorted_clips[idx]
        c2 = sorted_clips[idx + 1]
        assert c2.start_sec - c1.start_sec >= 15.0, f"Clips {c1} and {c2} overlap"
