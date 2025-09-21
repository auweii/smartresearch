from fastapi import APIRouter
from typing import Dict, Any
from ..services.jobs import start_job
from ..services.storage import JOBS
from ..schemas.models import JobStart, JobStatus, JobResult

router = APIRouter()

@router.post("/summarize_cluster")
async def create_job(payload: JobStart):
    job_id = await start_job(payload.dict())
    return {"job_id": job_id}

@router.get("/{job_id}/status", response_model=JobStatus)
async def job_status(job_id: str):
    j = JOBS.get(job_id)
    if not j:
        return {"job_id": job_id, "state":"ERROR", "stage":"missing", "overall_progress":0, "message":"Not found"}
    return {"job_id": job_id, **{k: j[k] for k in ["state","stage","overall_progress","message"]}}

@router.get("/{job_id}/result", response_model=JobResult | dict)
async def job_result(job_id: str):
    j = JOBS.get(job_id)
    if not j or j.get("state") != "DONE":
        return {"error": "Result not ready"}
    return {"job_id": job_id, **(j["result"] or {})}
