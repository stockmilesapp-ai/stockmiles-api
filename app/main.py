import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.engine import engine

logger = logging.getLogger(__name__)
app = FastAPI(title="StockMiles API")


@app.get("/health")
async def health():
    try:
        conn = await engine.connect()
        try:
            await conn.execute(text("SELECT 1"))
        finally:
            await conn.close()
    except (SQLAlchemyError, OSError):
        logger.exception("Health check failed")
        return JSONResponse(status_code=503, content={"db": "error"})
    return {"db": "ok"}
