from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    question: str

class SourceCitation(BaseModel):
    page: int
    content: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    error: Optional[str] = None

class IngestResponse(BaseModel):
    status: str
    page_count: int
    chunk_count: int
    error: Optional[str] = None
