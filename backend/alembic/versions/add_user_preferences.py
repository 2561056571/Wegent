# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Add preferences column to users table

Revision ID: add_user_preferences
Revises: 2b3c4d5e6f7g
Create Date: 2025-12-05 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_user_preferences"
down_revision: Union[str, None] = "2b3c4d5e6f7g"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    result = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = :table_name
            AND COLUMN_NAME = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar() > 0


def upgrade() -> None:
    # Add preferences column to users table
    connection = op.get_bind()
    if not _column_exists(connection, "users", "preferences"):
        op.add_column(
            "users",
            sa.Column(
                "preferences",
                sa.String(4096),
                nullable=False,
                server_default="{}",
                comment="user preferences",
            ),
        )


def downgrade() -> None:
    # Remove preferences column from users table
    op.drop_column("users", "preferences")
