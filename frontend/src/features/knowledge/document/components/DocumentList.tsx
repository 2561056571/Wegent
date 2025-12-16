// SPDX-FileCopyrightText: 2025 WeCode, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useState, useMemo } from 'react'
import { ArrowLeft, Upload, FileText, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { DocumentItem } from './DocumentItem'
import { DocumentUpload } from './DocumentUpload'
import { DeleteDocumentDialog } from './DeleteDocumentDialog'
import { useDocuments } from '../hooks/useDocuments'
import type { KnowledgeBase, KnowledgeDocument } from '@/types/knowledge'
import { useTranslation } from '@/hooks/useTranslation'

interface DocumentListProps {
  knowledgeBase: KnowledgeBase
  onBack?: () => void
  canManage?: boolean
}

export function DocumentList({
  knowledgeBase,
  onBack,
  canManage = true,
}: DocumentListProps) {
  const { t } = useTranslation()
  const {
    documents,
    loading,
    error,
    create,
    toggleStatus,
    remove,
    refresh,
  } = useDocuments({ knowledgeBaseId: knowledgeBase.id })

  const [showUpload, setShowUpload] = useState(false)
  const [deletingDoc, setDeletingDoc] = useState<KnowledgeDocument | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const filteredDocuments = useMemo(() => {
    if (!searchQuery.trim()) return documents
    const query = searchQuery.toLowerCase()
    return documents.filter((doc) =>
      doc.name.toLowerCase().includes(query)
    )
  }, [documents, searchQuery])

  const handleUploadComplete = async (attachmentId: number, file: File) => {
    const extension = file.name.split('.').pop() || ''
    try {
      await create({
        attachment_id: attachmentId,
        name: file.name,
        file_extension: extension,
        file_size: file.size,
      })
      setShowUpload(false)
    } catch {
      // Error handled by hook
    }
  }

  const handleDelete = async () => {
    if (!deletingDoc) return
    try {
      await remove(deletingDoc.id)
      setDeletingDoc(null)
    } catch {
      // Error handled by hook
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        {onBack && (
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
        )}
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold text-text-primary truncate">
            {knowledgeBase.name}
          </h2>
          {knowledgeBase.description && (
            <p className="text-sm text-text-secondary truncate">
              {knowledgeBase.description}
            </p>
          )}
        </div>
      </div>

      {/* Search and upload bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            className="w-full h-9 pl-9 pr-3 text-sm bg-surface border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder={t('knowledge.document.document.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        {canManage && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowUpload(true)}
          >
            <Upload className="w-4 h-4 mr-1" />
            {t('knowledge.document.document.upload')}
          </Button>
        )}
      </div>

      {/* Document List */}
      {loading && documents.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Spinner />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12 text-text-secondary">
          <p>{error}</p>
          <Button variant="outline" className="mt-4" onClick={refresh}>
            {t('actions.retry')}
          </Button>
        </div>
      ) : filteredDocuments.length > 0 ? (
        <div className="border border-border rounded-lg overflow-hidden">
          {filteredDocuments.map((doc, index) => (
            <DocumentItem
              key={doc.id}
              document={doc}
              onToggleStatus={toggleStatus}
              onDelete={setDeletingDoc}
              canManage={canManage}
              showBorder={index < filteredDocuments.length - 1}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-text-secondary">
          <FileText className="w-12 h-12 mb-4 opacity-50" />
          <p>
            {searchQuery
              ? t('knowledge.document.document.noResults')
              : t('knowledge.document.document.empty')}
          </p>
          {!searchQuery && canManage && (
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => setShowUpload(true)}
            >
              <Upload className="w-4 h-4 mr-1" />
              {t('knowledge.document.document.upload')}
            </Button>
          )}
        </div>
      )}

      {/* Dialogs */}
      <DocumentUpload
        open={showUpload}
        onOpenChange={setShowUpload}
        onUploadComplete={handleUploadComplete}
      />

      <DeleteDocumentDialog
        open={!!deletingDoc}
        onOpenChange={(open) => !open && setDeletingDoc(null)}
        document={deletingDoc}
        onConfirm={handleDelete}
        loading={loading}
      />
    </div>
  )
}
