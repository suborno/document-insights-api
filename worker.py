import asyncio
import logging
import random

from sqlalchemy import select

from database import AsyncSessionLocal, get_redis
from config import Settings

log = logging.getLogger(__name__)
settings = Settings()


async def decrement_active_count(user_id: str):
    r = get_redis()
    try:
        val = await r.decr(f"rate:{user_id}")
        if val < 0:
            await r.set(f"rate:{user_id}", 0)
    except Exception as e:
        log.error(f"Failed to decrement rate limit for {user_id}: {e}")


async def process_document(doc_id: int):
    from models import Document

    # lock the row to avoid race conditions
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document)
            .where(Document.id == doc_id, Document.status == "queued")
            .with_for_update()
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            return
        doc.status = "processing"
        user_id = doc.user_id
        await db.commit()

    # simulate processing delay
    await asyncio.sleep(random.uniform(2, 5))

    try:
        async with AsyncSessionLocal() as db:
            doc = await db.get(Document, doc_id)
            # simulate occasional failures for now
            if random.random() < 0.1:
                doc.status = "failed"
            else:
                doc.status = "completed"
                words = doc.content.split()
                doc.summary = " ".join(words[:40]) + ("..." if len(words) > 40 else "")

                r = get_redis()
                try:
                    await r.set(
                        f"cache:{doc.content_hash}",
                        doc.summary,
                        ex=settings.cache_ttl_seconds,
                    )
                except Exception as e:
                    log.warning(f"Cache write failed: {e}")
            await db.commit()
    except Exception as e:
        log.exception(f"Failed to process document {doc_id}: {e}")
    finally:
        await decrement_active_count(user_id)