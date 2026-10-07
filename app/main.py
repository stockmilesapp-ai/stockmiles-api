from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.engine import engine

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
        return JSONResponse(status_code=503, content={"db": "error"})
    return {"db": "ok"}
