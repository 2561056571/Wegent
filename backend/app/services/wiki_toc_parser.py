# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Wiki Table of Contents (TOC) parser service.

Parses H2/H3 headings from Markdown content to generate
navigation structure for wiki pages.
"""

import re
from typing import Dict, List, Set


def generate_heading_id(text: str, existing_ids: Set[str]) -> str:
    """
    Generate a unique anchor ID (slug) from heading text.

    Args:
        text: Heading text content
        existing_ids: Set of already used IDs for uniqueness checking

    Returns:
        Unique slug string for the heading
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()

    # Remove special characters except hyphens and alphanumerics
    slug = re.sub(r"[^\w\s-]", "", slug)

    # Replace whitespace with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Ensure uniqueness by adding numeric suffix if needed
    if not slug:
        slug = "heading"

    original_slug = slug
    counter = 1
    while slug in existing_ids:
        slug = f"{original_slug}-{counter}"
        counter += 1

    existing_ids.add(slug)
    return slug


def parse_toc_from_markdown(content: str, max_level: int = 3) -> List[Dict]:
    """
    Parse H2/H3 headings from Markdown content to generate table of contents.

    Args:
        content: Markdown text content
        max_level: Maximum heading level to parse (default 3 for H2 and H3)

    Returns:
        List of TOC items, each containing:
        - id: Anchor ID (slug)
        - text: Heading text
        - level: Heading level (2 or 3)
    """
    if not content:
        return []

    toc_items: List[Dict] = []
    existing_ids: Set[str] = set()

    # Match Markdown headings (## and ###)
    # Pattern matches lines starting with 2 or 3 # characters followed by space and text
    heading_pattern = re.compile(
        r"^(#{2,3})\s+(.+?)(?:\s*{#[\w-]+})?\s*$", re.MULTILINE
    )

    for match in heading_pattern.finditer(content):
        hashes = match.group(1)
        text = match.group(2).strip()

        level = len(hashes)

        # Only include headings up to max_level
        if level > max_level:
            continue

        # Clean up the heading text (remove inline formatting markers)
        clean_text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Remove bold
        clean_text = re.sub(r"\*(.+?)\*", r"\1", clean_text)  # Remove italic
        clean_text = re.sub(r"`(.+?)`", r"\1", clean_text)  # Remove inline code
        clean_text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", clean_text)  # Remove links

        heading_id = generate_heading_id(clean_text, existing_ids)

        toc_items.append({"id": heading_id, "text": clean_text, "level": level})

    return toc_items
