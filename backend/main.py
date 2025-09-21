from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from smartresearch_backend.api.router_files import router as files_router
from smartresearch_backend.api.router_jobs import router as jobs_router
from smartresearch_backend.services.storage import UPLOAD_DIR

app = FastAPI(title="SmartResearch Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(files_router, prefix="/files", tags=["files"])
app.include_router(jobs_router,  prefix="/jobs",  tags=["jobs"])
