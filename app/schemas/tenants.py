import uuid
from datetime import datetime

from app.schemas.base import ApiModel


class TenantOut(ApiModel):
    id: uuid.UUID
    name: str
    tenant_type: str
    template_key: str
    country_code: str
    currency_code: str
    status: str
    created_at: datetime
