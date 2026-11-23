"""profile past reaction ingredients

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-23 22:18:03.510335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('skin_profiles', sa.Column('past_reaction_ingredients', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('skin_profiles', 'past_reaction_ingredients')
