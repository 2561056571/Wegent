# SPDX-FileCopyrightText: 2025 WeCode, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Migrate knowledge_bases to kinds table

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2025-12-17 15:00:00.000000+08:00

This migration:
1. Drops the knowledge_bases table
2. Modifies knowledge_documents.knowledge_base_id to kind_id
3. Updates foreign key to reference kinds.id
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate knowledge_bases to kinds table."""

    # Step 1: Drop old indexes on knowledge_documents
    op.drop_index("ix_knowledge_documents_base_active_created", table_name="knowledge_documents")

    # Step 2: Drop foreign key constraint on knowledge_documents.knowledge_base_id
    op.drop_constraint(
        "knowledge_documents_ibfk_1",  # MySQL default FK name
        "knowledge_documents",
        type_="foreignkey",
    )

    # Step 3: Rename knowledge_base_id to kind_id
    op.alter_column(
        "knowledge_documents",
        "knowledge_base_id",
        new_column_name="kind_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Step 4: Add new foreign key constraint to kinds.id
    op.create_foreign_key(
        "fk_knowledge_documents_kind_id",
        "knowledge_documents",
        "kinds",
        ["kind_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Step 5: Create new index on kind_id
    op.create_index(
        "ix_knowledge_documents_kind_active_created",
        "knowledge_documents",
        ["kind_id", "is_active", "created_at"],
    )

    # Step 6: Drop knowledge_bases table and its indexes
    op.drop_index("ix_knowledge_bases_user_namespace_active", table_name="knowledge_bases")
    op.drop_index("ix_knowledge_bases_name_user_namespace", table_name="knowledge_bases")
    op.drop_table("knowledge_bases")


def downgrade() -> None:
    """Revert migration - recreate knowledge_bases table."""

    # Step 1: Recreate knowledge_bases table
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("namespace", sa.String(255), nullable=False, server_default="default"),
        sa.Column("document_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )

    # Step 2: Recreate indexes on knowledge_bases
    op.create_index(
        "ix_knowledge_bases_name_user_namespace",
        "knowledge_bases",
        ["name", "user_id", "namespace"],
        unique=True,
    )
    op.create_index(
        "ix_knowledge_bases_user_namespace_active",
        "knowledge_bases",
        ["user_id", "namespace", "is_active"],
    )

    # Step 3: Drop new index on kind_id
    op.drop_index("ix_knowledge_documents_kind_active_created", table_name="knowledge_documents")

    # Step 4: Drop foreign key to kinds
    op.drop_constraint(
        "fk_knowledge_documents_kind_id",
        "knowledge_documents",
        type_="foreignkey",
    )

    # Step 5: Rename kind_id back to knowledge_base_id
    op.alter_column(
        "knowledge_documents",
        "kind_id",
        new_column_name="knowledge_base_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Step 6: Recreate foreign key to knowledge_bases
    op.create_foreign_key(
        "knowledge_documents_ibfk_1",
        "knowledge_documents",
        "knowledge_bases",
        ["knowledge_base_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Step 7: Recreate old index
    op.create_index(
        "ix_knowledge_documents_base_active_created",
        "knowledge_documents",
        ["knowledge_base_id", "is_active", "created_at"],
    )
