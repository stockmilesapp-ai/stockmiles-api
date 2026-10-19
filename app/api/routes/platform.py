from fastapi import APIRouter

from app.api.guards.platform import CanReadTenants
from app.db.session import DbSession
from app.models import Tenant
from app.schemas.tenants import TenantOut
from app.services.tenants import list_tenants

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/tenants", response_model=list[TenantOut], dependencies=[CanReadTenants])
async def get_tenants(db: DbSession) -> list[Tenant]:
    return await list_tenants(db)
