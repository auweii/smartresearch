# backend/app.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, uuid, asyncio
from typing import List, Dict, Any

from smartresearch_backend.libs.pdf_rename_embed import rename_folder

# ----------------- FastAPI -----------------
app = FastAPI(title="SmartResearch Backend", version="0.1.0")

# CORS so Next.js can call us in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# simple in-memory job store (swap for Redis later)
JOBS: Dict[str, Dict[str, Any]] = {}


# ----------- health -----------
@app.get("/health")
def health():
    return {"ok": True}


# ----------- upload (rename + embed) -----------
@app.post("/files")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Accept 1+ PDFs. We save to data/uploads, then run the renamer on that folder.
    Returns: one dict per uploaded file with cleaned metadata & new_name.
    """
    # 1) save all incoming files (raw)
    for f in files:
        raw_path = os.path.join(UPLOAD_DIR, f.filename)
        with open(raw_path, "wb") as out:
            shutil.copyfileobj(f.file, out)

    # 2) run renamer on UPLOAD_DIR (apply=True embeds metadata + renames)
    out = []
    for status, old, new, title, authors, year in rename_folder(
        UPLOAD_DIR, apply=True, pages=2, mode="auto"
    ):
        # only return entries that correspond to files we just uploaded
        try:
            size = os.path.getsize(os.path.join(UPLOAD_DIR, new))
        except FileNotFoundError:
            size = 0
        out.append({
            "file_id": uuid.uuid4().hex[:8],
            "old_name": old,
            "new_name": new,
            "title": title,
            "authors": authors,
            "year": year,
            "size_bytes": size,
        })
    return out


# ----------- summarize + cluster job API -----------
@app.post("/jobs/summarize_cluster")
async def start_job(payload: Dict[str, Any]):
    """
    Start a background job that will (later) summarize + cluster uploaded PDFs.
    For now it simulates work so the frontend progress bar moves.
    payload:
      - file_ids: list[str]
      - summary_model, max_pages, chunk_size, etc. (optional)
    """
    job_id = f"job_{uuid.uuid4().hex[:6]}"
    JOBS[job_id] = {
        "state": "QUEUED",
        "stage": "queued",
        "overall_progress": 0,
        "files": [{"file_id": fid, "progress": 0, "stage": "queued"} for fid in payload.get("file_ids", [])],
        "message": "Queued",
        "result": None,
    }
    asyncio.create_task(run_job(job_id, payload))
    return {"job_id": job_id}

@app.get("/jobs/{job_id}/status")
async def job_status(job_id: str):
    return {"job_id": job_id, **JOBS.get(job_id, {"state":"ERROR","message":"Not found"})}

@app.get("/jobs/{job_id}/result")
async def job_result(job_id: str):
    j = JOBS.get(job_id)
    if not j or j["state"] != "DONE":
        return {"error": "Result not ready"}
    return {"job_id": job_id, **(j["result"] or {})}


# ----------- background job (fake for now) -----------
async def run_job(job_id: str, cfg: Dict[str, Any]):
    j = JOBS[job_id]
    try:
        # simulate summarizing
        j.update({"state":"PROCESSING","stage":"summarizing","message":"Summarizing...","overall_progress":10})
        await asyncio.sleep(1.0)

        # simulate clustering
        j.update({"stage":"clustering","message":"Clustering...","overall_progress":70})
        await asyncio.sleep(1.0)

        # fake result
        j["result"] = {
            "clusters": [
                {"topic_id": 0, "topic_label": "Example Topic", "summary": "Example summary", "members": []}
            ],
            "metrics": {"k": 1, "method": "kmeans", "embedding": "all-MiniLM"},
        }
        j.update({"state":"DONE","stage":"finished","overall_progress":100,"message":"Done"})
    except Exception as e:
        j.update({"state":"ERROR","message":str(e)})
