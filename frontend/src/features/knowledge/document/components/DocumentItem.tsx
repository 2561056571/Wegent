// SPDX-FileCopyrightText: 2025 WeCode, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { FileText, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { KnowledgeDocument } from '@/types/knowledge'
import { useTranslation } from '@/hooks/useTranslation'

interface DocumentItemProps {
  document: KnowledgeDocument
  onToggleStatus?: (doc: KnowledgeDocument) => void
  onDelete?: (doc: KnowledgeDocument) => void
  canManage?: boolean
  showBorder?: boolean
}

export function DocumentItem({
  document,
  onToggleStatus,
  onDelete,
  canManage = true,
  showBorder = true,
}: DocumentItemProps) {
  const { t } = useTranslation()

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const handleToggleStatus = (e: React.MouseEvent) => {
    e.stopPropagation()
    onToggleStatus?.(document)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDelete?.(document)
  }

  return (
    <div className={`flex items-center gap-4 px-4 py-3 bg-base hover:bg-surface transition-colors group ${showBorder ? 'border-b border-border' : ''}`}>
      {/* File icon */}
      <div className="p-2 bg-primary/10 rounded-lg flex-shrink-0">
        <FileText className="w-4 h-4 text-primary" />
      </div>

      {/* File name - takes most space */}
      <div className="flex-1 min-w-0">
        <span className="text-sm font-medium text-text-primary truncate block">
          {document.name}
        </span>
      </div>

      {/* Type */}
      <div className="w-16 flex-shrink-0 text-center">
        <span className="text-xs text-text-muted uppercase">
          {document.file_extension}
        </span>
      </div>

      {/* Size */}
      <div className="w-20 flex-shrink-0 text-right">
        <span className="text-xs text-text-muted">
          {formatFileSize(document.file_size)}
        </span>
      </div>

      {/* Upload date */}
      <div className="w-24 flex-shrink-0 text-right">
        <span className="text-xs text-text-muted">
          {formatDate(document.created_at)}
        </span>
      </div>

      {/* Status badge */}
      <div className="w-16 flex-shrink-0 text-center">
        <Badge
          variant={document.status === 'enabled' ? 'success' : 'secondary'}
          size="sm"
        >
          {document.status === 'enabled'
            ? t('knowledge.document.document.status.enabled')
            : t('knowledge.document.document.status.disabled')}
        </Badge>
      </div>

      {/* Action buttons */}
      {canManage && (
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            className="p-1.5 rounded-md text-text-muted hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
            onClick={handleToggleStatus}
            title={document.status === 'enabled'
              ? t('knowledge.document.document.disable')
              : t('knowledge.document.document.enable')}
          >
            {document.status === 'enabled' ? (
              <ToggleLeft className="w-4 h-4" />
            ) : (
              <ToggleRight className="w-4 h-4" />
            )}
          </button>
          <button
            className="p-1.5 rounded-md text-text-muted hover:text-error hover:bg-error/10 transition-colors opacity-0 group-hover:opacity-100"
            onClick={handleDelete}
            title={t('actions.delete')}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
