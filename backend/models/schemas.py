from pydantic import BaseModel, Field
from typing import List, Optional

# document and metadata schemas
class DocMeta(BaseModel):
    """basic info about a stored document"""
    id: str
    name: str
    n_chars: int


class Metadata(BaseModel):
    """optional bibliographic metadata (e.g., from CrossRef)"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    publisher: Optional[str] = None


# upload and summarization
class UploadResponse(BaseModel):
    """response payload for document upload"""
    doc: DocMeta
    preview: str
    used_ocr: bool = False  # true if OCR was used instead of direct extraction
    meta: Optional[Metadata] = None


class SummarizeRequest(BaseModel):
    """request for extractive summary (text or doc IDs)"""
    text: Optional[str] = None
    doc_ids: Optional[List[str]] = None
    max_sentences: int = Field(default=5, ge=1, le=15)


class SummarizeResponse(BaseModel):
    """response payload for extractive summary"""
    summary: str


# abstractive summarization
class AbstractiveRequest(BaseModel):
    """request body for transformer-based summarization"""
    text: Optional[str] = None
    doc_id: Optional[str] = None
    target: str = "medium"  # can be 'short' | 'medium' | 'long'


class AbstractiveResponse(BaseModel):
    """response payload for abstractive summarization"""
    summary: str
    model: str
    chunks_used: int


# clustering
class ClusterItem(BaseModel):
    """single document or text unit for clustering"""
    id: str
    name: str
    text: str


class ClusterRequest(BaseModel):
    """request body for clustering"""
    items: List[ClusterItem]
    k: int = Field(default=4, ge=2, le=50)  # number of clusters


class ClusterResponse(BaseModel):
    """cluster assignments and centroid metadata"""
    labels: List[int]
    centroids: List[List[float]]
    terms: List[List[str]]


# text and search
class TextResponse(BaseModel):
    """text content returned for a document"""
    id: str
    name: str
    text: str
    n_chars: int


class SearchRequest(BaseModel):
    """semantic search query with top-K limit"""
    q: str
    topk: int = Field(default=10, ge=1, le=100)


class SearchHit(BaseModel):
    """single search hit entry"""
    id: str
    name: str
    score: float
    preview: str


class SearchResponse(BaseModel):
    """list of search hits"""
    hits: List[SearchHit]


class MetaResponse(BaseModel):
    """stored metadata response for a document"""
    id: str
    meta: Optional[Metadata] = None
