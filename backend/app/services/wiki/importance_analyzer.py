# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
File Importance Analyzer Module

Uses pattern-based analysis to determine file importance for wiki generation.
Can optionally use AI for more sophisticated analysis.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from app.services.wiki.file_scanner import FileImportance, ScannedFile

logger = logging.getLogger(__name__)


class ImportanceAnalyzer:
    """
    Analyzes file importance for prioritization in wiki generation.

    Uses heuristics based on:
    - File path and naming patterns
    - Directory location
    - File type and extension
    """

    # Critical file patterns (highest priority)
    CRITICAL_PATTERNS = [
        # Entry points
        r"^main\.(py|ts|js|go|rs|java)$",
        r"^index\.(ts|js|tsx|jsx)$",
        r"^app\.(py|ts|js|tsx|jsx)$",
        r"^server\.(py|ts|js|go)$",
        r"^manage\.py$",
        r"^wsgi\.py$",
        r"^asgi\.py$",
        # Configuration
        r"^config\.(py|ts|js|yaml|yml|json)$",
        r"^settings\.(py|ts|js)$",
        r"^\.env\.example$",
        r"^pyproject\.toml$",
        r"^package\.json$",
        r"^tsconfig\.json$",
        r"^Cargo\.toml$",
        r"^go\.mod$",
        r"^pom\.xml$",
        r"^build\.gradle$",
        # Documentation
        r"^README\.(md|rst|txt)$",
        r"^CHANGELOG\.(md|rst|txt)$",
        r"^CONTRIBUTING\.(md|rst|txt)$",
        r"^AGENTS\.md$",
        r"^CLAUDE\.md$",
        # API definitions
        r"^openapi\.(yaml|yml|json)$",
        r"^swagger\.(yaml|yml|json)$",
        r"^schema\.(graphql|gql)$",
    ]

    # High priority directory patterns
    HIGH_PRIORITY_DIRS = [
        r"^src/?$",
        r"^app/?$",
        r"^lib/?$",
        r"^core/?$",
        r"^api/?$",
        r"^services/?$",
        r"^models/?$",
        r"^schemas/?$",
        r"^routes/?$",
        r"^controllers/?$",
        r"^handlers/?$",
        r"^components/?$",
    ]

    # Medium priority directory patterns
    MEDIUM_PRIORITY_DIRS = [
        r"^utils/?$",
        r"^helpers/?$",
        r"^common/?$",
        r"^shared/?$",
        r"^middleware/?$",
        r"^plugins/?$",
        r"^hooks/?$",
        r"^contexts/?$",
    ]

    # Low priority directory patterns
    LOW_PRIORITY_DIRS = [
        r"^tests?/?$",
        r"^test/?$",
        r"^__tests__/?$",
        r"^spec/?$",
        r"^examples?/?$",
        r"^samples?/?$",
        r"^demo/?$",
        r"^fixtures/?$",
        r"^mocks?/?$",
        r"^e2e/?$",
    ]

    # Skip priority patterns
    SKIP_PATTERNS = [
        r"\.generated\.(ts|js|py)$",
        r"\.g\.(ts|dart)$",
        r"\.pb\.(go|py)$",
        r"_pb2\.py$",
        r"\.d\.ts$",
        r"\.test\.(ts|js|tsx|jsx|py)$",
        r"\.spec\.(ts|js|tsx|jsx)$",
        r"_test\.(go|py)$",
        r"test_.*\.py$",
        r".*\.stories\.(tsx|jsx|ts|js)$",
        r".*\.mock\.(ts|js|py)$",
    ]

    # High priority file patterns
    HIGH_PATTERNS = [
        r"^router\.(py|ts|js)$",
        r"^routes\.(py|ts|js)$",
        r"^api\.(py|ts|js)$",
        r"^endpoints?\.(py|ts|js)$",
        r"^views?\.(py|ts|js)$",
        r"^models?\.(py|ts|js)$",
        r"^schemas?\.(py|ts|js)$",
        r"^services?\.(py|ts|js)$",
        r"^handlers?\.(py|ts|js)$",
        r"^controllers?\.(py|ts|js)$",
        r"^factory\.(py|ts|js)$",
        r"^base\.(py|ts|js)$",
        r"^types\.(py|ts|js)$",
    ]

    def __init__(self, use_ai: bool = False):
        """
        Initialize the importance analyzer.

        Args:
            use_ai: Whether to use AI for enhanced analysis (not yet implemented)
        """
        self.use_ai = use_ai
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        self._critical_re = [re.compile(p, re.IGNORECASE) for p in self.CRITICAL_PATTERNS]
        self._high_re = [re.compile(p, re.IGNORECASE) for p in self.HIGH_PATTERNS]
        self._skip_re = [re.compile(p, re.IGNORECASE) for p in self.SKIP_PATTERNS]
        self._high_dir_re = [re.compile(p, re.IGNORECASE) for p in self.HIGH_PRIORITY_DIRS]
        self._medium_dir_re = [re.compile(p, re.IGNORECASE) for p in self.MEDIUM_PRIORITY_DIRS]
        self._low_dir_re = [re.compile(p, re.IGNORECASE) for p in self.LOW_PRIORITY_DIRS]

    def analyze_file(self, file: ScannedFile) -> FileImportance:
        """
        Analyze and assign importance to a single file.

        Args:
            file: ScannedFile to analyze

        Returns:
            FileImportance level
        """
        path = file.relative_path
        basename = os.path.basename(path)
        dirname = os.path.dirname(path)
        dir_parts = dirname.split(os.sep) if dirname else []

        # Check skip patterns first
        for pattern in self._skip_re:
            if pattern.search(basename):
                return FileImportance.SKIP

        # Check critical patterns
        for pattern in self._critical_re:
            if pattern.search(basename):
                return FileImportance.CRITICAL

        # Check high priority patterns
        for pattern in self._high_re:
            if pattern.search(basename):
                return FileImportance.HIGH

        # Check directory-based importance
        dir_importance = self._get_dir_importance(dir_parts)
        if dir_importance is not None:
            return dir_importance

        # Default to medium importance
        return FileImportance.MEDIUM

    def _get_dir_importance(self, dir_parts: List[str]) -> Optional[FileImportance]:
        """
        Get importance based on directory path.

        Args:
            dir_parts: List of directory path components

        Returns:
            FileImportance or None if no match
        """
        for part in dir_parts:
            # Check high priority directories
            for pattern in self._high_dir_re:
                if pattern.search(part):
                    return FileImportance.HIGH

            # Check medium priority directories
            for pattern in self._medium_dir_re:
                if pattern.search(part):
                    return FileImportance.MEDIUM

            # Check low priority directories
            for pattern in self._low_dir_re:
                if pattern.search(part):
                    return FileImportance.LOW

        return None

    def analyze_files(self, files: List[ScannedFile]) -> List[ScannedFile]:
        """
        Analyze and assign importance to all files.

        Args:
            files: List of ScannedFile objects

        Returns:
            Same list with importance fields updated
        """
        for file in files:
            file.importance = self.analyze_file(file)
        return files

    def sort_by_importance(self, files: List[ScannedFile]) -> List[ScannedFile]:
        """
        Sort files by importance (highest first).

        Args:
            files: List of ScannedFile objects

        Returns:
            Sorted list (highest importance first)
        """
        return sorted(files, key=lambda f: (-f.importance.value, f.relative_path))

    def get_importance_summary(
        self, files: List[ScannedFile]
    ) -> Dict[FileImportance, Tuple[int, int]]:
        """
        Get summary statistics by importance level.

        Args:
            files: List of ScannedFile objects

        Returns:
            Dictionary mapping importance to (file_count, total_tokens)
        """
        summary: Dict[FileImportance, Tuple[int, int]] = {}
        for importance in FileImportance:
            matching = [f for f in files if f.importance == importance]
            count = len(matching)
            tokens = sum(f.tokens for f in matching)
            summary[importance] = (count, tokens)
        return summary

    def filter_by_importance(
        self,
        files: List[ScannedFile],
        min_importance: FileImportance = FileImportance.LOW,
    ) -> List[ScannedFile]:
        """
        Filter files by minimum importance level.

        Args:
            files: List of ScannedFile objects
            min_importance: Minimum importance level to include

        Returns:
            Filtered list of files
        """
        return [f for f in files if f.importance.value >= min_importance.value]
