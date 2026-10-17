from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.codes import CodeValueOut
from app.services.codes import list_system_code_values

router = APIRouter(prefix="/codes", tags=["codes"])


@router.get("/{key}/values", response_model=list[CodeValueOut])
async def get_code_values(key: str, db: DbSession, user: CurrentUser):
    values = await list_system_code_values(db, key)
    if values is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown code")
    return values
