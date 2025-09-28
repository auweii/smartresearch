from pydantic import BaseModel
from typing import Optional, List, Literal, Dict

class FileInfo(BaseModel):
    file_id: str
    old_name: str
    new_name: str
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    size_bytes: int

class JobStart(BaseModel):
    file_ids: List[str]
    max_pages: int = 40
    num_topics: int = 8
    cluster_k: Optional[int] = None
    summary_chars: int = 900
    section_mode: Literal["full", "abstract", "section"] = "abstract"
    section_label: Optional[str] = None
    use_abstractive: bool = True
    abstract_scan_pages: int = 25
    cluster_backend: Literal["auto", "sklearn", "bertopic"] = "auto"   # bertopic added

class JobStatus(BaseModel):
    job_id: str
    state: Literal["QUEUED","PROCESSING","DONE","ERROR"]
    stage: str
    overall_progress: int
    message: Optional[str] = None

class ClusterMember(BaseModel):
    file_id: str
    new_name: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    paper_summary: Optional[str] = None
    key_terms: List[str] = []

class Cluster(BaseModel):
    topic_id: int
    topic_label: str
    summary: str
    members: List[ClusterMember]

class JobResult(BaseModel):
    job_id: str
    clusters: List[Cluster]
    metrics: Dict[str, str | int]
