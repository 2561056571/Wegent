# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Scan Optimizer Module

Coordinates the optimization process for wiki generation scanning.
Manages token budget and applies optimization strategies.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from app.services.wiki.file_scanner import (
    DirectoryInfo,
    FileAction,
    FileImportance,
    FileScanner,
    ScannedFile,
    ScanStatistics,
)
from app.services.wiki.ignore_rules import IgnoreRulesParser
from app.services.wiki.importance_analyzer import ImportanceAnalyzer
from app.services.wiki.similarity_detector import SimilarityDetector, SimilarityGroup
from app.services.wiki.summary_generator import SummaryGenerator

logger = logging.getLogger(__name__)


@dataclass
class TokenBudget:
    """Token budget configuration and tracking."""

    max_total: int = 200000
    reserved: int = 20000
    available: int = 180000
    initial_required: int = 0
    final_used: int = 0
    optimization_applied: bool = False


@dataclass
class ScanReport:
    """Complete scan report for wiki generation."""

    report_version: str = "1.0"
    generated_at: str = ""
    repository: Dict[str, Any] = field(default_factory=dict)
    token_budget: Dict[str, Any] = field(default_factory=dict)
    scan_statistics: Dict[str, Any] = field(default_factory=dict)
    ignore_rules_applied: Dict[str, List[str]] = field(default_factory=dict)
    file_details: List[Dict[str, Any]] = field(default_factory=list)
    merged_directories: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_version": self.report_version,
            "generated_at": self.generated_at,
            "repository": self.repository,
            "token_budget": self.token_budget,
            "scan_statistics": self.scan_statistics,
            "ignore_rules_applied": self.ignore_rules_applied,
            "file_details": self.file_details,
            "merged_directories": self.merged_directories,
            "warnings": self.warnings,
        }


@dataclass
class OptimizationResult:
    """Result of the optimization process."""

    files: List[ScannedFile]
    report: ScanReport
    success: bool = True
    error_message: Optional[str] = None


