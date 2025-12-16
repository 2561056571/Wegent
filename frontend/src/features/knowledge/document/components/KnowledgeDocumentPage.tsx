// SPDX-FileCopyrightText: 2025 WeCode, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Users, User, FolderOpen, Plus, FileText, Pencil, Trash2, ArrowRight } from 'lucide-react'
import { Spinner } from '@/components/ui/spinner'
import { Card } from '@/components/ui/card'
import { CreateKnowledgeBaseDialog } from './CreateKnowledgeBaseDialog'
import { EditKnowledgeBaseDialog } from './EditKnowledgeBaseDialog'
import { DeleteKnowledgeBaseDialog } from './DeleteKnowledgeBaseDialog'
import { DocumentList } from './DocumentList'
import { useTranslation } from '@/hooks/useTranslation'
import { listGroups } from '@/apis/groups'
import { useKnowledgeBases } from '../hooks/useKnowledgeBases'
import type { Group } from '@/types/group'
import type { KnowledgeBase } from '@/types/knowledge'

interface TreeSection {
  id: string
  label: string
  icon: React.ReactNode
  isGroup: boolean
  groupName?: string
}

export function KnowledgeDocumentPage() {
  const { t } = useTranslation()
  const [groups, setGroups] = useState<Group[]>([])
  const [loadingGroups, setLoadingGroups] = useState(true)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['personal']))
  const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null)

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [createForGroup, setCreateForGroup] = useState<string | null>(null)
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null)
  const [deletingKb, setDeletingKb] = useState<KnowledgeBase | null>(null)

  // Personal knowledge bases
  const personalKb = useKnowledgeBases({ scope: 'personal' })

  // Load user's groups
  useEffect(() => {
    const loadGroups = async () => {
      try {
        const response = await listGroups()
        setGroups(response.items || [])
      } catch (error) {
        console.error('Failed to load groups:', error)
      } finally {
        setLoadingGroups(false)
      }
    }
    loadGroups()
  }, [])

  // Build tree sections
  const sections: TreeSection[] = [
    {
      id: 'personal',
      label: t('knowledge.document.personal'),
      icon: <User className="w-4 h-4" />,
      isGroup: false,
    },
    ...groups.map((group) => ({
      id: group.name,
      label: group.display_name || group.name,
      icon: <Users className="w-4 h-4" />,
      isGroup: true,
      groupName: group.name,
    })),
  ]

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev)
      if (next.has(sectionId)) {
        next.delete(sectionId)
      } else {
        next.add(sectionId)
      }
      return next
    })
  }

  const handleCreateKb = (groupName: string | null) => {
    setCreateForGroup(groupName)
    setShowCreateDialog(true)
  }

  const handleCreate = async (data: { name: string; description?: string }) => {
    try {
      await personalKb.create({
        name: data.name,
        description: data.description,
        namespace: createForGroup || 'default',
      })
      setShowCreateDialog(false)
      setCreateForGroup(null)
      // Refresh
      personalKb.refresh()
    } catch {
      // Error handled by hook
    }
  }

  const handleUpdate = async (data: { name: string; description?: string }) => {
    if (!editingKb) return
    try {
      await personalKb.update(editingKb.id, data)
      setEditingKb(null)
    } catch {
      // Error handled by hook
    }
  }

  const handleDelete = async () => {
    if (!deletingKb) return
    try {
      await personalKb.remove(deletingKb.id)
      setDeletingKb(null)
    } catch {
      // Error handled by hook
    }
  }

  if (loadingGroups) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner />
      </div>
    )
  }

  // Show document list if a knowledge base is selected
  if (selectedKb) {
    return (
      <DocumentList
        knowledgeBase={selectedKb}
        onBack={() => {
          setSelectedKb(null)
          personalKb.refresh()
        }}
        canManage={true}
      />
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {sections.map((section) => (
        <TreeSectionComponent
          key={section.id}
          section={section}
          isExpanded={expandedSections.has(section.id)}
          onToggle={() => toggleSection(section.id)}
          onCreateKb={() => handleCreateKb(section.isGroup ? section.groupName! : null)}
          onSelectKb={setSelectedKb}
          onEditKb={setEditingKb}
          onDeleteKb={setDeletingKb}
        />
      ))}

      {/* No teams hint */}
      {groups.length === 0 && (
        <div className="p-4 bg-muted rounded-lg">
          <div className="flex items-start gap-3">
            <FolderOpen className="w-5 h-5 text-text-muted mt-0.5" />
            <p className="text-sm text-text-secondary">
              {t('knowledge.document.noTeamHint')}
            </p>
          </div>
        </div>
      )}

      {/* Dialogs */}
      <CreateKnowledgeBaseDialog
        open={showCreateDialog}
        onOpenChange={(open) => {
          setShowCreateDialog(open)
          if (!open) setCreateForGroup(null)
        }}
        onSubmit={handleCreate}
        loading={personalKb.loading}
      />

      <EditKnowledgeBaseDialog
        open={!!editingKb}
        onOpenChange={(open) => !open && setEditingKb(null)}
        knowledgeBase={editingKb}
        onSubmit={handleUpdate}
        loading={personalKb.loading}
      />

      <DeleteKnowledgeBaseDialog
        open={!!deletingKb}
        onOpenChange={(open) => !open && setDeletingKb(null)}
        knowledgeBase={deletingKb}
        onConfirm={handleDelete}
        loading={personalKb.loading}
      />
    </div>
  )
}

