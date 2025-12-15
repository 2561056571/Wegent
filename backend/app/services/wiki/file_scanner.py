# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
File Scanner Module

Scans repository files and calculates token counts with ignore rules applied.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.services.wiki.token_counter import token_counter
from app.services.wiki.ignore_rules import IgnoreRulesParser

logger = logging.getLogger(__name__)


class FileAction(str, Enum):
    """Actions that can be applied to a file during wiki generation."""

    FULL_SCAN = "full_scan"
    SUMMARY = "summary"
    METADATA_ONLY = "metadata_only"
    SKIPPED = "skipped"
    IGNORED = "ignored"


class FileImportance(int, Enum):
    """File importance levels for prioritization."""

    CRITICAL = 4  # Core entry points, configuration files, main modules
    HIGH = 3  # Business logic, API interfaces
    MEDIUM = 2  # Utility classes, helper modules
    LOW = 1  # Test files, example code
    SKIP = 0  # Generated files, temporary files


@dataclass
class ScannedFile:
    """Information about a scanned file."""

    path: str
    relative_path: str
    tokens: int
    size_bytes: int
    importance: FileImportance = FileImportance.MEDIUM
    action: FileAction = FileAction.FULL_SCAN
    summary_tokens: Optional[int] = None
    reason: str = ""
    is_dir: bool = False


@dataclass
class ScanStatistics:
    """Statistics from a file scan operation."""

    total_files_found: int = 0
    files_ignored: int = 0
    files_scanned_full: int = 0
    files_scanned_summary: int = 0
    files_skipped: int = 0
    files_metadata_only: int = 0
    total_tokens_estimated: int = 0
    total_tokens_after_optimization: int = 0
    directories_found: int = 0


@dataclass
class DirectoryInfo:
    """Information about a scanned directory."""

    path: str
    relative_path: str
    file_count: int = 0
    total_tokens: int = 0
    file_types: Dict[str, int] = field(default_factory=dict)
    subdirs: List[str] = field(default_factory=list)


