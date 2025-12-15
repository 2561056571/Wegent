# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Token Counter Module

Provides precise token counting using tiktoken library for Claude models.
"""

import logging
from typing import Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)


class TokenCounter:
    """
    Token counter for estimating token usage in wiki generation.

    Uses tiktoken with cl100k_base encoding (compatible with Claude models).
    Falls back to character-based estimation if tiktoken is not available.
    """

    # Default encoding for Claude models
    DEFAULT_ENCODING = "cl100k_base"

    # Fallback ratio: approximately 4 characters per token
    CHARS_PER_TOKEN_FALLBACK = 4

    def __init__(self, encoding_name: str = DEFAULT_ENCODING):
        """
        Initialize the token counter.

        Args:
            encoding_name: The tiktoken encoding to use (default: cl100k_base)
        """
        self.encoding_name = encoding_name
        self._encoding = None
        self._use_fallback = False

        if TIKTOKEN_AVAILABLE:
            try:
                self._encoding = tiktoken.get_encoding(encoding_name)
                logger.info(f"TokenCounter initialized with tiktoken encoding: {encoding_name}")
            except Exception as e:
                logger.warning(f"Failed to load tiktoken encoding: {e}. Using fallback method.")
                self._use_fallback = True
        else:
            logger.warning("tiktoken not available. Using character-based fallback estimation.")
            self._use_fallback = True

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens in the text
        """
        if not text:
            return 0

        if self._use_fallback:
            return self._count_tokens_fallback(text)

        try:
            return len(self._encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}. Using fallback.")
            return self._count_tokens_fallback(text)

    def _count_tokens_fallback(self, text: str) -> int:
        """
        Fallback token counting using character ratio.

        Args:
            text: The text to count tokens for

        Returns:
            Estimated number of tokens
        """
        return max(1, len(text) // self.CHARS_PER_TOKEN_FALLBACK)

    def count_file_tokens(self, file_path: str, encoding: str = "utf-8") -> int:
        """
        Count tokens in a file.

        Args:
            file_path: Path to the file
            encoding: File encoding (default: utf-8)

        Returns:
            Number of tokens in the file, or 0 if file cannot be read
        """
        try:
            with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                content = f.read()
            return self.count_tokens(content)
        except Exception as e:
            logger.warning(f"Failed to count tokens in file {file_path}: {e}")
            return 0

    def estimate_tokens_from_size(self, file_size_bytes: int) -> int:
        """
        Estimate tokens from file size without reading the file.

        This is a rough estimation useful for quick pre-scanning.
        Assumes approximately 1 token per 4 bytes (for text files).

        Args:
            file_size_bytes: File size in bytes

        Returns:
            Estimated number of tokens
        """
        return max(1, file_size_bytes // 4)

    @staticmethod
    def is_tiktoken_available() -> bool:
        """Check if tiktoken is available for precise counting."""
        return TIKTOKEN_AVAILABLE


# Global token counter instance
token_counter = TokenCounter()
