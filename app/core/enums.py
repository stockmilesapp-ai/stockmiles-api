from enum import StrEnum


class TenantType(StrEnum):
    INDIVIDUAL = "individual"
    CHAIN = "chain"
    FRANCHISE = "franchise"


class TenantStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class TenantRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    STAFF = "staff"


class StoreRole(StrEnum):
    MANAGER = "manager"
    SALES = "sales"


class MemberStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    DISABLED = "disabled"


class LocationKind(StrEnum):
    SALES_FLOOR = "sales_floor"
    STOCK_ROOM = "stock_room"
    WAREHOUSE = "warehouse"


class PlatformRole(StrEnum):
    PLATFORM_ADMIN = "platform_admin"


class PlatformTenantScope(StrEnum):
    ALL = "all"
    ASSIGNED = "assigned"


class RoleScope(StrEnum):
    PLATFORM = "platform"
    TENANT = "tenant"


class RoleKind(StrEnum):
    CORPORATE = "corporate"
    STORE = "store"


class StoreAccess(StrEnum):
    ALL = "all"
    ASSIGNED = "assigned"


SYSTEM_CODES: dict[str, type[StrEnum]] = {
    "tenant_type": TenantType,
    "tenant_status": TenantStatus,
    "tenant_role": TenantRole,
    "store_role": StoreRole,
    "member_status": MemberStatus,
    "location_kind": LocationKind,
    "platform_role": PlatformRole,
    "platform_tenant_scope": PlatformTenantScope,
}
