"""probando

Revision ID: 30d7af8cbcf1
Revises: 
Create Date: 2025-02-26 11:03:49.379245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30d7af8cbcf1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # op.add_column('users', sa.Column('probando', sa.String))
    pass

def downgrade() -> None:
    op.drop_column('users', 'probando')
