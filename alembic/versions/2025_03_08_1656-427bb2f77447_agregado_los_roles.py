"""agregado los roles

Revision ID: 427bb2f77447
Revises: d7bb395cc787
Create Date: 2025-03-08 16:56:38.475568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '427bb2f77447'
down_revision: Union[str, None] = 'd7bb395cc787'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('role', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="user"))
    op.drop_column('users', 'permission')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('permission', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.drop_column('users', 'role')
    # ### end Alembic commands ###