// Tree section component
interface TreeSectionComponentProps {
  section: TreeSection
  isExpanded: boolean
  onToggle: () => void
  onCreateKb: () => void
  onSelectKb: (kb: KnowledgeBase) => void
  onEditKb: (kb: KnowledgeBase) => void
  onDeleteKb: (kb: KnowledgeBase) => void
}

function TreeSectionComponent({
  section,
  isExpanded,
  onToggle,
  onCreateKb,
  onSelectKb,
  onEditKb,
  onDeleteKb,
}: TreeSectionComponentProps) {
  const { t } = useTranslation()
  const { knowledgeBases, loading } = useKnowledgeBases({
    scope: section.isGroup ? 'group' : 'personal',
    groupName: section.groupName,
  })

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Section header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-4 py-3 bg-surface hover:bg-muted transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-text-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-text-muted" />
        )}
        {section.icon}
        <span className="font-medium text-sm text-text-primary">{section.label}</span>
        <span className="text-xs text-text-muted ml-1">({knowledgeBases.length})</span>
      </button>

      {/* Section content */}
      {isExpanded && (
        <div className="bg-base">
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : knowledgeBases.length === 0 ? (
            // Empty state - show centered add card
            <div className="flex justify-center py-8">
              <Card
                padding="sm"
                className="hover:bg-hover transition-colors cursor-pointer flex flex-col items-center justify-center w-64 h-32"
                onClick={onCreateKb}
              >
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-2">
                  <Plus className="w-5 h-5 text-primary" />
                </div>
                <span className="text-sm font-medium text-text-primary">
                  {t('knowledge.document.knowledgeBase.create')}
                </span>
              </Card>
            </div>
          ) : (
            // Knowledge base list
            <div>
              {/* Add button row */}
              <div className="px-4 py-2 border-b border-border">
                <button
                  onClick={onCreateKb}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-md transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  {t('knowledge.document.knowledgeBase.create')}
                </button>
              </div>
              {/* Knowledge base items */}
              {knowledgeBases.map((kb, index) => (
                <KnowledgeBaseItem
                  key={kb.id}
                  knowledgeBase={kb}
                  onClick={() => onSelectKb(kb)}
                  onEdit={() => onEditKb(kb)}
                  onDelete={() => onDeleteKb(kb)}
                  showBorder={index < knowledgeBases.length - 1}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Knowledge base list item component
interface KnowledgeBaseItemProps {
  knowledgeBase: KnowledgeBase
  onClick: () => void
  onEdit: () => void
  onDelete: () => void
  showBorder?: boolean
}

function KnowledgeBaseItem({
  knowledgeBase,
  onClick,
  onEdit,
  onDelete,
  showBorder = true,
}: KnowledgeBaseItemProps) {
  const { t } = useTranslation()

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <div
      className={`flex items-center gap-4 px-4 py-3 hover:bg-surface transition-colors cursor-pointer group ${showBorder ? 'border-b border-border' : ''}`}
      onClick={onClick}
    >
      {/* Icon */}
      <div className="p-2 bg-primary/10 rounded-lg flex-shrink-0">
        <FolderOpen className="w-4 h-4 text-primary" />
      </div>

      {/* Name and description */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-text-primary truncate">
          {knowledgeBase.name}
        </div>
        {knowledgeBase.description && (
          <div className="text-xs text-text-muted truncate">
            {knowledgeBase.description}
          </div>
        )}
      </div>

      {/* Document count */}
      <div className="flex items-center gap-1 text-xs text-text-muted flex-shrink-0">
        <FileText className="w-3 h-3" />
        <span>{knowledgeBase.document_count}</span>
      </div>

      {/* Update date */}
      <div className="w-24 flex-shrink-0 text-right">
        <span className="text-xs text-text-muted">
          {formatDate(knowledgeBase.updated_at)}
        </span>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-1 flex-shrink-0">
        <button
          className="p-1.5 rounded-md text-text-muted hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
          onClick={(e) => {
            e.stopPropagation()
            onEdit()
          }}
          title={t('actions.edit')}
        >
          <Pencil className="w-3.5 h-3.5" />
        </button>
        <button
          className="p-1.5 rounded-md text-text-muted hover:text-error hover:bg-error/10 transition-colors opacity-0 group-hover:opacity-100"
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          title={t('actions.delete')}
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
        <button
          className="p-1.5 rounded-md text-text-muted hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
          onClick={(e) => {
            e.stopPropagation()
            onClick()
          }}
          title={t('actions.view')}
        >
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
