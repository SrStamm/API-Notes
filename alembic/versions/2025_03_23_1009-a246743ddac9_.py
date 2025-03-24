"""empty message

Revision ID: a246743ddac9
Revises: 763b1ec42cc6
Create Date: 2025-03-23 10:09:39.212866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a246743ddac9'
down_revision: Union[str, None] = '763b1ec42cc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notes', sa.Column('create_time', sa.Time(), nullable=False, server_default='00:00:00.265359'))
    op.drop_index('ix_tasks_user_id', table_name='notes')
    op.create_index(op.f('ix_notes_user_id'), 'notes', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_notes_user_id'), table_name='notes')
    op.create_index('ix_tasks_user_id', 'notes', ['user_id'], unique=False)
    op.drop_column('notes', 'create_time')
    # ### end Alembic commands ###
