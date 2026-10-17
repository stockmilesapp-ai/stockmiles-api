"""Add roles and permissions

Expand step (D53): the new tables, their system data, and role_id on members,
filled from the old role strings. The old role columns stay, nullable, until the
contract migration drops them.

Revision ID: e3f8510d8a3d
Revises: 761e5a3d1e3a
Create Date: 2026-10-17 13:12:51.298412

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3f8510d8a3d"
down_revision: str | Sequence[str] | None = "761e5a3d1e3a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# A frozen copy of the role and permission registries at the time of this
# migration (D52). Later catalog changes get their own data migration.

# (key, name, scope, kind, level, store_access, app_access)
ROLES = [
    ("platform_admin", "Platform admin", "platform", None, 100, None, True),
    ("platform_support", "Platform support", "platform", None, 50, None, True),
    ("owner", "Owner", "tenant", "corporate", 100, "all", True),
    ("administrator", "Administrator", "tenant", "corporate", 90, "all", True),
    ("accounts", "Accounts", "tenant", "corporate", 70, "all", True),
    ("buyer", "Buyer", "tenant", "corporate", 70, "all", True),
    ("branch_manager", "Branch manager", "tenant", "store", 50, "assigned", True),
    ("counter", "Counter", "tenant", "store", 30, "assigned", True),
    ("sales_assistant", "Sales assistant", "tenant", "store", 10, "assigned", False),
    ("support_staff", "Support staff", "tenant", "store", 10, "assigned", False),
]

CORPORATE = ["owner", "administrator"]
SIGNED_IN = ["owner", "administrator", "accounts", "buyer", "branch_manager", "counter"]
STORE_TEAM = ["owner", "administrator", "branch_manager", "counter"]
PURCHASING = ["owner", "administrator", "buyer"]
PURCHASING_READ = [*PURCHASING, "accounts"]

# (key, scope, section, name, default roles); the module is the key's first part.
PERMISSIONS = [
    ("platform.tenants.read", "platform", "tenants", "View tenants",
     ["platform_admin", "platform_support"]),
    ("platform.tenants.manage", "platform", "tenants", "Manage tenants",
     ["platform_admin"]),
    ("platform.access_links.create", "platform", "tenants",
     "Create member access links", ["platform_admin", "platform_support"]),
    ("platform.roles.read", "platform", "roles", "View roles and permissions",
     ["platform_admin"]),
    ("platform.roles.manage", "platform", "roles", "Change role permissions",
     ["platform_admin"]),
    ("platform.metadata.read", "platform", "metadata", "View metadata",
     ["platform_admin"]),
    ("platform.metadata.manage", "platform", "metadata", "Manage metadata",
     ["platform_admin"]),
    ("business.settings.manage", "tenant", "settings", "Manage business settings",
     CORPORATE),
    ("business.stores.read", "tenant", "stores", "View stores", SIGNED_IN),
    ("business.stores.manage", "tenant", "stores", "Manage stores", CORPORATE),
    ("team.members.read", "tenant", "members", "View team members", STORE_TEAM),
    ("team.members.manage", "tenant", "members", "Manage team members", STORE_TEAM),
    ("team.roles.manage", "tenant", "roles", "Manage roles", CORPORATE),
    ("team.attendance.read", "tenant", "attendance", "View attendance", STORE_TEAM),
    ("team.attendance.manage", "tenant", "attendance", "Record attendance",
     STORE_TEAM),
    ("purchasing.suppliers.read", "tenant", "suppliers", "View suppliers",
     PURCHASING_READ),
    ("purchasing.suppliers.manage", "tenant", "suppliers", "Manage suppliers",
     PURCHASING),
    ("purchasing.trips.read", "tenant", "trips", "View purchase trips",
     PURCHASING_READ),
    ("purchasing.trips.manage", "tenant", "trips", "Manage purchase trips",
     PURCHASING),
    ("purchasing.bills.read", "tenant", "bills", "View purchase bills",
     PURCHASING_READ),
    ("purchasing.bills.manage", "tenant", "bills", "Manage purchase bills",
     PURCHASING),
    ("catalog.products.read", "tenant", "products", "View products", SIGNED_IN),
    ("catalog.products.manage", "tenant", "products", "Manage products", PURCHASING),
    ("catalog.products.view_cost", "tenant", "products", "View product costs",
     PURCHASING_READ),
    ("inventory.stock.read", "tenant", "stock", "View stock", SIGNED_IN),
    ("inventory.stock.adjust", "tenant", "stock", "Adjust stock",
     [*CORPORATE, "branch_manager"]),
    ("inventory.stock.transfer", "tenant", "stock", "Transfer stock",
     [*CORPORATE, "branch_manager"]),
    ("sales.bills.create", "tenant", "bills", "Create sales bills", STORE_TEAM),
    ("sales.bills.read", "tenant", "bills", "View sales bills", STORE_TEAM),
    ("sales.bills.discount", "tenant", "bills", "Give discounts",
     [*CORPORATE, "branch_manager"]),
    ("sales.bills.refund", "tenant", "bills", "Refund sales",
     [*CORPORATE, "branch_manager"]),
    ("sales.bills.void", "tenant", "bills", "Void sales bills",
     [*CORPORATE, "branch_manager"]),
    ("reports.sales.view", "tenant", "sales", "Sales reports",
     [*CORPORATE, "accounts", "branch_manager"]),
    ("reports.inventory.view", "tenant", "inventory", "Inventory reports",
     [*CORPORATE, "accounts", "branch_manager"]),
    ("reports.profit.view", "tenant", "profit", "Profit reports",
     [*CORPORATE, "accounts"]),
]  # fmt: skip


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("module", sa.String(length=32), nullable=False),
        sa.Column("section", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_permissions_key"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=True),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("store_access", sa.String(length=16), nullable=True),
        sa.Column(
            "app_access", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "is_system", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "key",
            name="uq_roles_tenant_key",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(op.f("ix_roles_tenant_id"), "roles", ["tenant_id"], unique=False)
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    op.create_index(
        op.f("ix_role_permissions_tenant_id"),
        "role_permissions",
        ["tenant_id"],
        unique=False,
    )

    _seed_access()

    # Members: new columns first, then fill them, then constraints.
    op.add_column("platform_members", sa.Column("role_id", sa.Uuid(), nullable=True))
    op.alter_column(
        "platform_members", "role", existing_type=sa.VARCHAR(length=32), nullable=True
    )
    op.alter_column(
        "store_members", "role", existing_type=sa.VARCHAR(length=32), nullable=True
    )
    op.add_column(
        "tenant_members", sa.Column("full_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "tenant_members", sa.Column("phone", sa.String(length=32), nullable=True)
    )
    op.add_column("tenant_members", sa.Column("role_id", sa.Uuid(), nullable=True))
    op.alter_column(
        "tenant_members", "email", existing_type=sa.VARCHAR(length=320), nullable=True
    )
    op.alter_column(
        "tenant_members", "role", existing_type=sa.VARCHAR(length=32), nullable=True
    )

    # Backfill role_id from the old role strings (mapping in D56).
    op.execute(
        """
        UPDATE platform_members pm SET role_id = r.id
        FROM roles r
        WHERE r.tenant_id IS NULL AND r.scope = 'platform' AND r.key = pm.role
        """
    )
    op.execute(
        """
        UPDATE tenant_members tm SET role_id = r.id
        FROM roles r
        WHERE r.tenant_id IS NULL AND r.scope = 'tenant'
          AND r.key = CASE tm.role
              WHEN 'owner' THEN 'owner'
              WHEN 'admin' THEN 'administrator'
              WHEN 'accountant' THEN 'accounts'
              WHEN 'staff' THEN CASE WHEN EXISTS (
                  SELECT 1 FROM store_members sm
                  WHERE sm.member_id = tm.id AND sm.role = 'manager'
              ) THEN 'branch_manager' ELSE 'counter' END
          END
        """
    )
    op.execute(
        """
        UPDATE tenant_members tm
        SET full_name = COALESCE(
            (SELECT u.name FROM users u WHERE u.id = tm.user_id), tm.email, ''
        )
        """
    )
    op.alter_column(
        "tenant_members",
        "full_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.create_index(
        op.f("ix_platform_members_role_id"),
        "platform_members",
        ["role_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_platform_members_role",
        "platform_members",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_tenant_members_role_id"),
        "tenant_members",
        ["role_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_tenant_members_role",
        "tenant_members",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def _seed_access() -> None:
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("scope", sa.String()),
        sa.column("kind", sa.String()),
        sa.column("key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("level", sa.Integer()),
        sa.column("store_access", sa.String()),
        sa.column("app_access", sa.Boolean()),
        sa.column("is_system", sa.Boolean()),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("key", sa.String()),
        sa.column("scope", sa.String()),
        sa.column("module", sa.String()),
        sa.column("section", sa.String()),
        sa.column("name", sa.String()),
        sa.column("sort_order", sa.Integer()),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )

    role_ids: dict[str, uuid.UUID] = {}
    role_rows = []
    for key, name, scope, kind, level, store_access, app_access in ROLES:
        role_ids[key] = uuid.uuid4()
        role_rows.append(
            {
                "id": role_ids[key],
                "scope": scope,
                "kind": kind,
                "key": key,
                "name": name,
                "level": level,
                "store_access": store_access,
                "app_access": app_access,
                "is_system": True,
            }
        )

    permission_rows = []
    grant_rows = []
    for position, (key, scope, section, name, default_roles) in enumerate(
        PERMISSIONS, start=1
    ):
        permission_id = uuid.uuid4()
        permission_rows.append(
            {
                "id": permission_id,
                "key": key,
                "scope": scope,
                "module": key.split(".")[0],
                "section": section,
                "name": name,
                "sort_order": position,
            }
        )
        for role_key in default_roles:
            grant_rows.append(
                {"role_id": role_ids[role_key], "permission_id": permission_id}
            )

    op.bulk_insert(roles, role_rows)
    op.bulk_insert(permissions, permission_rows)
    op.bulk_insert(role_permissions, grant_rows)


def downgrade() -> None:
    """Downgrade schema."""
    # Refill the old role strings from role_id before they become NOT NULL again.
    op.execute(
        """
        UPDATE platform_members pm SET role = r.key
        FROM roles r
        WHERE r.id = pm.role_id AND pm.role IS NULL
        """
    )
    op.execute(
        """
        UPDATE tenant_members tm SET role = CASE r.key
            WHEN 'owner' THEN 'owner'
            WHEN 'administrator' THEN 'admin'
            WHEN 'accounts' THEN 'accountant'
            ELSE 'staff'
        END
        FROM roles r
        WHERE r.id = tm.role_id AND tm.role IS NULL
        """
    )
    op.execute(
        """
        UPDATE store_members sm SET role = CASE r.key
            WHEN 'branch_manager' THEN 'manager' ELSE 'sales'
        END
        FROM tenant_members tm JOIN roles r ON r.id = tm.role_id
        WHERE tm.id = sm.member_id AND sm.role IS NULL
        """
    )
    op.execute("UPDATE store_members SET role = 'sales' WHERE role IS NULL")

    op.drop_constraint("fk_tenant_members_role", "tenant_members", type_="foreignkey")
    op.drop_index(op.f("ix_tenant_members_role_id"), table_name="tenant_members")
    op.alter_column(
        "tenant_members", "role", existing_type=sa.VARCHAR(length=32), nullable=False
    )
    # Fails on purpose if members without an email exist: restoring NOT NULL
    # would otherwise mean deleting them.
    op.alter_column(
        "tenant_members", "email", existing_type=sa.VARCHAR(length=320), nullable=False
    )
    op.drop_column("tenant_members", "role_id")
    op.drop_column("tenant_members", "phone")
    op.drop_column("tenant_members", "full_name")
    op.alter_column(
        "store_members", "role", existing_type=sa.VARCHAR(length=32), nullable=False
    )
    op.drop_constraint(
        "fk_platform_members_role", "platform_members", type_="foreignkey"
    )
    op.drop_index(op.f("ix_platform_members_role_id"), table_name="platform_members")
    op.alter_column(
        "platform_members", "role", existing_type=sa.VARCHAR(length=32), nullable=False
    )
    op.drop_column("platform_members", "role_id")
    op.drop_index(op.f("ix_role_permissions_tenant_id"), table_name="role_permissions")
    op.drop_table("role_permissions")
    op.drop_index(op.f("ix_roles_tenant_id"), table_name="roles")
    op.drop_table("roles")
    op.drop_table("permissions")
