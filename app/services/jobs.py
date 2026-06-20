"""In-memory async job manager for slicing large models.

A job runs the same slicing pipeline as the synchronous endpoint, but in the
background so the client can poll instead of holding a long request open. Jobs
live in memory only — they do not survive a restart — and the most recent
``JOB_RETENTION`` finished jobs are kept.
"""
import asyncio
import time
import uuid
from collections import OrderedDict
from typing import Awaitable, Callable, Optional

from ..config import JOB_RETENTION
from ..core.errors import APIError
from ..models import SliceResponse

# A runner produces the SliceResponse (and is responsible for its own cleanup).
Runner = Callable[[], Awaitable[SliceResponse]]


class Job:
    def __init__(self, job_id: str):
        self.id = job_id
        self.status = "pending"  # pending | running | succeeded | failed
        self.created_at = time.time()
        self.finished_at: Optional[float] = None
        self.result: Optional[SliceResponse] = None
        self.error_code: Optional[str] = None
        self.error_message: Optional[str] = None

    def to_status(self) -> dict:
        payload = {
            "job_id": self.id,
            "status": self.status,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "result": self.result,
            "error": None,
        }
        if self.error_code:
            payload["error"] = {"code": self.error_code, "message": self.error_message}
        return payload


class JobManager:
    def __init__(self, retention: int = JOB_RETENTION):
        self._jobs: "OrderedDict[str, Job]" = OrderedDict()
        self._retention = retention
        self._lock = asyncio.Lock()

    async def submit(self, runner: Runner) -> Job:
        job = Job(uuid.uuid4().hex)
        async with self._lock:
            self._jobs[job.id] = job
            self._prune()
        asyncio.create_task(self._run(job, runner))
        return job

    async def get(self, job_id: str) -> Optional[Job]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def _run(self, job: Job, runner: Runner) -> None:
        job.status = "running"
        try:
            job.result = await runner()
            job.status = "succeeded"
        except APIError as exc:
            job.status = "failed"
            job.error_code = exc.code
            job.error_message = exc.detail
        except Exception as exc:  # noqa: BLE001 - surface any failure to the caller
            job.status = "failed"
            job.error_code = "INTERNAL_ERROR"
            job.error_message = str(exc)
        finally:
            job.finished_at = time.time()

    def _prune(self) -> None:
        # Drop oldest *finished* jobs beyond the retention limit.
        while len(self._jobs) > self._retention:
            for job_id, job in list(self._jobs.items()):
                if job.status in ("succeeded", "failed"):
                    del self._jobs[job_id]
                    break
            else:
                break


job_manager = JobManager()
