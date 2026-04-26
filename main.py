from fastapi import FastAPI
from sqlalchemy import text
from database import engine, get_redis, Base
from routers.documents import router as documents_router

app = FastAPI(title="Document Insights API")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(documents_router)


@app.get("/health")
async def health():
    errors = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        errors["mysql"] = str(exc)
    try:
        await get_redis().ping()
    except Exception as exc:
        errors["redis"] = str(exc)
    if errors:
        return {"status": "degraded", "errors": errors}
    return {"status": "ok"}
