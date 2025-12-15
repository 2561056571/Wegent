# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Optional

from pydantic_settings import BaseSettings


class WikiSettings(BaseSettings):
    """Wiki feature independent configuration"""

    # Wiki tables now use main database (task_manager)
    # DATABASE_URL configuration removed - wiki tables share the main database

    # Wiki feature toggle (env var: WIKI_ENABLED)
    ENABLED: bool = True

    # Wiki task configuration (env vars: WIKI_DEFAULT_TEAM_NAME, WIKI_DEFAULT_AGENT_TYPE, WIKI_DEFAULT_USER_ID, WIKI_DEFAULT_LANGUAGE)
    DEFAULT_TEAM_NAME: str = (
        "wiki-team"  # Default execution team name (matches init_data/01-default-resources.yaml)
    )
    DEFAULT_AGENT_TYPE: str = "ClaudeCode"  # Default agent type
    DEFAULT_USER_ID: int = 0  # Default user ID for task creation (0 = use current user)
    DEFAULT_LANGUAGE: str = (
        "en"  # Default language for wiki documentation generation (en/zh)
    )

    # Wiki generation configuration (env vars: WIKI_MAX_CONCURRENT_GENERATIONS)
    MAX_CONCURRENT_GENERATIONS: int = 5  # Maximum concurrent generations
    RESULT_POLL_INTERVAL_SECONDS: int = 30  # Background polling interval
    RESULT_POLL_BATCH_SIZE: int = 20  # Background polling batch size

    # Wiki content configuration (env var: WIKI_MAX_CONTENT_SIZE)
    MAX_CONTENT_SIZE: int = 10 * 1024 * 1024  # Maximum content size 10MB
    SUPPORTED_FORMATS: list[str] = ["markdown", "html"]  # Supported formats
    CONTENT_WRITE_BASE_URL: str = (
        "http://localhost:8000"  # Base server address for internal wiki content writer
    )
    CONTENT_WRITE_ENDPOINT: str = (
        "/api/internal/wiki/generations/contents"  # Fixed relative path for content writes
    )
    DEFAULT_SECTION_TYPES: list[str] = [
        "overview",
        "architecture",
        "module",
        "api",
        "guide",
        "deep",
    ]
    INTERNAL_API_TOKEN: str = (
        "weki"  # Internal authentication token for content write API
    )

    # Token optimization configuration (env vars: WIKI_MAX_TOKENS, WIKI_RESERVE_TOKENS, etc.)
    MAX_TOKENS: int = 200000  # Maximum total token budget
    RESERVE_TOKENS: int = 20000  # Tokens reserved for prompt and output
    MAX_SCAN_DEPTH: int = 10  # Maximum directory scan depth
    MAX_FILES_PER_DIR: int = 100  # Maximum files per directory before sampling
    MAX_TOTAL_FILES: int = 1000  # Maximum total files to process
    LARGE_FILE_THRESHOLD: int = 10000  # Token threshold for summary generation
    HUGE_FILE_THRESHOLD: int = 50000  # Token threshold for metadata-only
    ENABLE_AI_ANALYSIS: bool = False  # Enable AI-based importance analysis
    IGNORE_CONFIG_PATH: Optional[str] = None  # Path to .wikiignore file

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "WIKI_"  # Environment variable prefix
        extra = "ignore"  # Ignore extra fields from .env file

    def get_wikiignore_path(self) -> Optional[str]:
        """Get the path to .wikiignore configuration file."""
        if self.IGNORE_CONFIG_PATH:
            return self.IGNORE_CONFIG_PATH
        # Default path: backend/config/.wikiignore
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            ".wikiignore",
        )
        if os.path.isfile(default_path):
            return default_path
        return None


# Global wiki configuration instance
wiki_settings = WikiSettings()
