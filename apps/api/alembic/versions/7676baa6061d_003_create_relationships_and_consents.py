"""003_create_relationships_and_consents

Revision ID: 7676baa6061d
Revises: f87f34bf0e81
Create Date: 2026-10-05 10:06:49.498693

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7676baa6061d'
down_revision: str | Sequence[str] | None = 'f87f34bf0e81'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create relationships, permissions, consents, and user_preferences tables."""
    # 1. Consents
    op.create_table(
        'consents',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('consent_type', sa.String(length=64), nullable=False),
        sa.Column('version', sa.String(length=16), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_consents_consent_type'), 'consents', ['consent_type'], unique=False)
    op.create_index(op.f('ix_consents_id'), 'consents', ['id'], unique=False)
    op.create_index(op.f('ix_consents_user_id'), 'consents', ['user_id'], unique=False)

    # 2. Relationships
    op.create_table(
        'relationships',
        sa.Column('subject_user_id', sa.UUID(), nullable=False),
        sa.Column('related_user_id', sa.UUID(), nullable=False),
        sa.Column('relationship_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['related_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subject_user_id', 'related_user_id', 'relationship_type', name='uq_subject_related_relationship'),
    )
    op.create_index(op.f('ix_relationships_id'), 'relationships', ['id'], unique=False)
    op.create_index(op.f('ix_relationships_related_user_id'), 'relationships', ['related_user_id'], unique=False)
    op.create_index(op.f('ix_relationships_status'), 'relationships', ['status'], unique=False)
    op.create_index(op.f('ix_relationships_subject_user_id'), 'relationships', ['subject_user_id'], unique=False)

    # 3. Relationship Permissions
    op.create_table(
        'relationship_permissions',
        sa.Column('relationship_id', sa.UUID(), nullable=False),
        sa.Column('permission', sa.String(length=64), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['relationship_id'], ['relationships.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('relationship_id', 'permission', name='uq_relationship_permission'),
    )
    op.create_index(op.f('ix_relationship_permissions_id'), 'relationship_permissions', ['id'], unique=False)
    op.create_index(op.f('ix_relationship_permissions_relationship_id'), 'relationship_permissions', ['relationship_id'], unique=False)

    # 4. User Preferences
    op.create_table(
        'user_preferences',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_preferences_id'), 'user_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_user_preferences_user_id'), 'user_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_preferences_user_id'), table_name='user_preferences')
    op.drop_index(op.f('ix_user_preferences_id'), table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_index(op.f('ix_relationship_permissions_relationship_id'), table_name='relationship_permissions')
    op.drop_index(op.f('ix_relationship_permissions_id'), table_name='relationship_permissions')
    op.drop_table('relationship_permissions')
    op.drop_index(op.f('ix_relationships_subject_user_id'), table_name='relationships')
    op.drop_index(op.f('ix_relationships_status'), table_name='relationships')
    op.drop_index(op.f('ix_relationships_related_user_id'), table_name='relationships')
    op.drop_index(op.f('ix_relationships_id'), table_name='relationships')
    op.drop_table('relationships')
    op.drop_index(op.f('ix_consents_user_id'), table_name='consents')
    op.drop_index(op.f('ix_consents_id'), table_name='consents')
    op.drop_index(op.f('ix_consents_consent_type'), table_name='consents')
    op.drop_table('consents')
