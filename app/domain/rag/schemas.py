from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    ready = "ready"
    failed = "failed"
    deleted = "deleted"


class DocumentRecord(BaseModel):
    document_id: str
    user_id: str
    filename: str
    content_type: str
    storage_path: str
    status: DocumentStatus
    chunk_count: int = 0
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ChunkRecord(BaseModel):
    chunk_id: str
    document_id: str
    user_id: str
    filename: str
    content: str
    chunk_index: int


class DocumentBatchIngestResponse(BaseModel):
    items: list[DocumentRecord]
    rejected_files: list[str] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    items: list[DocumentRecord]


class QueryRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=200)
    query: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=3, ge=1, le=10)


class InternalChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=4000)
    model: str | None = Field(default=None, max_length=200)
    max_tokens: int = Field(default=1000, ge=1, le=4000)


class QueryCitation(BaseModel):
    document_id: str | None = None
    filename: str | None = None
    score: float | None = None
    snippet: str


class QueryResponse(BaseModel):
    user_id: str
    query: str
    response: str
    citations: list[QueryCitation]
    primary_citation_document_id: str | None = None
    primary_citation_filename: str | None = None


class InternalChatResponse(BaseModel):
    user_id: str
    message: str
    answer: str
    provider: str
    model: str
