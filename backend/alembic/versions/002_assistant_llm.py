"""Add assistant LLM provider columns

Revision ID: 002_assistant_llm
Revises: 001_initial
Create Date: 2026-08-28
"""

from alembic import op
import sqlalchemy as sa

revision = "002_assistant_llm"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assistants", sa.Column("llm_provider", sa.String(length=32), server_default="openai"))
    op.add_column("assistants", sa.Column("llm_model", sa.String(length=80), nullable=True))


def downgrade() -> None:
    op.drop_column("assistants", "llm_model")
    op.drop_column("assistants", "llm_provider")
