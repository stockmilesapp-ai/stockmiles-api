"""Seed industry templates

Revision ID: 761e5a3d1e3a
Revises: d0c05ac1272c
Create Date: 2026-10-16 20:30:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "761e5a3d1e3a"
down_revision: str | Sequence[str] | None = "d0c05ac1272c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Industry templates a tenant picks at onboarding. Not a system code: the
# program never branches on these values, and a new industry is added as data.
TEMPLATE_CODE = "industry_template"
TEMPLATES = [
    ("clothing", "Clothing and textiles"),
    ("mobile_accessories", "Mobile accessories"),
]

codes = sa.table(
    "codes",
    sa.column("id", sa.Uuid()),
    sa.column("key", sa.String()),
    sa.column("name", sa.String()),
    sa.column("is_system", sa.Boolean()),
)
code_values = sa.table(
    "code_values",
    sa.column("id", sa.Uuid()),
    sa.column("code_id", sa.Uuid()),
    sa.column("key", sa.String()),
    sa.column("label", sa.String()),
    sa.column("sort_order", sa.Integer()),
)


def upgrade() -> None:
    code_id = uuid.uuid4()
    op.bulk_insert(
        codes,
        [
            {
                "id": code_id,
                "key": TEMPLATE_CODE,
                "name": "Industry template",
                "is_system": False,
            }
        ],
    )
    op.bulk_insert(
        code_values,
        [
            {
                "id": uuid.uuid4(),
                "code_id": code_id,
                "key": key,
                "label": label,
                "sort_order": position,
            }
            for position, (key, label) in enumerate(TEMPLATES, start=1)
        ],
    )


def downgrade() -> None:
    # The code's values go with it through ON DELETE CASCADE.
    op.execute(codes.delete().where(codes.c.key == TEMPLATE_CODE))
