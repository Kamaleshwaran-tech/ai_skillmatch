"""add_resume_is_active

Revision ID: 8a3c9e12b4f1
Revises: dd4ee4ad6d27
Create Date: 2026-10-13 09:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a3c9e12b4f1'
down_revision: Union[str, None] = 'dd4ee4ad6d27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('resumes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False))
        batch_op.create_index(batch_op.f('ix_resumes_is_active'), ['is_active'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('resumes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_resumes_is_active'))
        batch_op.drop_column('is_active')
