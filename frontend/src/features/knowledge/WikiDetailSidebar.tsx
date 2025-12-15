// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

import { WikiGenerationDetail, WikiContent, WikiTocItem } from '@/types/wiki';
import { getSortedContents } from './wikiUtils';
import { getTocFromContent, getH2TocItems } from './tocUtils';
import { useTranslation } from '@/hooks/useTranslation';
import { useMemo } from 'react';

interface WikiDetailSidebarProps {
  wikiDetail: WikiGenerationDetail | null;
  loading: boolean;
  error: string | null;
  selectedContentId: number | null;
  onBackToList: () => void;
  onSelectContent: (contentId: number) => void;
  onTocItemClick?: (id: string) => void;
  activeTocId?: string | null;
}

/**
 * Wiki detail page sidebar component
 * Shows page list with H2 level sub-navigation for selected content
 */
export function WikiDetailSidebar({
  wikiDetail,
  loading,
  error,
  selectedContentId,
  onBackToList,
  onSelectContent,
  onTocItemClick,
  activeTocId,
}: WikiDetailSidebarProps) {
  const { t } = useTranslation('common');

  // Get sorted contents
  const sortedContents = useMemo(() => getSortedContents(wikiDetail), [wikiDetail]);

  // Build a map of content ID to H2 TOC items
  const contentTocMap = useMemo(() => {
    const map = new Map<number, WikiTocItem[]>();
    sortedContents.forEach((content) => {
      const fullToc = getTocFromContent(content);
      const h2Items = getH2TocItems(fullToc);
      if (h2Items.length > 0) {
        map.set(content.id, h2Items);
      }
    });
    return map;
  }, [sortedContents]);

  return (
    <div className="w-64 border-r border-border overflow-y-auto bg-surface/10">
      <div className="p-4 sticky top-0">
        <button
          onClick={onBackToList}
          className="flex items-center text-sm text-primary mb-4 hover:underline"
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          {t('wiki.back_to_list')}
        </button>

        <h2 className="text-lg font-medium mb-2 border-b border-border pb-2">
          {wikiDetail?.project?.source_url ? (
            <a
              href={wikiDetail.project.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:text-primary-hover transition-colors duration-200 flex items-center group"
              title="Open repository in new tab"
            >
              <span>{wikiDetail.project.project_name}</span>
              <svg
                className="w-4 h-4 ml-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>
          ) : (
            <span>{wikiDetail?.project?.project_name || t('wiki.loading')}</span>
          )}
        </h2>

        {wikiDetail?.updated_at && (
          <div className="mb-4 text-xs text-text-muted flex items-center">
            <svg
              className="w-3.5 h-3.5 mr-1.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>
              {t('wiki.last_indexed')}:{' '}
              {new Date(wikiDetail.updated_at).toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
        ) : error ? (
          <div className="text-red-500 text-sm">{error}</div>
        ) : (
          <ul className="space-y-0.5">
            {sortedContents.map((content: WikiContent) => {
              const isSelected = selectedContentId === content.id;
              const h2Items = contentTocMap.get(content.id) || [];

              return (
                <li key={content.id}>
                  {/* Main content item */}
                  <div
                    className={`p-2 rounded-md cursor-pointer transition-colors duration-200 ${
                      isSelected
                        ? 'bg-primary/15 text-primary font-medium border-l-2 border-primary pl-3'
                        : 'hover:bg-surface-hover pl-3.5'
                    }`}
                    onClick={() => onSelectContent(content.id)}
                  >
                    <span className="text-sm">{content.title}</span>
                  </div>

                  {/* H2 sub-navigation (only show for selected content) */}
                  {isSelected && h2Items.length > 0 && (
                    <ul className="ml-4 mt-1 space-y-0.5 border-l border-border/50">
                      {h2Items.map((tocItem) => (
                        <li key={tocItem.id}>
                          <button
                            className={`w-full text-left pl-3 pr-2 py-1.5 text-xs rounded-r transition-colors duration-200 ${
                              activeTocId === tocItem.id
                                ? 'text-primary bg-primary/10 border-l-2 border-primary -ml-[1px]'
                                : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                            }`}
                            onClick={(e) => {
                              e.stopPropagation();
                              onTocItemClick?.(tocItem.id);
                            }}
                          >
                            <span className="line-clamp-2">{tocItem.text}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
