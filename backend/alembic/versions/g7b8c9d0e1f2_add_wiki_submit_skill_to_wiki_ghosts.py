# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Add wiki_submit skill to wiki ghost resources

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2025-12-11 18:00:00.000000+08:00

This migration updates existing wiki ghost resources to add the wiki_submit skill.
The skill is added to the JSON spec.skills field for all wiki-related ghosts.
"""
from typing import Sequence, Union

import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Wiki ghost names that should have wiki_submit skill
WIKI_GHOST_NAMES = [
    "wiki-coordinator-ghost",
    "wiki-overview-ghost",
    "wiki-architecture-ghost",
    "wiki-module-ghost",
    "wiki-api-ghost",
    "wiki-guide-ghost",
]


def upgrade() -> None:
    """Add wiki_submit skill to all wiki ghost resources."""
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # Query all wiki ghost resources
        result = session.execute(
            sa.text(
                """
                SELECT id, name, json FROM kinds
                WHERE kind = 'Ghost'
                AND name IN :names
                AND is_active = 1
                """
            ),
            {"names": tuple(WIKI_GHOST_NAMES)},
        )

        rows = result.fetchall()

        for row in rows:
            kind_id, name, json_data = row
            if json_data:
                try:
                    data = json.loads(json_data) if isinstance(json_data, str) else json_data

                    # Get or create spec.skills
                    if "spec" not in data:
                        data["spec"] = {}

                    skills = data["spec"].get("skills", [])

                    # Add wiki_submit if not already present
                    if "wiki_submit" not in skills:
                        skills.append("wiki_submit")
                        data["spec"]["skills"] = skills

                        # Update the record
                        session.execute(
                            sa.text(
                                """
                                UPDATE kinds SET json = :json_data
                                WHERE id = :id
                                """
                            ),
                            {"json_data": json.dumps(data), "id": kind_id},
                        )
                        print(f"Updated Ghost '{name}' with wiki_submit skill")
                    else:
                        print(f"Ghost '{name}' already has wiki_submit skill")

                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Failed to parse JSON for Ghost '{name}': {e}")

        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        session.close()


def downgrade() -> None:
    """Remove wiki_submit skill from wiki ghost resources."""
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # Query all wiki ghost resources
        result = session.execute(
            sa.text(
                """
                SELECT id, name, json FROM kinds
                WHERE kind = 'Ghost'
                AND name IN :names
                AND is_active = 1
                """
            ),
            {"names": tuple(WIKI_GHOST_NAMES)},
        )

        rows = result.fetchall()

        for row in rows:
            kind_id, name, json_data = row
            if json_data:
                try:
                    data = json.loads(json_data) if isinstance(json_data, str) else json_data

                    # Remove wiki_submit from skills
                    if "spec" in data and "skills" in data["spec"]:
                        skills = data["spec"]["skills"]
                        if "wiki_submit" in skills:
                            skills.remove("wiki_submit")
                            data["spec"]["skills"] = skills

                            # Update the record
                            session.execute(
                                sa.text(
                                    """
                                    UPDATE kinds SET json = :json_data
                                    WHERE id = :id
                                    """
                                ),
                                {"json_data": json.dumps(data), "id": kind_id},
                            )
                            print(f"Removed wiki_submit skill from Ghost '{name}'")

                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Failed to parse JSON for Ghost '{name}': {e}")

        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Downgrade failed: {e}")
        raise
    finally:
        session.close()
