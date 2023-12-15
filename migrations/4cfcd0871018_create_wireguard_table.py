"""create wireguard table

Revision ID: 4cfcd0871018
Revises: 
Create Date: 2023-12-15 21:55:07.783659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cfcd0871018'
down_revision = None
branch_labels = None
depends_on = None


def upgrade(op=None):
    op.create_table(
        "wireguardDB",
        sa.Column("userid", sa.Integer, nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("index", sa.Integer, nullable=False, autoincrement=True),
        sa.ForeignKeyConstraint(["userid"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("index"),
    )


def downgrade(op=None) -> None:
    op.drop_table("wireguardDB")

