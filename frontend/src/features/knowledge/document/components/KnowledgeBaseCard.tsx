// SPDX-FileCopyrightText: 2025 WeCode, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useState } from 'react'
import { FolderOpen, MoreVertical, Pencil, Trash2, FileText } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { KnowledgeBase } from '@/types/knowledge'
import { useTranslation } from '@/hooks/useTranslation'

interface KnowledgeBaseCardProps {
  knowledgeBase: KnowledgeBase
  onEdit?: (kb: KnowledgeBase) => void
  onDelete?: (kb: KnowledgeBase) => void
  onClick?: (kb: KnowledgeBase) => void
  canManage?: boolean
}

export function KnowledgeBaseCard({
  knowledgeBase,
  onEdit,
  onDelete,
  onClick,
  canManage = true,
}: KnowledgeBaseCardProps) {
  const { t } = useTranslation()
  const [showMenu, setShowMenu] = useState(false)

  const handleCardClick = () => {
    onClick?.(knowledgeBase)
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowMenu(false)
    onEdit?.(knowledgeBase)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowMenu(false)
    onDelete?.(knowledgeBase)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <Card
      className="p-4 cursor-pointer hover:bg-surface transition-colors relative group"
      onClick={handleCardClick}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <FolderOpen className="w-5 h-5 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-text-primary truncate">
            {knowledgeBase.name}
          </h3>
          {knowledgeBase.description && (
            <p className="text-sm text-text-secondary mt-1 line-clamp-2">
              {knowledgeBase.description}
            </p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {knowledgeBase.document_count} {t('knowledge.document.documents')}
            </span>
            <span>{formatDate(knowledgeBase.updated_at)}</span>
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
                <div className="absolute right-0 top-full mt-1 bg-surface border border-border rounded-lg shadow-lg py-1 z-50 min-w-[120px]">
                  <button
                    className="w-full px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2"
                    onClick={handleEdit}
                  >
                    <Pencil className="w-4 h-4" />
                    {t('actions.edit')}
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
    </Card>
  )
}
