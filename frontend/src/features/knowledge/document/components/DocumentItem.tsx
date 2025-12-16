// SPDX-FileCopyrightText: 2025 WeCode, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { FileText, MoreVertical, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { KnowledgeDocument } from '@/types/knowledge'
import { useTranslation } from '@/hooks/useTranslation'

interface DocumentItemProps {
  document: KnowledgeDocument
  onToggleStatus?: (doc: KnowledgeDocument) => void
  onDelete?: (doc: KnowledgeDocument) => void
  canManage?: boolean
}

export function DocumentItem({
  document,
  onToggleStatus,
  onDelete,
  canManage = true,
}: DocumentItemProps) {
  const { t } = useTranslation()
  const [showMenu, setShowMenu] = useState(false)

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
    setShowMenu(false)
    onToggleStatus?.(document)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowMenu(false)
    onDelete?.(document)
  }

  const getFileIcon = () => {
    // Could add more specific icons based on extension in the future
    // const ext = document.file_extension.toLowerCase()
    return <FileText className="w-5 h-5 text-primary" />
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-surface transition-colors group">
      <div className="p-2 bg-primary/10 rounded-lg">
        {getFileIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-text-primary truncate">
            {document.name}
          </span>
          <Badge
            variant={document.status === 'enabled' ? 'success' : 'secondary'}
            size="sm"
          >
            {document.status === 'enabled'
              ? t('knowledge.document.document.status.enabled')
              : t('knowledge.document.document.status.disabled')}
          </Badge>
        </div>
        <div className="flex items-center gap-3 mt-1 text-xs text-text-muted">
          <span>{document.file_extension.toUpperCase()}</span>
          <span>{formatFileSize(document.file_size)}</span>
          <span>{formatDate(document.created_at)}</span>
        </div>
      </div>
      {canManage && (
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => {
              e.stopPropagation()
              setShowMenu(!showMenu)
            }}
          >
            <MoreVertical className="w-4 h-4" />
          </Button>
          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowMenu(false)
                }}
              />
              <div className="absolute right-0 top-full mt-1 bg-surface border border-border rounded-lg shadow-lg py-1 z-50 min-w-[140px]">
                <button
                  className="w-full px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2"
                  onClick={handleToggleStatus}
                >
                  {document.status === 'enabled' ? (
                    <>
                      <ToggleLeft className="w-4 h-4" />
                      {t('knowledge.document.document.disable')}
                    </>
                  ) : (
                    <>
                      <ToggleRight className="w-4 h-4" />
                      {t('knowledge.document.document.enable')}
                    </>
                  )}
                </button>
                <button
                  className="w-full px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2 text-error"
                  onClick={handleDelete}
                >
                  <Trash2 className="w-4 h-4" />
                  {t('actions.delete')}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
