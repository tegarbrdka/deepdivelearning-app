"""
Simple asyncio-based job queue for 3M video analysis.
Limits concurrent pipeline executions to MAX_CONCURRENT_JOBS.
"""
from __future__ import annotations

import asyncio
from typing import Optional, Dict
from fastapi import BackgroundTasks


class VideoAnalysisJobQueue:
    """
    Manages concurrent pipeline executions.
    Reads MAX_CONCURRENT_JOBS from SystemConfig (default: 2).
    """

    def __init__(self):
        self._active: Dict[str, bool] = {}
        self._pending: list = []  # list of (job_id, video_path, rpp_path)
        self._lock = asyncio.Lock()

    def _get_max_concurrent(self) -> int:
        try:
            from backend.database import SessionLocal
            from backend.models.db_models import SystemConfig
            db = SessionLocal()
            try:
                cfg = db.query(SystemConfig).filter(
                    SystemConfig.key == "max_concurrent_jobs"
                ).first()
                return int(cfg.value) if cfg else 2
            finally:
                db.close()
        except Exception:
            return 2

    async def enqueue(
        self,
        job_id: str,
        video_path: str,
        rpp_path: Optional[str],
        background_tasks: BackgroundTasks,
    ) -> None:
        """Enqueue a job. Starts immediately if a slot is available."""
        max_jobs = self._get_max_concurrent()

        if len(self._active) < max_jobs:
            self._active[job_id] = True
            background_tasks.add_task(self._run_and_release, job_id, video_path, rpp_path)
        else:
            # Mark as queued in DB (already done by router), add to pending
            self._pending.append((job_id, video_path, rpp_path))
            background_tasks.add_task(self._wait_and_run, job_id, video_path, rpp_path)

    async def _run_and_release(
        self,
        job_id: str,
        video_path: str,
        rpp_path: Optional[str],
    ) -> None:
        """Run the pipeline and release the slot when done."""
        try:
            from backend.ai.video_3m.pipeline import VideoAnalysisPipeline
            pipeline = VideoAnalysisPipeline()
            await pipeline.run(job_id, video_path, rpp_path)
        finally:
            self._active.pop(job_id, None)
            await self._start_next()

    async def _wait_and_run(
        self,
        job_id: str,
        video_path: str,
        rpp_path: Optional[str],
    ) -> None:
        """Wait until a slot opens, then run."""
        max_jobs = self._get_max_concurrent()
        while len(self._active) >= max_jobs:
            await asyncio.sleep(5)

        self._active[job_id] = True
        # Remove from pending list
        self._pending = [p for p in self._pending if p[0] != job_id]
        await self._run_and_release(job_id, video_path, rpp_path)

    async def _start_next(self) -> None:
        """Start the next pending job if a slot is available."""
        max_jobs = self._get_max_concurrent()
        if self._pending and len(self._active) < max_jobs:
            job_id, video_path, rpp_path = self._pending.pop(0)
            self._active[job_id] = True
            asyncio.create_task(self._run_and_release(job_id, video_path, rpp_path))

    def get_queue_status(self) -> dict:
        return {
            "active_jobs": list(self._active.keys()),
            "active_count": len(self._active),
            "pending_count": len(self._pending),
            "max_concurrent": self._get_max_concurrent(),
        }


# Global singleton
job_queue = VideoAnalysisJobQueue()
