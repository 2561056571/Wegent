# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Similarity Detector Module

Detects similar directories based on structure and naming patterns
to enable sampling and reduce token usage.
"""

import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from app.services.wiki.file_scanner import DirectoryInfo

logger = logging.getLogger(__name__)


@dataclass
class SimilarityGroup:
    """Group of similar directories."""

    pattern: str  # Pattern description (e.g., "src/components/*/")
    directories: List[DirectoryInfo] = field(default_factory=list)
    sampled_dirs: List[str] = field(default_factory=list)
    reason: str = ""
    tokens_saved: int = 0


class SimilarityDetector:
    """
    Detects similar directories for optimization through sampling.

    Similarity is determined by:
    1. Structure similarity (file count, types, subdirectory patterns)
    2. Naming patterns (numbered directories, version directories)
    """

    # Minimum number of similar directories to form a group
    MIN_GROUP_SIZE = 3

    # Maximum directories to sample from a group
    MAX_SAMPLE_SIZE = 2

    # Naming patterns that indicate similar directories
    NAMING_PATTERNS = [
        r"^v\d+$",  # v1, v2, v3
        r"^\d+$",  # 1, 2, 3
        r"^module[-_]?\d+$",  # module1, module_2
        r"^chapter[-_]?\d+$",  # chapter1, chapter_2
        r"^part[-_]?\d+$",  # part1, part_2
        r"^step[-_]?\d+$",  # step1, step_2
        r"^day[-_]?\d+$",  # day1, day_2
        r"^week[-_]?\d+$",  # week1, week_2
        r"^lesson[-_]?\d+$",  # lesson1, lesson_2
    ]

    # File type distribution similarity threshold (0.0 - 1.0)
    SIMILARITY_THRESHOLD = 0.7

    def __init__(
        self,
        min_group_size: int = MIN_GROUP_SIZE,
        max_sample_size: int = MAX_SAMPLE_SIZE,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
    ):
        """
        Initialize the similarity detector.

        Args:
            min_group_size: Minimum directories to form a similar group
            max_sample_size: Maximum directories to sample from each group
            similarity_threshold: Threshold for structure similarity (0.0 - 1.0)
        """
        self.min_group_size = min_group_size
        self.max_sample_size = max_sample_size
        self.similarity_threshold = similarity_threshold
        self._naming_patterns = [re.compile(p, re.IGNORECASE) for p in self.NAMING_PATTERNS]

    def detect_similar_groups(
        self, directories: List[DirectoryInfo]
    ) -> List[SimilarityGroup]:
        """
        Detect groups of similar directories.

        Args:
            directories: List of DirectoryInfo objects from file scanner

        Returns:
            List of SimilarityGroup objects
        """
        groups: List[SimilarityGroup] = []

        # Group by parent directory
        by_parent: Dict[str, List[DirectoryInfo]] = defaultdict(list)
        for dir_info in directories:
            if not dir_info.relative_path:
                continue
            parent = os.path.dirname(dir_info.relative_path)
            by_parent[parent].append(dir_info)

        # Check each parent for similar children
        for parent, children in by_parent.items():
            if len(children) < self.min_group_size:
                continue

            # Try naming pattern similarity
            naming_groups = self._group_by_naming_pattern(children)
            for pattern, dirs in naming_groups.items():
                if len(dirs) >= self.min_group_size:
                    group = self._create_group_from_naming(parent, pattern, dirs)
                    groups.append(group)

            # Try structure similarity for remaining
            remaining = [d for d in children if not any(d in g.directories for g in groups)]
            if len(remaining) >= self.min_group_size:
                structure_groups = self._group_by_structure(remaining)
                for struct_group in structure_groups:
                    if len(struct_group) >= self.min_group_size:
                        group = self._create_group_from_structure(parent, struct_group)
                        groups.append(group)

        return groups

    def _group_by_naming_pattern(
        self, directories: List[DirectoryInfo]
    ) -> Dict[str, List[DirectoryInfo]]:
        """
        Group directories by naming pattern.

        Args:
            directories: List of directories to group

        Returns:
            Dictionary mapping pattern name to matching directories
        """
        groups: Dict[str, List[DirectoryInfo]] = defaultdict(list)

        for dir_info in directories:
            basename = os.path.basename(dir_info.relative_path)
            for i, pattern in enumerate(self._naming_patterns):
                if pattern.match(basename):
                    groups[f"naming_pattern_{i}"].append(dir_info)
                    break

        return groups

    def _group_by_structure(
        self, directories: List[DirectoryInfo]
    ) -> List[List[DirectoryInfo]]:
        """
        Group directories by structure similarity.

        Args:
            directories: List of directories to group

        Returns:
            List of groups (each group is a list of similar directories)
        """
        if len(directories) < self.min_group_size:
            return []

        groups: List[List[DirectoryInfo]] = []
        used: Set[str] = set()

        for i, dir_a in enumerate(directories):
            if dir_a.relative_path in used:
                continue

            group = [dir_a]
            used.add(dir_a.relative_path)

            for j in range(i + 1, len(directories)):
                dir_b = directories[j]
                if dir_b.relative_path in used:
                    continue

                if self._are_structurally_similar(dir_a, dir_b):
                    group.append(dir_b)
                    used.add(dir_b.relative_path)

            if len(group) >= self.min_group_size:
                groups.append(group)

        return groups

    def _are_structurally_similar(
        self, dir_a: DirectoryInfo, dir_b: DirectoryInfo
    ) -> bool:
        """
        Check if two directories are structurally similar.

        Similarity is based on:
        - Similar file count (within 50% range)
        - Similar file type distribution

        Args:
            dir_a: First directory
            dir_b: Second directory

        Returns:
            True if directories are similar
        """
        # Check file count similarity (within 50% range)
        if dir_a.file_count == 0 and dir_b.file_count == 0:
            return True
        if dir_a.file_count == 0 or dir_b.file_count == 0:
            return False

        count_ratio = min(dir_a.file_count, dir_b.file_count) / max(
            dir_a.file_count, dir_b.file_count
        )
        if count_ratio < 0.5:
            return False

        # Check file type distribution similarity
        similarity = self._calculate_type_similarity(
            dir_a.file_types, dir_b.file_types
        )
        return similarity >= self.similarity_threshold

    def _calculate_type_similarity(
        self, types_a: Dict[str, int], types_b: Dict[str, int]
    ) -> float:
        """
        Calculate similarity between two file type distributions.

        Uses Jaccard similarity on the set of file types.

        Args:
            types_a: File type counts for first directory
            types_b: File type counts for second directory

        Returns:
            Similarity score (0.0 - 1.0)
        """
        if not types_a and not types_b:
            return 1.0
        if not types_a or not types_b:
            return 0.0

        set_a = set(types_a.keys())
        set_b = set(types_b.keys())

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)

        return intersection / union if union > 0 else 0.0

    def _create_group_from_naming(
        self, parent: str, pattern: str, directories: List[DirectoryInfo]
    ) -> SimilarityGroup:
        """
        Create a similarity group from naming pattern match.

        Args:
            parent: Parent directory path
            pattern: Pattern identifier
            directories: Matched directories

        Returns:
            SimilarityGroup object
        """
        # Sort by file count (most files first) and select samples
        sorted_dirs = sorted(directories, key=lambda d: -d.file_count)
        sampled = sorted_dirs[: self.max_sample_size]

        # Calculate tokens saved
        total_tokens = sum(d.total_tokens for d in directories)
        sampled_tokens = sum(d.total_tokens for d in sampled)
        tokens_saved = total_tokens - sampled_tokens

        return SimilarityGroup(
            pattern=f"{parent}/*/ (naming pattern)",
            directories=directories,
            sampled_dirs=[d.relative_path for d in sampled],
            reason="Directories follow similar naming pattern",
            tokens_saved=tokens_saved,
        )

    def _create_group_from_structure(
        self, parent: str, directories: List[DirectoryInfo]
    ) -> SimilarityGroup:
        """
        Create a similarity group from structure similarity.

        Args:
            parent: Parent directory path
            directories: Structurally similar directories

        Returns:
            SimilarityGroup object
        """
        # Sort by file count and token count, select samples
        sorted_dirs = sorted(
            directories, key=lambda d: (-d.file_count, -d.total_tokens)
        )
        sampled = sorted_dirs[: self.max_sample_size]

        # Calculate tokens saved
        total_tokens = sum(d.total_tokens for d in directories)
        sampled_tokens = sum(d.total_tokens for d in sampled)
        tokens_saved = total_tokens - sampled_tokens

        return SimilarityGroup(
            pattern=f"{parent}/*/ (structure similarity)",
            directories=directories,
            sampled_dirs=[d.relative_path for d in sampled],
            reason="Directories have similar file structure",
            tokens_saved=tokens_saved,
        )

    def get_files_to_skip(
        self, groups: List[SimilarityGroup]
    ) -> Set[str]:
        """
        Get set of directory paths that should be skipped (not sampled).

        Args:
            groups: List of similarity groups

        Returns:
            Set of directory paths to skip
        """
        skip_paths: Set[str] = set()

        for group in groups:
            sampled_set = set(group.sampled_dirs)
            for dir_info in group.directories:
                if dir_info.relative_path not in sampled_set:
                    skip_paths.add(dir_info.relative_path)

        return skip_paths

    def get_total_tokens_saved(self, groups: List[SimilarityGroup]) -> int:
        """
        Calculate total tokens saved by all groups.

        Args:
            groups: List of similarity groups

        Returns:
            Total tokens saved
        """
        return sum(g.tokens_saved for g in groups)
