"""Add platform owner role

The platform owner is one person (D62). Platform admins, the people the owner
hires, keep every platform permission except changing role permissions.

Revision ID: 1534eaac6c01
Revises: e3f8510d8a3d
Create Date: 2026-10-17 18:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1534eaac6c01"
down_revision: str | Sequence[str] | None = "e3f8510d8a3d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SYSTEM_PLATFORM_ROLE = "r.tenant_id IS NULL AND r.scope = 'platform'"


def upgrade() -> None:
    """Upgrade schema."""
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("scope", sa.String()),
        sa.column("key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("level", sa.Integer()),
        sa.column("is_system", sa.Boolean()),
    )
    owner_id = uuid.uuid4()
    op.bulk_insert(
        roles,
        [
            {
                "id": owner_id,
                "scope": "platform",
                "key": "platform_owner",
                "name": "Platform owner",
                "level": 100,
                "is_system": True,
            }
        ],
    )
    # The owner holds every platform permission.
    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT :owner_id, p.id FROM permissions p WHERE p.scope = 'platform'
            """
        ).bindparams(owner_id=owner_id)
    )
    op.execute(
        f"""
        UPDATE roles r SET level = 90, updated_at = now()
        WHERE {SYSTEM_PLATFORM_ROLE} AND r.key = 'platform_admin'
        """
    )
    op.execute(
        f"""
        DELETE FROM role_permissions rp
        USING roles r, permissions p
        WHERE rp.role_id = r.id AND rp.permission_id = p.id
          AND {SYSTEM_PLATFORM_ROLE} AND r.key = 'platform_admin'
          AND p.key = 'platform.roles.manage'
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # members.role_id is ON DELETE RESTRICT, so move the owner back first.
    op.execute(
        f"""
        UPDATE platform_members pm
        SET role_id = admin.id, role = 'platform_admin'
        FROM roles r, roles admin
        WHERE pm.role_id = r.id AND {SYSTEM_PLATFORM_ROLE}
          AND r.key = 'platform_owner'
          AND admin.tenant_id IS NULL AND admin.key = 'platform_admin'
        """
    )
    op.execute(
        f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE {SYSTEM_PLATFORM_ROLE} AND r.key = 'platform_admin'
          AND p.key = 'platform.roles.manage'
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        f"""
        UPDATE roles r SET level = 100, updated_at = now()
        WHERE {SYSTEM_PLATFORM_ROLE} AND r.key = 'platform_admin'
        """
    )
    # Its grants go with it (ON DELETE CASCADE).
    op.execute(
        f"DELETE FROM roles r WHERE {SYSTEM_PLATFORM_ROLE} AND r.key = 'platform_owner'"
    )
