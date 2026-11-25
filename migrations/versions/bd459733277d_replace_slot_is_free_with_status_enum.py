"""replace_slot_is_free_with_status_enum

Revision ID: bd459733277d
Revises: d3d547f34dec
Create Date: 2026-11-25 19:49:38.988281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd459733277d'
down_revision: Union[str, Sequence[str], None] = 'd3d547f34dec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


slot_status_enum = sa.Enum("FREE", "BOOKED", "UNAVAILABLE", name="slot_status_enum")


def upgrade() -> None:
    """Upgrade schema."""
    slot_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("slots", sa.Column("status", slot_status_enum, nullable=True))
    op.execute(
        "UPDATE slots SET status = CASE "
        "WHEN is_free = true THEN 'FREE'::slot_status_enum "
        "ELSE 'BOOKED'::slot_status_enum END"
    )
    op.alter_column(
        "slots",
        "status",
        existing_type=slot_status_enum,
        nullable=False,
        server_default="FREE",
    )
    op.drop_column("slots", "is_free")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("slots", sa.Column("is_free", sa.Boolean(), nullable=True))
    op.execute(
        "UPDATE slots SET is_free = CASE "
        "WHEN status = 'FREE'::slot_status_enum THEN true "
        "ELSE false END"
    )
    op.alter_column(
        "slots",
        "is_free",
        existing_type=sa.Boolean(),
        nullable=False,
    )
    op.drop_column("slots", "status")
    slot_status_enum.drop(op.get_bind(), checkfirst=True)
