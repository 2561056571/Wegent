# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Summary Generator Module

Generates file summaries for large files to reduce token usage
while preserving key structural information.
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.services.wiki.token_counter import token_counter

logger = logging.getLogger(__name__)


@dataclass
class FileSummary:
    """Summary of a large file."""

    file_path: str
    original_tokens: int
    summary_tokens: int
    summary_content: str
    head_lines: int
    tail_lines: int
    structures_extracted: int


class SummaryGenerator:
    """
    Generates summaries for large files.

    Extracts:
    1. File head (imports, class definitions)
    2. File tail (exports, main blocks)
    3. Key structures (class/function signatures, constants)
    """

    # Default line limits
    DEFAULT_HEAD_LINES = 50
    DEFAULT_TAIL_LINES = 20
    DEFAULT_MAX_SUMMARY_TOKENS = 2000

    # File type specific patterns for structure extraction
    PYTHON_PATTERNS = {
        "class": r"^class\s+\w+.*:",
        "function": r"^(?:async\s+)?def\s+\w+\s*\([^)]*\).*:",
        "constant": r"^[A-Z][A-Z0-9_]+\s*=",
        "import": r"^(?:from|import)\s+",
    }

    JAVASCRIPT_PATTERNS = {
        "class": r"^(?:export\s+)?class\s+\w+",
        "function": r"^(?:export\s+)?(?:async\s+)?function\s+\w+",
        "arrow": r"^(?:export\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
        "constant": r"^(?:export\s+)?const\s+[A-Z][A-Z0-9_]+\s*=",
        "import": r"^import\s+",
        "export": r"^export\s+",
    }

    TYPESCRIPT_PATTERNS = {
        **JAVASCRIPT_PATTERNS,
        "interface": r"^(?:export\s+)?interface\s+\w+",
        "type": r"^(?:export\s+)?type\s+\w+\s*=",
        "enum": r"^(?:export\s+)?enum\s+\w+",
    }

    GO_PATTERNS = {
        "function": r"^func\s+(?:\([^)]+\)\s+)?\w+\s*\(",
        "struct": r"^type\s+\w+\s+struct\s*\{",
        "interface": r"^type\s+\w+\s+interface\s*\{",
        "constant": r"^(?:const|var)\s+[A-Z]",
        "import": r"^import\s+",
        "package": r"^package\s+",
    }

    RUST_PATTERNS = {
        "function": r"^(?:pub\s+)?(?:async\s+)?fn\s+\w+",
        "struct": r"^(?:pub\s+)?struct\s+\w+",
        "enum": r"^(?:pub\s+)?enum\s+\w+",
        "impl": r"^impl\s+",
        "trait": r"^(?:pub\s+)?trait\s+\w+",
        "use": r"^use\s+",
        "mod": r"^(?:pub\s+)?mod\s+",
    }

    JAVA_PATTERNS = {
        "class": r"^(?:public|private|protected)?\s*(?:abstract\s+)?class\s+\w+",
        "interface": r"^(?:public|private|protected)?\s*interface\s+\w+",
        "method": r"^\s*(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?\w+\s+\w+\s*\(",
        "import": r"^import\s+",
        "package": r"^package\s+",
    }

    # Extension to pattern mapping
    EXTENSION_PATTERNS = {
        ".py": PYTHON_PATTERNS,
        ".js": JAVASCRIPT_PATTERNS,
        ".jsx": JAVASCRIPT_PATTERNS,
        ".ts": TYPESCRIPT_PATTERNS,
        ".tsx": TYPESCRIPT_PATTERNS,
        ".go": GO_PATTERNS,
        ".rs": RUST_PATTERNS,
        ".java": JAVA_PATTERNS,
    }

    def __init__(
        self,
        head_lines: int = DEFAULT_HEAD_LINES,
        tail_lines: int = DEFAULT_TAIL_LINES,
        max_summary_tokens: int = DEFAULT_MAX_SUMMARY_TOKENS,
    ):
        """
        Initialize the summary generator.

        Args:
            head_lines: Number of lines to include from file head
            tail_lines: Number of lines to include from file tail
            max_summary_tokens: Maximum tokens for the summary
        """
        self.head_lines = head_lines
        self.tail_lines = tail_lines
        self.max_summary_tokens = max_summary_tokens

    def generate_summary(
        self,
        file_path: str,
        original_tokens: Optional[int] = None,
    ) -> FileSummary:
        """
        Generate a summary for a file.

        Args:
            file_path: Path to the file
            original_tokens: Original token count (calculated if not provided)

        Returns:
            FileSummary object
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return FileSummary(
                file_path=file_path,
                original_tokens=original_tokens or 0,
                summary_tokens=0,
                summary_content="[ERROR: Could not read file]",
                head_lines=0,
                tail_lines=0,
                structures_extracted=0,
            )

        if original_tokens is None:
            original_tokens = token_counter.count_tokens(content)

        # Get file extension for pattern matching
        ext = os.path.splitext(file_path)[1].lower()
        patterns = self.EXTENSION_PATTERNS.get(ext, {})

        # Extract sections
        head_content = self._extract_head(lines)
        tail_content = self._extract_tail(lines)
        structures = self._extract_structures(lines, patterns)

        # Build summary
        summary_parts = []

        # Header with metadata
        summary_parts.append(f"[FILE SUMMARY: {file_path}]")
        summary_parts.append(
            f"[Original size: {original_tokens:,} tokens | Total lines: {len(lines)}]"
        )
        summary_parts.append("")

        # Head section
        if head_content:
            summary_parts.append(f"--- HEAD (lines 1-{min(self.head_lines, len(lines))}) ---")
            summary_parts.append(head_content)
            summary_parts.append("")

        # Key structures section
        if structures:
            summary_parts.append("--- KEY STRUCTURES ---")
            summary_parts.append(structures)
            summary_parts.append("")

        # Tail section
        if tail_content and len(lines) > self.head_lines:
            tail_start = max(len(lines) - self.tail_lines + 1, self.head_lines + 1)
            summary_parts.append(f"--- TAIL (lines {tail_start}-{len(lines)}) ---")
            summary_parts.append(tail_content)
            summary_parts.append("")

        summary_parts.append("[END SUMMARY]")

        summary_content = "\n".join(summary_parts)
        summary_tokens = token_counter.count_tokens(summary_content)

        # Truncate if still too large
        if summary_tokens > self.max_summary_tokens:
            summary_content = self._truncate_summary(summary_content)
            summary_tokens = token_counter.count_tokens(summary_content)

        return FileSummary(
            file_path=file_path,
            original_tokens=original_tokens,
            summary_tokens=summary_tokens,
            summary_content=summary_content,
            head_lines=min(self.head_lines, len(lines)),
            tail_lines=min(self.tail_lines, max(0, len(lines) - self.head_lines)),
            structures_extracted=len(structures.splitlines()) if structures else 0,
        )

    def _extract_head(self, lines: List[str]) -> str:
        """
        Extract the head section of a file.

        Args:
            lines: File lines

        Returns:
            Head content string
        """
        head = lines[: self.head_lines]
        return "\n".join(head)

    def _extract_tail(self, lines: List[str]) -> str:
        """
        Extract the tail section of a file.

        Args:
            lines: File lines

        Returns:
            Tail content string
        """
        if len(lines) <= self.head_lines:
            return ""

        tail_start = max(len(lines) - self.tail_lines, self.head_lines)
        tail = lines[tail_start:]
        return "\n".join(tail)

    def _extract_structures(
        self, lines: List[str], patterns: dict
    ) -> str:
        """
        Extract key structural elements from a file.

        Args:
            lines: File lines
            patterns: Regex patterns for the file type

        Returns:
            Extracted structures as string
        """
        if not patterns:
            return ""

        structures: List[Tuple[int, str, str]] = []  # (line_num, type, content)

        for i, line in enumerate(lines):
            # Skip lines already in head or tail
            if i < self.head_lines or i >= len(lines) - self.tail_lines:
                continue

            stripped = line.strip()
            if not stripped:
                continue

            for struct_type, pattern in patterns.items():
                if re.match(pattern, stripped):
                    # Get the line and possibly docstring/signature continuation
                    extracted = self._extract_structure_with_context(lines, i, struct_type)
                    structures.append((i + 1, struct_type, extracted))
                    break

        if not structures:
            return ""

        # Format output
        output_lines = []
        for line_num, struct_type, content in structures:
            output_lines.append(f"[L{line_num}] {struct_type}:")
            output_lines.append(content)
            output_lines.append("")

        return "\n".join(output_lines).strip()

    def _extract_structure_with_context(
        self, lines: List[str], start_idx: int, struct_type: str
    ) -> str:
        """
        Extract a structure with minimal context.

        Args:
            lines: File lines
            start_idx: Starting line index
            struct_type: Type of structure being extracted

        Returns:
            Extracted content
        """
        result = [lines[start_idx]]

        # For functions/methods, include docstring if present
        if struct_type in ("function", "method", "class", "def"):
            # Check for docstring on next lines
            for i in range(start_idx + 1, min(start_idx + 5, len(lines))):
                line = lines[i].strip()
                if line.startswith('"""') or line.startswith("'''"):
                    # Include docstring lines
                    quote = line[:3]
                    result.append(lines[i])
                    if not (line.count(quote) >= 2 and len(line) > 3):
                        # Multi-line docstring
                        for j in range(i + 1, min(i + 10, len(lines))):
                            result.append(lines[j])
                            if quote in lines[j]:
                                break
                    break
                elif line and not line.startswith("#"):
                    break

        return "\n".join(result)

    def _truncate_summary(self, summary: str) -> str:
        """
        Truncate summary to fit within token limit.

        Args:
            summary: Summary content

        Returns:
            Truncated summary
        """
        lines = summary.splitlines()
        truncated_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = token_counter.count_tokens(line)
            if current_tokens + line_tokens > self.max_summary_tokens - 100:
                truncated_lines.append("...")
                truncated_lines.append("[SUMMARY TRUNCATED DUE TO SIZE]")
                truncated_lines.append("[END SUMMARY]")
                break
            truncated_lines.append(line)
            current_tokens += line_tokens

        return "\n".join(truncated_lines)

    def should_summarize(
        self,
        file_tokens: int,
        normal_threshold: int = 10000,
    ) -> bool:
        """
        Check if a file should be summarized based on token count.

        Args:
            file_tokens: Number of tokens in the file
            normal_threshold: Threshold above which to summarize

        Returns:
            True if file should be summarized
        """
        return file_tokens > normal_threshold
