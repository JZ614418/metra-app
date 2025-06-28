"""add invite_code_used column

Revision ID: add_invite_code_column
Revises: add_phase2_models
Create Date: 2025-06-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_invite_code_column'
down_revision = 'add_phase2_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add invite_code_used column to users table
    op.add_column('users', sa.Column('invite_code_used', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove invite_code_used column from users table
    op.drop_column('users', 'invite_code_used') 