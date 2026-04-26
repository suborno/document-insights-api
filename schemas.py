from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    user_id: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    content: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    id: int
    user_id: str
    title: str
    status: str
    summary: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SubmitResponse(BaseModel):
    document_id: int
    status: str


class PaginatedResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[DocumentResponse]
