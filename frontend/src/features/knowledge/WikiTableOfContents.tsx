// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useTranslation } from '@/hooks/useTranslation'
import type { WikiTocItem } from '@/types/wiki'
import { ListBulletIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { cn } from '@/lib/utils'

interface WikiTableOfContentsProps {
  toc: WikiTocItem[]
  activeId: string | null
  onItemClick: (id: string) => void
  collapsed?: boolean
  onToggleCollapse?: () => void
  className?: string
}

/**
 * Wiki Table of Contents component for right sidebar navigation.
 * Displays H2/H3 headings with hierarchical indentation and active state highlighting.
 */
export function WikiTableOfContents({
  toc,
  activeId,
  onItemClick,
  collapsed = false,
  onToggleCollapse,
  className,
}: WikiTableOfContentsProps) {
  const { t } = useTranslation('common')

  // Mobile floating toggle button
  if (collapsed) {
    return (
      <button
        onClick={onToggleCollapse}
        className="fixed right-4 bottom-20 z-50 w-11 h-11 flex items-center justify-center rounded-full bg-primary text-white shadow-lg hover:bg-primary/90 transition-colors duration-200 md:hidden"
        title={t('wiki.expand_toc')}
        aria-label={t('wiki.expand_toc')}
      >
        <ListBulletIcon className="w-5 h-5" />
      </button>
    )
  }

  const hasItems = toc.length > 0

  return (
    <aside
      className={cn(
        'w-56 shrink-0 border-l border-border bg-surface/10 overflow-hidden',
        'hidden lg:block',
        className
      )}
    >
      <div className="sticky top-0 h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
          <h3 className="text-sm font-medium text-text-secondary">
            {t('wiki.table_of_contents')}
          </h3>
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="p-1 rounded hover:bg-hover text-text-muted hover:text-text-secondary transition-colors lg:hidden"
              title={t('wiki.collapse_toc')}
              aria-label={t('wiki.collapse_toc')}
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* TOC Items */}
        <nav className="flex-1 overflow-y-auto py-2">
          {hasItems ? (
            <ul className="space-y-0.5">
              {toc.map((item) => (
                <li key={item.id}>
                  <button
                    onClick={() => onItemClick(item.id)}
                    className={cn(
                      'w-full text-left px-4 py-1.5 text-[13px] leading-snug transition-all duration-200',
                      'hover:text-text-primary hover:bg-hover',
                      item.level === 3 && 'pl-7',
                      activeId === item.id
                        ? 'text-primary bg-primary/8 border-l-2 border-primary -ml-[2px] pl-[calc(1rem+2px)]'
                        : 'text-text-secondary border-l-2 border-transparent'
                    )}
                    style={
                      item.level === 3 && activeId === item.id
                        ? { paddingLeft: 'calc(1.75rem + 2px)' }
                        : undefined
                    }
                  >
                    <span className="line-clamp-2">{item.text}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-4 py-8 text-center text-text-muted text-sm">
              {t('wiki.no_headings')}
            </div>
          )}
        </nav>
      </div>
    </aside>
  )
}

/**
 * Mobile floating TOC panel.
 * Appears as a bottom sheet on mobile devices.
 */
export function WikiTableOfContentsMobile({
  toc,
  activeId,
  onItemClick,
  isOpen,
  onClose,
}: {
  toc: WikiTocItem[]
  activeId: string | null
  onItemClick: (id: string) => void
  isOpen: boolean
  onClose: () => void
}) {
  const { t } = useTranslation('common')

  if (!isOpen) return null

  const hasItems = toc.length > 0

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/50 lg:hidden"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="fixed right-0 bottom-0 left-0 z-50 bg-surface rounded-t-2xl shadow-xl max-h-[60vh] flex flex-col lg:hidden animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h3 className="text-sm font-medium text-text-primary">
            {t('wiki.table_of_contents')}
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-hover text-text-secondary transition-colors"
            aria-label={t('wiki.collapse_toc')}
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto py-2">
          {hasItems ? (
            <ul className="space-y-0.5">
              {toc.map((item) => (
                <li key={item.id}>
                  <button
                    onClick={() => {
                      onItemClick(item.id)
                      onClose()
                    }}
                    className={cn(
                      'w-full text-left px-4 py-2.5 text-sm transition-all duration-200',
                      'hover:text-text-primary hover:bg-hover',
                      item.level === 3 && 'pl-8',
                      activeId === item.id
                        ? 'text-primary bg-primary/8 border-l-2 border-primary'
                        : 'text-text-secondary border-l-2 border-transparent'
                    )}
                  >
                    <span className="line-clamp-2">{item.text}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-4 py-8 text-center text-text-muted text-sm">
              {t('wiki.no_headings')}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
