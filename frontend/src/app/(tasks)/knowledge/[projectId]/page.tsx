// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client';

import { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import TopNavigation from '@/features/layout/TopNavigation';
import UserMenu from '@/features/layout/UserMenu';
import '@/app/tasks/tasks.css';
import '@/features/common/scrollbar.css';
import { GithubStarButton } from '@/features/layout/GithubStarButton';
import { useTranslation } from '@/hooks/useTranslation';
import { saveLastTab } from '@/utils/userPreferences';
import {
  wikiStyles,
  WikiDetailSidebar,
  useMermaidInit,
  WikiContent,
  useWikiDetail,
  WikiTableOfContents,
  WikiTableOfContentsMobile,
  useActiveHeading,
  scrollToHeadingInContainer,
  getTocFromContent,
} from '@/features/knowledge';
import { useIsMobile } from '@/features/layout/hooks/useMediaQuery';

export default function WikiDetailPage() {
  const { t: _t } = useTranslation('common');
  const params = useParams();
  const router = useRouter();
  const projectId = Number(params.projectId);
  const isMobile = useIsMobile();

  // Reference to the content scrollable container
  const contentRef = useRef<HTMLDivElement>(null);

  // Mobile TOC panel state
  const [isTocPanelOpen, setIsTocPanelOpen] = useState(false);

  // Use shared Hook to manage detail page data
  const { wikiDetail, loading, error, selectedContentId, selectedContent, handleSelectContent } =
    useWikiDetail(projectId);

  // Get TOC from selected content
  const currentToc = useMemo(() => getTocFromContent(selectedContent), [selectedContent]);

  // Get heading IDs for active tracking
  const headingIds = useMemo(() => currentToc.map((item) => item.id), [currentToc]);

  // Track active heading during scroll
  const activeHeadingId = useActiveHeading(headingIds, contentRef);

  // Handle TOC item click
  const handleTocItemClick = useCallback(
    (id: string) => {
      scrollToHeadingInContainer(id, contentRef.current, 80);
    },
    []
  );

  const handleBackToList = () => {
    router.push('/knowledge');
  };

  // Save last active tab to localStorage
  useEffect(() => {
    saveLastTab('wiki');
  }, []);

  // Use shared Mermaid initialization Hook
  useMermaidInit(selectedContent);

  return (
    <div>
      <style jsx global>
        {wikiStyles}
      </style>

      <div className="flex smart-h-screen bg-base text-text-primary box-border">
        <div className="flex-1 flex flex-col min-w-0">
          <TopNavigation activePage="wiki" variant="standalone">
            <GithubStarButton />
            <UserMenu />
          </TopNavigation>

          <div className="flex h-full overflow-hidden">
            {/* Left Sidebar - Page List with H2 sub-navigation */}
            <WikiDetailSidebar
              wikiDetail={wikiDetail}
              loading={loading}
              error={error}
              selectedContentId={selectedContentId}
              onBackToList={handleBackToList}
              onSelectContent={handleSelectContent}
              onTocItemClick={handleTocItemClick}
              activeTocId={activeHeadingId}
            />

            {/* Main Content Area */}
            <div ref={contentRef} className="flex-1 overflow-auto p-6 bg-surface/5">
              <WikiContent content={selectedContent} loading={loading} error={error} />
            </div>

            {/* Right Sidebar - Table of Contents (Desktop) */}
            {!isMobile && currentToc.length > 0 && (
              <WikiTableOfContents
                toc={currentToc}
                activeId={activeHeadingId}
                onItemClick={handleTocItemClick}
              />
            )}
          </div>
        </div>
      </div>

      {/* Mobile TOC - Floating Button + Panel */}
      {isMobile && currentToc.length > 0 && (
        <>
          <WikiTableOfContents
            toc={currentToc}
            activeId={activeHeadingId}
            onItemClick={handleTocItemClick}
            collapsed={!isTocPanelOpen}
            onToggleCollapse={() => setIsTocPanelOpen(true)}
          />
          <WikiTableOfContentsMobile
            toc={currentToc}
            activeId={activeHeadingId}
            onItemClick={handleTocItemClick}
            isOpen={isTocPanelOpen}
            onClose={() => setIsTocPanelOpen(false)}
          />
        </>
      )}
    </div>
  );
}
