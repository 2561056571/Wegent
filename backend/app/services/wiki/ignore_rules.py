# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Ignore Rules Parser Module

Parses and applies ignore rules from multiple sources:
1. Built-in rules (lowest priority)
2. Project .gitignore (medium priority)
3. Wegent .wikiignore (highest priority)
"""

import fnmatch
import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class IgnoreRulesParser:
    """
    Parser for file ignore rules supporting .gitignore and .wikiignore formats.

    Priority (highest to lowest):
    1. .wikiignore rules
    2. .gitignore rules
    3. Built-in default rules
    """

    # Built-in ignore patterns (lowest priority)
    BUILTIN_IGNORE_PATTERNS = [
        # Version control
        ".git/",
        ".git",
        ".svn/",
        ".hg/",
        # Dependencies
        "node_modules/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        # Build outputs
        "dist/",
        "build/",
        "*.egg-info/",
        ".next/",
        "out/",
        "target/",
        # Virtual environments
        ".venv/",
        "venv/",
        "env/",
        ".env",
        ".env.*",
        # IDE files
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        ".DS_Store",
        "Thumbs.db",
        # Logs and cache
        "*.log",
        "logs/",
        ".cache/",
        ".pytest_cache/",
        # Lock files
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Pipfile.lock",
        # Minified files
        "*.min.js",
        "*.min.css",
        # Coverage and tests
        "coverage/",
        ".coverage",
        "htmlcov/",
        # Binaries and media (usually not useful for wiki)
        "*.exe",
        "*.dll",
        "*.so",
        "*.dylib",
        "*.bin",
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.ico",
        "*.mp3",
        "*.mp4",
        "*.avi",
        "*.mov",
        "*.zip",
        "*.tar",
        "*.gz",
        "*.rar",
        "*.7z",
        "*.pdf",
        "*.doc",
        "*.docx",
        "*.xls",
        "*.xlsx",
        "*.woff",
        "*.woff2",
        "*.ttf",
        "*.eot",
    ]

    def __init__(
        self,
        wikiignore_path: Optional[str] = None,
        enable_builtin: bool = True,
    ):
        """
        Initialize the ignore rules parser.

        Args:
            wikiignore_path: Path to the .wikiignore file
            enable_builtin: Whether to enable built-in ignore rules
        """
        self.wikiignore_path = wikiignore_path
        self.enable_builtin = enable_builtin

        # Rule sets (patterns and negations)
        self.builtin_patterns: List[str] = []
        self.gitignore_patterns: List[str] = []
        self.wikiignore_patterns: List[str] = []

        # Force include patterns (from .wikiignore with ! prefix)
        self.force_include_patterns: List[str] = []

        # Summary-only patterns (from .wikiignore with @summary: prefix)
        self.summary_patterns: List[str] = []

        # Max scan depth (from .wikiignore with @max_depth: directive)
        self.max_depth: Optional[int] = None

        # Load built-in rules
        if enable_builtin:
            self.builtin_patterns = self.BUILTIN_IGNORE_PATTERNS.copy()

    def load_gitignore(self, repo_root: str) -> List[str]:
        """
        Load and parse .gitignore from repository root.

        Args:
            repo_root: Repository root directory path

        Returns:
            List of loaded patterns
        """
        gitignore_path = os.path.join(repo_root, ".gitignore")
        if os.path.isfile(gitignore_path):
            patterns = self._parse_ignore_file(gitignore_path)
            self.gitignore_patterns = patterns
            logger.info(f"Loaded {len(patterns)} patterns from .gitignore")
            return patterns
        return []

    def load_wikiignore(self, path: Optional[str] = None) -> List[str]:
        """
        Load and parse .wikiignore file.

        Args:
            path: Path to .wikiignore file (uses self.wikiignore_path if None)

        Returns:
            List of loaded patterns
        """
        wikiignore_path = path or self.wikiignore_path
        if not wikiignore_path or not os.path.isfile(wikiignore_path):
            return []

        patterns = []
        try:
            with open(wikiignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Handle special directives
                    if line.startswith("@max_depth:"):
                        try:
                            self.max_depth = int(line.split(":", 1)[1].strip())
                            logger.info(f"Set max_depth to {self.max_depth}")
                        except ValueError:
                            logger.warning(f"Invalid @max_depth value: {line}")
                        continue

                    if line.startswith("@summary:"):
                        pattern = line.split(":", 1)[1].strip()
                        self.summary_patterns.append(pattern)
                        logger.debug(f"Added summary pattern: {pattern}")
                        continue

                    # Handle force include (negation patterns)
                    if line.startswith("!"):
                        pattern = line[1:].strip()
                        self.force_include_patterns.append(pattern)
                        logger.debug(f"Added force include pattern: {pattern}")
                        continue

                    # Regular ignore pattern
                    patterns.append(line)

            self.wikiignore_patterns = patterns
            logger.info(f"Loaded {len(patterns)} patterns from .wikiignore")
            return patterns

        except Exception as e:
            logger.error(f"Failed to load .wikiignore from {wikiignore_path}: {e}")
            return []

    def _parse_ignore_file(self, file_path: str) -> List[str]:
        """
        Parse a .gitignore-style file.

        Args:
            file_path: Path to the ignore file

        Returns:
            List of patterns (excluding comments and empty lines)
        """
        patterns = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception as e:
            logger.warning(f"Failed to parse ignore file {file_path}: {e}")
        return patterns

    def should_ignore(self, path: str, is_dir: bool = False) -> bool:
        """
        Check if a path should be ignored based on all rules.

        Args:
            path: Relative path to check
            is_dir: Whether the path is a directory

        Returns:
            True if the path should be ignored
        """
        # Normalize path separators
        path = path.replace("\\", "/")

        # Check force include first (highest priority)
        if self._matches_any_pattern(path, self.force_include_patterns, is_dir):
            return False

        # Check wikiignore patterns (highest ignore priority)
        if self._matches_any_pattern(path, self.wikiignore_patterns, is_dir):
            return True

        # Check gitignore patterns
        if self._matches_any_pattern(path, self.gitignore_patterns, is_dir):
            return True

        # Check builtin patterns (lowest priority)
        if self._matches_any_pattern(path, self.builtin_patterns, is_dir):
            return True

        return False

    def should_summarize(self, path: str) -> bool:
        """
        Check if a file should be summarized instead of fully scanned.

        Args:
            path: Relative path to check

        Returns:
            True if the file should be summarized
        """
        path = path.replace("\\", "/")
        return self._matches_any_pattern(path, self.summary_patterns, is_dir=False)

    def _matches_any_pattern(
        self, path: str, patterns: List[str], is_dir: bool = False
    ) -> bool:
        """
        Check if a path matches any of the given patterns.

        Args:
            path: Path to check
            patterns: List of patterns to match against
            is_dir: Whether the path is a directory

        Returns:
            True if the path matches any pattern
        """
        # Get the basename for matching
        basename = os.path.basename(path.rstrip("/"))

        for pattern in patterns:
            if self._matches_pattern(path, basename, pattern, is_dir):
                return True
        return False

    def _matches_pattern(
        self, path: str, basename: str, pattern: str, is_dir: bool = False
    ) -> bool:
        """
        Check if a path matches a single pattern.

        Supports gitignore-style patterns:
        - * matches anything except /
        - ** matches any path including /
        - ? matches any single character
        - [seq] matches any character in seq
        - Patterns ending with / only match directories
        - Patterns with / match full paths, otherwise match basenames

        Args:
            path: Full relative path
            basename: Base name of the path
            pattern: Pattern to match against
            is_dir: Whether the path is a directory

        Returns:
            True if the path matches the pattern
        """
        original_pattern = pattern

        # Handle directory-only patterns (ending with /)
        if pattern.endswith("/"):
            if not is_dir:
                return False
            pattern = pattern.rstrip("/")

        # Check if pattern should match full path or just basename
        if "/" in pattern:
            # Pattern contains /, match against full path
            match_target = path
        else:
            # Pattern without /, match against basename
            match_target = basename

        # Convert gitignore pattern to regex
        regex_pattern = self._gitignore_to_regex(pattern)

        try:
            return bool(re.match(regex_pattern, match_target, re.IGNORECASE))
        except re.error as e:
            logger.warning(f"Invalid pattern '{original_pattern}': {e}")
            return False

    def _gitignore_to_regex(self, pattern: str) -> str:
        """
        Convert a gitignore pattern to a regex pattern.

        Args:
            pattern: Gitignore-style pattern

        Returns:
            Regex pattern string
        """
        # Escape special regex characters except gitignore wildcards
        special_chars = ".^$+{}[]|()"
        result = ""
        i = 0
        while i < len(pattern):
            c = pattern[i]
            if c in special_chars:
                result += "\\" + c
            elif c == "*":
                if i + 1 < len(pattern) and pattern[i + 1] == "*":
                    # ** matches any path
                    result += ".*"
                    i += 1  # Skip next *
                else:
                    # * matches anything except /
                    result += "[^/]*"
            elif c == "?":
                result += "[^/]"
            else:
                result += c
            i += 1

        return f"^{result}$"

    def get_all_patterns(self) -> dict:
        """
        Get all loaded patterns organized by source.

        Returns:
            Dictionary with patterns from each source
        """
        return {
            "builtin": self.builtin_patterns,
            "gitignore": self.gitignore_patterns,
            "wikiignore": self.wikiignore_patterns,
            "force_include": self.force_include_patterns,
            "summary": self.summary_patterns,
            "max_depth": self.max_depth,
        }

    def get_stats(self) -> dict:
        """
        Get statistics about loaded rules.

        Returns:
            Dictionary with rule counts
        """
        return {
            "builtin_count": len(self.builtin_patterns),
            "gitignore_count": len(self.gitignore_patterns),
            "wikiignore_count": len(self.wikiignore_patterns),
            "force_include_count": len(self.force_include_patterns),
            "summary_count": len(self.summary_patterns),
            "max_depth": self.max_depth,
        }
