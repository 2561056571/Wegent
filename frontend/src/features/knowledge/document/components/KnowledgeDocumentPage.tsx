// SPDX-FileCopyrightText: 2025 WeCode, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useState, useEffect } from 'react'
import { Users, User, FolderOpen } from 'lucide-react'
import { Spinner } from '@/components/ui/spinner'
import { KnowledgeBaseList } from './KnowledgeBaseList'
import { useTranslation } from '@/hooks/useTranslation'
import { listGroups } from '@/apis/groups'
import type { Group } from '@/types/group'

type TabType = 'personal' | string // 'personal' or group name

interface TabItem {
  id: TabType
  label: string
  icon: React.ReactNode
}

export function KnowledgeDocumentPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabType>('personal')
  const [groups, setGroups] = useState<Group[]>([])
  const [loadingGroups, setLoadingGroups] = useState(true)

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

  // Build tabs: personal + groups
  const tabs: TabItem[] = [
    {
      id: 'personal',
      label: t('knowledge.document.personal'),
      icon: <User className="w-4 h-4" />,
    },
    ...groups.map((group) => ({
      id: group.name,
      label: group.display_name || group.name,
      icon: <Users className="w-4 h-4" />,
    })),
  ]

  if (loadingGroups) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Tab navigation - consistent with KnowledgeTabs style */}
      <div className="flex items-center gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium
              transition-colors duration-200 whitespace-nowrap
              ${
                activeTab === tab.id
                  ? 'text-primary bg-primary/10'
                  : 'text-text-secondary hover:text-text-primary hover:bg-muted'
              }
            `}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content based on active tab */}
      {activeTab === 'personal' ? (
        <KnowledgeBaseList scope="personal" canManage={true} />
      ) : (
        <KnowledgeBaseList
          scope="group"
          groupName={activeTab}
          canManage={true}
        />
      )}

      {/* Show hint when no groups */}
      {groups.length === 0 && (
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <div className="flex items-start gap-3">
            <FolderOpen className="w-5 h-5 text-text-muted mt-0.5" />
            <div>
              <p className="text-sm text-text-secondary">
                {t('knowledge.document.noTeamHint')}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