class ScanOptimizer:
    """
    Coordinates scan optimization for wiki generation.

    Optimization flow:
    1. Load ignore rules
    2. Pre-scan for token estimation
    3. Check budget, apply optimization if needed:
       a. Analyze file importance
       b. Detect similar directories
       c. Apply summarization for large files
       d. Skip low-priority files
    4. Generate scan report
    """

    # Token thresholds for file processing
    NORMAL_THRESHOLD = 10000  # Files under this: full scan
    LARGE_THRESHOLD = 50000   # Files under this: generate summary
    # Files above LARGE_THRESHOLD: metadata only

    def __init__(
        self,
        max_total_tokens: int = 200000,
        reserve_tokens: int = 20000,
        wikiignore_path: Optional[str] = None,
        max_scan_depth: int = 10,
        max_files_per_dir: int = 100,
        max_total_files: int = 1000,
        enable_ai_analysis: bool = False,
    ):
        """
        Initialize the scan optimizer.

        Args:
            max_total_tokens: Maximum total token budget
            reserve_tokens: Tokens reserved for prompt and output
            wikiignore_path: Path to .wikiignore configuration file
            max_scan_depth: Maximum directory depth to scan
            max_files_per_dir: Maximum files per directory
            max_total_files: Maximum total files to process
            enable_ai_analysis: Whether to use AI for importance analysis
        """
        self.budget = TokenBudget(
            max_total=max_total_tokens,
            reserved=reserve_tokens,
            available=max_total_tokens - reserve_tokens,
        )

        self.wikiignore_path = wikiignore_path
        self.max_scan_depth = max_scan_depth
        self.max_files_per_dir = max_files_per_dir
        self.max_total_files = max_total_files
        self.enable_ai_analysis = enable_ai_analysis

        # Initialize components
        self.ignore_parser = IgnoreRulesParser(wikiignore_path=wikiignore_path)
        self.importance_analyzer = ImportanceAnalyzer(use_ai=enable_ai_analysis)
        self.similarity_detector = SimilarityDetector()
        self.summary_generator = SummaryGenerator()

    def optimize(
        self,
        repo_path: str,
        repo_url: Optional[str] = None,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
    ) -> OptimizationResult:
        """
        Run the full optimization process on a repository.

        Args:
            repo_path: Path to the repository
            repo_url: Repository URL (for report)
            branch: Branch name (for report)
            commit: Commit hash (for report)

        Returns:
            OptimizationResult with optimized file list and report
        """
        try:
            repo_path = os.path.abspath(repo_path)
            if not os.path.isdir(repo_path):
                return OptimizationResult(
                    files=[],
                    report=ScanReport(),
                    success=False,
                    error_message=f"Repository path does not exist: {repo_path}",
                )

            # Initialize report
            report = ScanReport(
                generated_at=datetime.utcnow().isoformat() + "Z",
                repository={
                    "path": repo_path,
                    "url": repo_url or "",
                    "branch": branch or "",
                    "commit": commit or "",
                },
            )

            # Load ignore rules
            self.ignore_parser.load_gitignore(repo_path)
            if self.wikiignore_path:
                self.ignore_parser.load_wikiignore()

            # Override max depth if set in wikiignore
            if self.ignore_parser.max_depth is not None:
                self.max_scan_depth = self.ignore_parser.max_depth

            # Record ignore rules
            rules = self.ignore_parser.get_all_patterns()
            report.ignore_rules_applied = {
                "builtin": rules["builtin"][:20],  # Limit for report size
                "gitignore": rules["gitignore"][:50],
                "wikiignore": rules["wikiignore"][:50],
            }

            # Initialize scanner
            scanner = FileScanner(
                ignore_parser=self.ignore_parser,
                max_depth=self.max_scan_depth,
                max_files_per_dir=self.max_files_per_dir,
                max_total_files=self.max_total_files,
            )

            # Scan repository
            files, stats, directories = scanner.scan_repository(
                repo_path, calculate_tokens=True
            )

            # Record initial statistics
            self.budget.initial_required = stats.total_tokens_estimated
            report.scan_statistics = {
                "total_files_found": stats.total_files_found,
                "files_ignored": stats.files_ignored,
                "directories_found": stats.directories_found,
            }

            # Check if optimization is needed
            if self.budget.initial_required <= self.budget.available:
                # No optimization needed
                self._finalize_report(report, files, stats, [])
                return OptimizationResult(files=files, report=report)

            # Apply optimization
            self.budget.optimization_applied = True
            files, similarity_groups = self._apply_optimization(
                files, directories, stats, report
            )

            # Finalize report
            self._finalize_report(report, files, stats, similarity_groups)

            return OptimizationResult(files=files, report=report)

        except Exception as e:
            logger.exception(f"Optimization failed: {e}")
            return OptimizationResult(
                files=[],
                report=ScanReport(),
                success=False,
                error_message=str(e),
            )

    def _apply_optimization(
        self,
        files: List[ScannedFile],
        directories: List[DirectoryInfo],
        stats: ScanStatistics,
        report: ScanReport,
    ) -> tuple[List[ScannedFile], List[SimilarityGroup]]:
        """
        Apply optimization strategies to reduce token usage.

        Args:
            files: Scanned files
            directories: Directory information
            stats: Scan statistics
            report: Report to update

        Returns:
            Tuple of (optimized files, similarity groups)
        """
        # Step 1: Analyze file importance
        files = self.importance_analyzer.analyze_files(files)

        # Step 2: Detect similar directories
        similarity_groups = self.similarity_detector.detect_similar_groups(directories)
        skip_dirs = self.similarity_detector.get_files_to_skip(similarity_groups)

        # Step 3: Apply optimization to each file
        current_tokens = 0
        for file in files:
            # Skip files in merged directories
            file_dir = os.path.dirname(file.relative_path)
            if file_dir in skip_dirs:
                file.action = FileAction.SKIPPED
                file.reason = "Directory merged with similar directories"
                stats.files_skipped += 1
                continue

            # Determine action based on importance and budget
            if file.importance == FileImportance.SKIP:
                file.action = FileAction.SKIPPED
                file.reason = "Low importance (generated/test file)"
                stats.files_skipped += 1
                continue

            # Check if we can afford full scan
            if current_tokens + file.tokens <= self.budget.available:
                # Check file size for summary decision
                if file.tokens > self.LARGE_THRESHOLD:
                    file.action = FileAction.METADATA_ONLY
                    file.reason = "File too large, metadata only"
                    stats.files_metadata_only += 1
                    report.warnings.append({
                        "type": "large_file_truncated",
                        "path": file.relative_path,
                        "message": f"File has {file.tokens:,} tokens, only metadata recorded",
                    })
                elif file.tokens > self.NORMAL_THRESHOLD:
                    # Generate summary
                    file.action = FileAction.SUMMARY
                    file.summary_tokens = min(
                        file.tokens // 5, self.summary_generator.max_summary_tokens
                    )
                    file.reason = "Large file, summary generated"
                    current_tokens += file.summary_tokens
                    stats.files_scanned_summary += 1
                else:
                    file.action = FileAction.FULL_SCAN
                    file.reason = ""
                    current_tokens += file.tokens
                    stats.files_scanned_full += 1
            else:
                # Budget exceeded - decide based on importance
                if file.importance.value >= FileImportance.HIGH.value:
                    # High importance: try summary
                    if file.tokens > self.NORMAL_THRESHOLD:
                        file.action = FileAction.SUMMARY
                        file.summary_tokens = min(
                            file.tokens // 5, self.summary_generator.max_summary_tokens
                        )
                        file.reason = "Budget constrained, summary generated"
                        current_tokens += file.summary_tokens
                        stats.files_scanned_summary += 1
                    else:
                        file.action = FileAction.FULL_SCAN
                        file.reason = "High priority file included"
                        current_tokens += file.tokens
                        stats.files_scanned_full += 1
                else:
                    file.action = FileAction.SKIPPED
                    file.reason = f"Token budget exceeded, priority: {file.importance.name}"
                    stats.files_skipped += 1

        # Update final token count
        self.budget.final_used = current_tokens
        stats.total_tokens_after_optimization = current_tokens

        return files, similarity_groups

    def _finalize_report(
        self,
        report: ScanReport,
        files: List[ScannedFile],
        stats: ScanStatistics,
        similarity_groups: List[SimilarityGroup],
    ):
        """
        Finalize the scan report with all statistics.

        Args:
            report: Report to finalize
            files: Processed files
            stats: Scan statistics
            similarity_groups: Detected similarity groups
        """
        # Token budget section
        report.token_budget = {
            "max_total": self.budget.max_total,
            "reserved": self.budget.reserved,
            "available": self.budget.available,
            "initial_required": self.budget.initial_required,
            "final_used": self.budget.final_used,
            "optimization_applied": self.budget.optimization_applied,
        }

        # Scan statistics section
        report.scan_statistics.update({
            "files_scanned_full": stats.files_scanned_full,
            "files_scanned_summary": stats.files_scanned_summary,
            "files_skipped": stats.files_skipped,
            "files_metadata_only": stats.files_metadata_only,
        })

        # File details (limit to avoid huge reports)
        max_file_details = 500
        for file in files[:max_file_details]:
            detail = {
                "path": file.relative_path,
                "tokens": file.tokens,
                "importance": file.importance.name,
                "action": file.action.value,
                "reason": file.reason,
            }
            if file.summary_tokens:
                detail["summary_tokens"] = file.summary_tokens
            report.file_details.append(detail)

        if len(files) > max_file_details:
            report.warnings.append({
                "type": "file_details_truncated",
                "path": "",
                "message": f"File details truncated to {max_file_details} entries",
            })

        # Merged directories section
        for group in similarity_groups:
            report.merged_directories.append({
                "pattern": group.pattern,
                "total_dirs": len(group.directories),
                "sampled_dirs": group.sampled_dirs,
                "reason": group.reason,
                "tokens_saved": group.tokens_saved,
            })

    def get_files_for_scanning(
        self, result: OptimizationResult
    ) -> List[ScannedFile]:
        """
        Get the list of files that should be scanned (not skipped).

        Args:
            result: Optimization result

        Returns:
            List of files to scan
        """
        return [
            f for f in result.files
            if f.action in (FileAction.FULL_SCAN, FileAction.SUMMARY)
        ]

    def estimate_final_tokens(self, result: OptimizationResult) -> int:
        """
        Estimate final token usage based on optimization result.

        Args:
            result: Optimization result

        Returns:
            Estimated total tokens
        """
        total = 0
        for file in result.files:
            if file.action == FileAction.FULL_SCAN:
                total += file.tokens
            elif file.action == FileAction.SUMMARY:
                total += file.summary_tokens or (file.tokens // 5)
        return total


# Convenience function for quick preview
def preview_scan(
    repo_path: str,
    max_tokens: int = 200000,
    wikiignore_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Quick preview of scan results without full optimization.

    Args:
        repo_path: Path to repository
        max_tokens: Token budget
        wikiignore_path: Path to .wikiignore

    Returns:
        Dictionary with preview results
    """
    optimizer = ScanOptimizer(
        max_total_tokens=max_tokens,
        wikiignore_path=wikiignore_path,
    )
    result = optimizer.optimize(repo_path)

    return {
        "success": result.success,
        "error": result.error_message,
        "optimization_needed": result.report.token_budget.get("optimization_applied", False),
        "initial_tokens": result.report.token_budget.get("initial_required", 0),
        "final_tokens": result.report.token_budget.get("final_used", 0),
        "files_total": result.report.scan_statistics.get("total_files_found", 0),
        "files_scanned": result.report.scan_statistics.get("files_scanned_full", 0),
        "files_summarized": result.report.scan_statistics.get("files_scanned_summary", 0),
        "files_skipped": result.report.scan_statistics.get("files_skipped", 0),
        "merged_directories": len(result.report.merged_directories),
    }
