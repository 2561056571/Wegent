# SPDX-FileCopyrightText: 2025 WeCode, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Knowledge base and document models for document knowledge management.

Provides storage for user and team knowledge bases with document management.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    BigInteger,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DocumentStatus(str, PyEnum):
    """Document status for knowledge documents."""

    ENABLED = "enabled"
    DISABLED = "disabled"


class KnowledgeBase(Base):
    """
    Knowledge base model for document organization.

    Supports both personal knowledge bases (namespace='default') and
    team knowledge bases (namespace=group_name).
    """

    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    user_id = Column(Integer, nullable=False, index=True)
    # 'default' for personal knowledge base, group_name for team knowledge base
    namespace = Column(String(255), nullable=False, default="default", index=True)
    # Cached document count for performance
    document_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    documents = relationship(
        "KnowledgeDocument",
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Unique constraint: same name within user and namespace
        Index(
            "ix_knowledge_bases_name_user_namespace",
            "name",
            "user_id",
            "namespace",
            unique=True,
        ),
        # Index for listing knowledge bases
        Index(
            "ix_knowledge_bases_user_namespace_active",
            "user_id",
            "namespace",
            "is_active",
        ),
        {
            "sqlite_autoincrement": True,
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
            "comment": "Knowledge base table for document organization",
        },
    )


class KnowledgeDocument(Base):
    """
    Knowledge document model for storing document metadata.

    Links to subtask_attachments table for actual file storage.
    """

    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    attachment_id = Column(
        Integer,
        ForeignKey("subtask_attachments.id", ondelete="SET NULL"),
        nullable=True,
    )
    name = Column(String(255), nullable=False)
    file_extension = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)
    status = Column(
        SQLEnum(DocumentStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DocumentStatus.ENABLED,
    )
    user_id = Column(Integer, nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

    __table_args__ = (
        # Index for listing documents in a knowledge base
        Index(
            "ix_knowledge_documents_base_active_created",
            "knowledge_base_id",
            "is_active",
            "created_at",
        ),
        # Index for attachment lookup
        Index("ix_knowledge_documents_attachment", "attachment_id"),
        {
            "sqlite_autoincrement": True,
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
            "comment": "Knowledge document table for file metadata",
        },
    )
