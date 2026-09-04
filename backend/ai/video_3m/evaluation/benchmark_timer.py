"""
PipelineTimer — context manager and utilities for benchmarking
processing time of each stage in the 3M video analysis pipeline.

Usage:
    timer = PipelineTimer()
    with timer.stage("fragmenting"):
        processor.fragment_video(...)
    with timer.stage("audio_processing"):
        run_audio_analysis(...)
    
    report = timer.get_report()
    # → {"fragmenting": {"mean_sec": 12.3, ...}, ...}
"""
from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Dict, List

from backend.ai.video_3m.evaluation.metrics import ProcessingTimeResult


class PipelineTimer:
    """
    Accumulates timing measurements for pipeline stages.
    Thread-safe for sequential use; not designed for concurrent access.
    """

    def __init__(self):
        self._times: Dict[str, List[float]] = defaultdict(list)
        self._current_stage: str | None = None
        self._start_time: float | None = None

    @contextmanager
    def stage(self, name: str):
        """Context manager to time a pipeline stage."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self._times[name].append(elapsed)

    def start(self, name: str) -> None:
        """Manually start timing a stage (use with stop())."""
        self._current_stage = name
        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop timing the current stage. Returns elapsed seconds."""
        if self._start_time is None or self._current_stage is None:
            return 0.0
        elapsed = time.perf_counter() - self._start_time
        self._times[self._current_stage].append(elapsed)
        self._current_stage = None
        self._start_time = None
        return elapsed

    def record(self, name: str, elapsed_sec: float) -> None:
        """Manually record a timing measurement."""
        self._times[name].append(elapsed_sec)

    def get_results(self) -> List[ProcessingTimeResult]:
        """Get timing results as a list of ProcessingTimeResult objects."""
        results = []
        for stage_name, times in self._times.items():
            results.append(ProcessingTimeResult(
                stage=stage_name,
                times_sec=list(times),
            ))
        return results

    def get_report(self) -> Dict[str, dict]:
        """Get timing report as a plain dict."""
        report = {}
        for result in self.get_results():
            report[result.stage] = {
                "mean_sec": round(result.mean_sec, 3),
                "std_sec": round(result.std_sec, 3),
                "min_sec": round(result.min_sec, 3),
                "max_sec": round(result.max_sec, 3),
                "n_runs": len(result.times_sec),
            }
        return report

    def get_total_time(self) -> float:
        """Get total elapsed time across all stages."""
        total = 0.0
        for times in self._times.values():
            total += sum(times)
        return round(total, 3)

    def reset(self) -> None:
        """Clear all recorded timings."""
        self._times.clear()
        self._current_stage = None
        self._start_time = None

    def __repr__(self) -> str:
        report = self.get_report()
        lines = [f"PipelineTimer (total: {self.get_total_time():.3f}s)"]
        for stage, data in report.items():
            lines.append(f"  {stage}: {data['mean_sec']:.3f}s ± {data['std_sec']:.3f}s")
        return "\n".join(lines)
