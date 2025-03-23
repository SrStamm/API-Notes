"""cambia Tasks por Notes

Revision ID: 763b1ec42cc6
Revises: 2b598c7ad377
Create Date: 2025-03-21 16:34:21.511060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '763b1ec42cc6'
down_revision: Union[str, None] = '2b598c7ad377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("tasks", "notes")
    op.rename_table("tasks_tags_link", "notes_tags_link")

def downgrade() -> None:
    op.rename_table("notes", "tasks")
    op.rename_table("notes_tags_link", "tasks_tags_link")