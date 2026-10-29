"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-29 20:10:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. screenings
    op.create_table(
        'screenings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('idempotency_key', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, default='queued'),
        sa.Column('risk_level', sa.String(length=30), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('requires_human_review', sa.Boolean(), nullable=False, default=False),
        sa.Column('extracted_fields', sa.JSON(), nullable=False),
        sa.Column('checks', sa.JSON(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_screenings_idempotency_key', 'screenings', ['idempotency_key'], unique=False)
    op.create_index('ix_screenings_user_id', 'screenings', ['user_id'], unique=False)
    op.create_index('ix_screenings_status', 'screenings', ['status'], unique=False)

    # 3. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('screening_id', sa.String(length=36), sa.ForeignKey('screenings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('sha256_checksum', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_documents_screening_id', 'documents', ['screening_id'], unique=False)

    # 4. findings
    op.create_table(
        'findings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('screening_id', sa.String(length=36), sa.ForeignKey('screenings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('evidence_ref', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_findings_screening_id', 'findings', ['screening_id'], unique=False)

    # 5. assessments
    op.create_table(
        'assessments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('screening_id', sa.String(length=36), sa.ForeignKey('screenings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.String(length=30), nullable=False),
        sa.Column('requires_human_review', sa.Boolean(), nullable=False, default=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_assessments_screening_id', 'assessments', ['screening_id'], unique=False)

    # 6. reviews
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('screening_id', sa.String(length=36), sa.ForeignKey('screenings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('decision', sa.String(length=30), nullable=False),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('reviewed_by', sa.String(length=64), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_reviews_screening_id', 'reviews', ['screening_id'], unique=False)
    op.create_index('ix_reviews_user_id', 'reviews', ['user_id'], unique=False)

    # 7. audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('case_id', sa.String(length=36), nullable=False),
        sa.Column('screening_id', sa.String(length=36), sa.ForeignKey('screenings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_events_case_id', 'audit_events', ['case_id'], unique=False)
    op.create_index('ix_audit_events_screening_id', 'audit_events', ['screening_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('reviews')
    op.drop_table('assessments')
    op.drop_table('findings')
    op.drop_table('documents')
    op.drop_table('screenings')
    op.drop_table('users')

