"""rag knowledge base, llm call logs, catalog fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-23 21:24:59.550893

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector must be available on the server (docker image pgvector/pgvector:pg16).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('knowledge_documents',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=512), nullable=False),
    sa.Column('source_type', sa.String(length=32), nullable=False),
    sa.Column('source_url', sa.String(length=1024), nullable=False),
    sa.Column('publisher', sa.String(length=255), nullable=False),
    sa.Column('accessed_at', sa.Date(), nullable=False),
    sa.Column('license', sa.String(length=128), nullable=False),
    sa.Column('verification_status', sa.String(length=16), nullable=False),
    sa.Column('language', sa.String(length=8), nullable=False),
    sa.Column('topics', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_documents_verification_status'), 'knowledge_documents', ['verification_status'], unique=False)
    op.create_table('llm_call_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('purpose', sa.String(length=32), nullable=False),
    sa.Column('provider', sa.String(length=32), nullable=False),
    sa.Column('model', sa.String(length=128), nullable=False),
    sa.Column('mode', sa.String(length=16), nullable=False),
    sa.Column('fallback_reason', sa.String(length=64), nullable=True),
    sa.Column('latency_ms', sa.Float(), nullable=True),
    sa.Column('input_tokens', sa.Integer(), nullable=True),
    sa.Column('output_tokens', sa.Integer(), nullable=True),
    sa.Column('est_cost_usd', sa.Float(), nullable=True),
    sa.Column('grounded_ratio', sa.Float(), nullable=True),
    sa.Column('safe', sa.Boolean(), nullable=True),
    sa.Column('rules_version', sa.String(length=32), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('knowledge_chunks',
    sa.Column('id', sa.String(length=96), nullable=False),
    sa.Column('document_id', sa.String(length=64), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=False),
    sa.Column('embedding_model', sa.String(length=128), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_chunks_document_id'), 'knowledge_chunks', ['document_id'], unique=False)
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_embedding_hnsw ON knowledge_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    op.add_column('products', sa.Column('manufacturer', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('usage_instructions', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('targets', sa.JSON(), nullable=True))
    op.add_column('products', sa.Column('suitable_skin_types', sa.JSON(), nullable=True))
    op.add_column('products', sa.Column('price_checked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('products', sa.Column('available', sa.Boolean(), nullable=True))
    op.add_column('products', sa.Column('availability_note', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('discovery_url', sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'discovery_url')
    op.drop_column('products', 'availability_note')
    op.drop_column('products', 'available')
    op.drop_column('products', 'price_checked_at')
    op.drop_column('products', 'suitable_skin_types')
    op.drop_column('products', 'targets')
    op.drop_column('products', 'usage_instructions')
    op.drop_column('products', 'manufacturer')
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding_hnsw")
    op.drop_index(op.f('ix_knowledge_chunks_document_id'), table_name='knowledge_chunks')
    op.drop_table('knowledge_chunks')
    op.drop_table('llm_call_logs')
    op.drop_index(op.f('ix_knowledge_documents_verification_status'), table_name='knowledge_documents')
    op.drop_table('knowledge_documents')
