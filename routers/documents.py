import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database import get_db, get_redis
from models import Document
from schemas import DocumentCreate, DocumentResponse, PaginatedResponse, SubmitResponse
from worker import process_document

router = APIRouter(tags=["documents"])
log = logging.getLogger(__name__)
settings = Settings()


def _hash_content(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@router.post("/documents", response_model=SubmitResponse, status_code=201)
async def submit_document(
    payload: DocumentCreate,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    content_hash = _hash_content(payload.content)

    # check if we already processed this content
    r = get_redis()
    try:
        cached_summary = await r.get(f"cache:{content_hash}")
        if cached_summary:
            return {"document_id": -1, "status": "completed", "summary": cached_summary}
    except Exception as e:
        log.warning(f"Redis cache error: {e}")

    # rate limiting
    rate_key = f"rate:{payload.user_id}"
    try:
        current = await r.get(rate_key)
        if current and int(current) >= settings.max_active_jobs:
            raise HTTPException(status_code=429, detail="Too many active jobs")
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Redis error during rate check: {e}")

    doc = Document(
        user_id=payload.user_id,
        title=payload.title,
        content=payload.content,
        content_hash=content_hash,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        await r.incr(rate_key)
    except Exception as e:
        log.warning(f"Failed to increment rate counter: {e}")

    bg.add_task(process_document, doc.id)
    return SubmitResponse(document_id=doc.id, status=doc.status)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, detail="Document not found")
    return doc


@router.get("/users/{user_id}/documents", response_model=PaginatedResponse)
async def list_user_documents(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    filters = [Document.user_id == user_id]
    if status:
        filters.append(Document.status == status)

    total_result = await db.execute(
        select(func.count()).select_from(Document).where(*filters)
    )
    total = total_result.scalar()

    offset = (page - 1) * page_size
    stmt = (
        select(Document)
        .where(*filters)
        .order_by(Document.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = await db.execute(stmt)
    items = rows.scalars().all()

    return PaginatedResponse(
        page=page,
        page_size=page_size,
        total=total,
        items=[DocumentResponse.model_validate(i) for i in items],
    )