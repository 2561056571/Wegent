// SPDX-FileCopyrightText: 2025 WeCode, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Users, User, FolderOpen, Plus } from 'lucide-react'
import { Spinner } from '@/components/ui/spinner'
import { Card } from '@/components/ui/card'
import { KnowledgeBaseCard } from './KnowledgeBaseCard'
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
        <div className="p-4 bg-base">
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {/* Add knowledge base card */}
              <Card
                padding="sm"
                className="hover:bg-hover transition-colors cursor-pointer flex flex-col items-center justify-center h-[120px]"
                onClick={onCreateKb}
              >
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-2">
                  <Plus className="w-5 h-5 text-primary" />
                </div>
                <span className="text-sm font-medium text-text-primary">
                  {t('knowledge.document.knowledgeBase.create')}
                </span>
              </Card>

              {/* Knowledge base cards */}
              {knowledgeBases.map((kb) => (
                <KnowledgeBaseCard
                  key={kb.id}
                  knowledgeBase={kb}
                  onClick={onSelectKb}
                  onEdit={onEditKb}
                  onDelete={onDeleteKb}
                  canManage={true}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
