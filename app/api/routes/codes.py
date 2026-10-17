from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.codes import CodeOut
from app.services.codes import get_code, list_codes

router = APIRouter(prefix="/codes", tags=["codes"])


@router.get("", response_model=list[CodeOut])
async def get_codes(db: DbSession, user: CurrentUser):
    return await list_codes(db)


@router.get("/{key}", response_model=CodeOut)
async def get_code_by_key(key: str, db: DbSession, user: CurrentUser):
    code = await get_code(db, key)
    if code is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown code")
    return code
