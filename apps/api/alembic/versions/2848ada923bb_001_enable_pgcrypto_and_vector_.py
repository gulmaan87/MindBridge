"""001_enable_pgcrypto_and_vector_extensions

Revision ID: 2848ada923bb
Revises:
Create Date: 2026-10-01 15:03:17.407615

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2848ada923bb"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable pgcrypto for UUID generation and vector for semantic memory embeddings."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade() -> None:
    """Drop vector and pgcrypto extensions."""
    op.execute("DROP EXTENSION IF EXISTS vector;")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto;")