class FileScanner:
    """
    Scanner for repository files with token counting and ignore rules.

    Performs two-phase scanning:
    1. Pre-scan: Quick estimation using file sizes
    2. Full scan: Accurate token counting with content reading
    """

    # Default scan limits
    DEFAULT_MAX_DEPTH = 10
    DEFAULT_MAX_FILES_PER_DIR = 100
    DEFAULT_MAX_TOTAL_FILES = 1000

    # File size thresholds (in bytes) for quick filtering
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB max file size

    def __init__(
        self,
        ignore_parser: Optional[IgnoreRulesParser] = None,
        max_depth: Optional[int] = None,
        max_files_per_dir: int = DEFAULT_MAX_FILES_PER_DIR,
        max_total_files: int = DEFAULT_MAX_TOTAL_FILES,
    ):
        """
        Initialize the file scanner.

        Args:
            ignore_parser: Ignore rules parser instance
            max_depth: Maximum directory depth to scan
            max_files_per_dir: Maximum files per directory before sampling
            max_total_files: Maximum total files to scan
        """
        self.ignore_parser = ignore_parser or IgnoreRulesParser()
        self.max_depth = max_depth or self.DEFAULT_MAX_DEPTH
        self.max_files_per_dir = max_files_per_dir
        self.max_total_files = max_total_files

        # Override max_depth if set in ignore parser
        if self.ignore_parser.max_depth is not None:
            self.max_depth = self.ignore_parser.max_depth

    def scan_repository(
        self,
        repo_path: str,
        calculate_tokens: bool = True,
    ) -> Tuple[List[ScannedFile], ScanStatistics, List[DirectoryInfo]]:
        """
        Scan a repository and return file information with token counts.

        Args:
            repo_path: Path to the repository root
            calculate_tokens: Whether to calculate actual token counts

        Returns:
            Tuple of (list of scanned files, scan statistics, directory info list)
        """
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")

        # Load .gitignore from repo
        self.ignore_parser.load_gitignore(repo_path)

        files: List[ScannedFile] = []
        directories: List[DirectoryInfo] = []
        stats = ScanStatistics()

        # Walk the directory tree
        self._scan_directory(
            repo_path,
            repo_path,
            0,
            files,
            directories,
            stats,
            calculate_tokens,
        )

        # Sort files by path for consistent output
        files.sort(key=lambda f: f.relative_path)
        directories.sort(key=lambda d: d.relative_path)

        # Calculate final statistics
        stats.total_tokens_estimated = sum(
            f.tokens for f in files if f.action != FileAction.IGNORED
        )

        return files, stats, directories

    def _scan_directory(
        self,
        current_path: str,
        repo_root: str,
        depth: int,
        files: List[ScannedFile],
        directories: List[DirectoryInfo],
        stats: ScanStatistics,
        calculate_tokens: bool,
    ) -> DirectoryInfo:
        """
        Recursively scan a directory.

        Args:
            current_path: Current directory path
            repo_root: Repository root path
            depth: Current depth in the directory tree
            files: List to collect scanned files
            directories: List to collect directory info
            stats: Statistics object to update
            calculate_tokens: Whether to calculate token counts

        Returns:
            DirectoryInfo for the current directory
        """
        relative_path = os.path.relpath(current_path, repo_root)
        if relative_path == ".":
            relative_path = ""

        dir_info = DirectoryInfo(
            path=current_path,
            relative_path=relative_path,
        )

        # Check depth limit
        if depth > self.max_depth:
            logger.debug(f"Skipping directory (max depth): {relative_path}")
            return dir_info

        stats.directories_found += 1

        try:
            entries = sorted(os.listdir(current_path))
        except PermissionError:
            logger.warning(f"Permission denied: {current_path}")
            return dir_info

        dir_file_count = 0

        for entry in entries:
            entry_path = os.path.join(current_path, entry)
            entry_relative = os.path.join(relative_path, entry) if relative_path else entry

            is_dir = os.path.isdir(entry_path)

            # Check ignore rules
            if self.ignore_parser.should_ignore(entry_relative, is_dir):
                if not is_dir:
                    stats.files_ignored += 1
                continue

            if is_dir:
                # Recursively scan subdirectory
                dir_info.subdirs.append(entry)
                self._scan_directory(
                    entry_path,
                    repo_root,
                    depth + 1,
                    files,
                    directories,
                    stats,
                    calculate_tokens,
                )
            else:
                # Process file
                stats.total_files_found += 1
                dir_file_count += 1

                # Check if we've exceeded max total files
                if len(files) >= self.max_total_files:
                    logger.warning(
                        f"Max total files limit ({self.max_total_files}) reached"
                    )
                    continue

                # Check if we've exceeded max files per directory
                if dir_file_count > self.max_files_per_dir:
                    logger.debug(
                        f"Max files per dir ({self.max_files_per_dir}) reached in {relative_path}"
                    )
                    continue

                scanned_file = self._scan_file(
                    entry_path,
                    entry_relative,
                    calculate_tokens,
                )
                files.append(scanned_file)

                # Update directory file type stats
                ext = os.path.splitext(entry)[1].lower() or "(no ext)"
                dir_info.file_types[ext] = dir_info.file_types.get(ext, 0) + 1
                dir_info.file_count += 1
                dir_info.total_tokens += scanned_file.tokens

        directories.append(dir_info)
        return dir_info

    def _scan_file(
        self,
        file_path: str,
        relative_path: str,
        calculate_tokens: bool,
    ) -> ScannedFile:
        """
        Scan a single file and get its information.

        Args:
            file_path: Absolute path to the file
            relative_path: Path relative to repository root
            calculate_tokens: Whether to calculate actual token count

        Returns:
            ScannedFile with file information
        """
        try:
            size_bytes = os.path.getsize(file_path)
        except OSError:
            size_bytes = 0

        # Check file size limit
        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            return ScannedFile(
                path=file_path,
                relative_path=relative_path,
                tokens=0,
                size_bytes=size_bytes,
                action=FileAction.METADATA_ONLY,
                reason="File too large",
            )

        # Calculate tokens
        if calculate_tokens and size_bytes > 0:
            tokens = token_counter.count_file_tokens(file_path)
        else:
            tokens = token_counter.estimate_tokens_from_size(size_bytes)

        # Check if this file should be summarized
        should_summarize = self.ignore_parser.should_summarize(relative_path)

        return ScannedFile(
            path=file_path,
            relative_path=relative_path,
            tokens=tokens,
            size_bytes=size_bytes,
            action=FileAction.SUMMARY if should_summarize else FileAction.FULL_SCAN,
            reason="Marked for summary in .wikiignore" if should_summarize else "",
        )

    def quick_estimate(self, repo_path: str) -> Tuple[int, int, int]:
        """
        Quick token estimation without full file reading.

        Args:
            repo_path: Path to repository root

        Returns:
            Tuple of (total files, total estimated tokens, ignored files)
        """
        repo_path = os.path.abspath(repo_path)
        self.ignore_parser.load_gitignore(repo_path)

        total_files = 0
        total_tokens = 0
        ignored_files = 0

        for root, dirs, filenames in os.walk(repo_path):
            # Get relative path
            rel_root = os.path.relpath(root, repo_path)
            if rel_root == ".":
                rel_root = ""

            # Check depth
            depth = len(rel_root.split(os.sep)) if rel_root else 0
            if depth > self.max_depth:
                dirs.clear()  # Don't recurse deeper
                continue

            # Filter directories
            dirs[:] = [
                d for d in dirs
                if not self.ignore_parser.should_ignore(
                    os.path.join(rel_root, d) if rel_root else d,
                    is_dir=True,
                )
            ]

            for filename in filenames:
                rel_path = os.path.join(rel_root, filename) if rel_root else filename

                if self.ignore_parser.should_ignore(rel_path, is_dir=False):
                    ignored_files += 1
                    continue

                total_files += 1
                try:
                    file_path = os.path.join(root, filename)
                    size = os.path.getsize(file_path)
                    if size <= self.MAX_FILE_SIZE_BYTES:
                        total_tokens += token_counter.estimate_tokens_from_size(size)
                except OSError:
                    pass

        return total_files, total_tokens, ignored_files

    def get_file_extension_stats(
        self, files: List[ScannedFile]
    ) -> Dict[str, Tuple[int, int]]:
        """
        Get statistics grouped by file extension.

        Args:
            files: List of scanned files

        Returns:
            Dictionary mapping extension to (file_count, total_tokens)
        """
        stats: Dict[str, Tuple[int, int]] = {}
        for f in files:
            if f.action == FileAction.IGNORED:
                continue
            ext = os.path.splitext(f.relative_path)[1].lower() or "(no ext)"
            count, tokens = stats.get(ext, (0, 0))
            stats[ext] = (count + 1, tokens + f.tokens)
        return stats
