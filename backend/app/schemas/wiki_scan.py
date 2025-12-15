# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Wiki Scan Schemas

Pydantic schemas for wiki token optimization and scan reports.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ========== Token Budget Schemas ==========
class TokenBudgetConfig(BaseModel):
    """Token budget configuration."""

    max_total_tokens: int = Field(
        default=200000,
        description="Maximum total token budget",
    )
    reserve_tokens: int = Field(
        default=20000,
        description="Tokens reserved for prompt and output",
    )
    optimization_enabled: bool = Field(
        default=True,
        description="Whether to enable token optimization",
    )


class TokenBudgetResult(BaseModel):
    """Token budget result in scan report."""

    max_total: int
    reserved: int
    available: int
    initial_required: int
    final_used: int
    optimization_applied: bool


# ========== File Detail Schemas ==========
class FileDetailItem(BaseModel):
    """File detail in scan report."""

    path: str
    tokens: int
    importance: str
    action: str
    reason: str = ""
    summary_tokens: Optional[int] = None


# ========== Directory Merge Schemas ==========
class MergedDirectoryItem(BaseModel):
    """Merged directory information in scan report."""

    pattern: str
    total_dirs: int
    sampled_dirs: List[str]
    reason: str
    tokens_saved: int


# ========== Warning Schemas ==========
class ScanWarning(BaseModel):
    """Warning item in scan report."""

    type: str
    path: str
    message: str


# ========== Statistics Schemas ==========
class ScanStatisticsResult(BaseModel):
    """Scan statistics in report."""

    total_files_found: int = 0
    files_ignored: int = 0
    files_scanned_full: int = 0
    files_scanned_summary: int = 0
    files_skipped: int = 0
    files_metadata_only: int = 0
    directories_found: int = 0


# ========== Repository Info Schemas ==========
class RepositoryInfo(BaseModel):
    """Repository information in scan report."""

    path: Optional[str] = None
    url: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None


# ========== Scan Report Schema ==========
class WikiScanReport(BaseModel):
    """Complete scan report for wiki generation."""

    report_version: str = "1.0"
    generated_at: str
    repository: RepositoryInfo
    token_budget: TokenBudgetResult
    scan_statistics: ScanStatisticsResult
    ignore_rules_applied: Dict[str, List[str]] = Field(default_factory=dict)
    file_details: List[FileDetailItem] = Field(default_factory=list)
    merged_directories: List[MergedDirectoryItem] = Field(default_factory=list)
    warnings: List[ScanWarning] = Field(default_factory=list)


# ========== API Request/Response Schemas ==========
class WikiPreviewRequest(BaseModel):
    """Request for wiki scan preview."""

    repository_url: str = Field(..., description="Repository URL")
    branch: Optional[str] = Field(None, description="Branch name")
    token_budget: Optional[int] = Field(
        None,
        description="Token budget (uses default if not specified)",
    )
    optimization_enabled: bool = Field(
        default=True,
        description="Whether to enable optimization",
    )
    custom_ignore_rules: Optional[List[str]] = Field(
        None,
        description="Additional ignore rules",
    )


class WikiPreviewResponse(BaseModel):
    """Response for wiki scan preview."""

    success: bool
    error: Optional[str] = None
    optimization_needed: bool = False
    initial_tokens: int = 0
    final_tokens: int = 0
    files_total: int = 0
    files_scanned: int = 0
    files_summarized: int = 0
    files_skipped: int = 0
    merged_directories: int = 0
    report: Optional[WikiScanReport] = None


class WikiGenerationCreateWithOptimization(BaseModel):
    """Extended wiki generation create request with optimization settings."""

    project_name: str = Field(..., description="Project name")
    source_url: str = Field(..., description="Source URL")
    source_id: Optional[str] = Field(None, description="Source ID")
    source_domain: Optional[str] = Field(None, description="Source domain")
    project_type: str = Field(default="git", description="Project type")
    source_type: str = Field(default="github", description="Source type")
    generation_type: str = Field(default="full", description="Generation type")
    language: Optional[str] = Field(
        default="en",
        description="Target language for documentation",
    )
    source_snapshot: Dict[str, Any] = Field(..., description="Source snapshot")
    ext: Optional[Dict[str, Any]] = Field(None, description="Extension fields")

    # Optimization settings
    token_budget: Optional[int] = Field(
        None,
        description="Token budget (uses default if not specified)",
    )
    optimization_enabled: bool = Field(
        default=True,
        description="Whether to enable token optimization",
    )
    custom_ignore_rules: Optional[List[str]] = Field(
        None,
        description="Additional ignore rules",
    )


# ========== Scan Report Summary Schemas ==========
class WikiScanReportSummary(BaseModel):
    """Summary view of scan report for API response."""

    optimization_applied: bool
    initial_tokens: int
    final_tokens: int
    tokens_saved: int
    files_total: int
    files_processed: int
    files_skipped: int
    directories_merged: int
    warnings_count: int

    @classmethod
    def from_report(cls, report: WikiScanReport) -> "WikiScanReportSummary":
        """Create summary from full report."""
        return cls(
            optimization_applied=report.token_budget.optimization_applied,
            initial_tokens=report.token_budget.initial_required,
            final_tokens=report.token_budget.final_used,
            tokens_saved=report.token_budget.initial_required - report.token_budget.final_used,
            files_total=report.scan_statistics.total_files_found,
            files_processed=(
                report.scan_statistics.files_scanned_full
                + report.scan_statistics.files_scanned_summary
            ),
            files_skipped=report.scan_statistics.files_skipped,
            directories_merged=len(report.merged_directories),
            warnings_count=len(report.warnings),
        )
