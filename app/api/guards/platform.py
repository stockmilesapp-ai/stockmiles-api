from fastapi import Depends

from app.api.guards.base import require_permission

CanReadRoles = Depends(require_permission("platform.roles.read"))
CanManageRoles = Depends(require_permission("platform.roles.manage"))
CanReadTenants = Depends(require_permission("platform.tenants.read"))
