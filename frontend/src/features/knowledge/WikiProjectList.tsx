// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { WikiProject, WikiGeneration } from '@/types/wiki';
import { getProjectDisplayName } from './wikiUtils';
import { Card } from '@/components/ui/card';

interface WikiProjectListProps {
  projects: (WikiProject & { generations?: WikiGeneration[] })[];
  loading: boolean;
  loadingMore?: boolean;
  error: string | null;
  onAddRepo: () => void;
  onProjectClick: (projectId: number) => void;
  onTaskClick: (taskId: number) => void;
  onCancelClick: (projectId: number, e: React.MouseEvent) => void;
  cancellingIds: Set<number>;
  searchTerm?: string;
  hasMore?: boolean;
  onLoadMore?: () => void;
}

export default function WikiProjectList({
  projects,
  loading,
  loadingMore = false,
  error,
  onAddRepo,
  onProjectClick,
  onTaskClick,
  onCancelClick,
  cancellingIds,
  searchTerm = '',
  hasMore = false,
  onLoadMore,
}: WikiProjectListProps) {
  const { t } = useTranslation();
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreTriggerRef = useRef<HTMLDivElement | null>(null);

  // Setup intersection observer for infinite scroll
  const setupObserver = useCallback(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    if (!hasMore || !onLoadMore) return;

    observerRef.current = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && onLoadMore) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreTriggerRef.current) {
      observerRef.current.observe(loadMoreTriggerRef.current);
    }
  }, [hasMore, loadingMore, onLoadMore]);

  useEffect(() => {
    setupObserver();
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [setupObserver]);
  // Filter projects
  const filteredProjects = projects.filter(project => {
    const matchesSearch =
      project.project_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (project.description &&
        project.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
      project.project_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.source_type.toLowerCase().includes(searchTerm.toLowerCase());

    const hasValidGeneration =
      !project.generations ||
      project.generations.length === 0 ||
      (project.generations[0].status !== 'FAILED' && project.generations[0].status !== 'CANCELLED');

    return matchesSearch && hasValidGeneration;
  });

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return <div className="bg-red-50 text-red-500 p-4 rounded-md">{error}</div>;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {/* Add repository card */}
        <Card
          padding="sm"
          className="hover:bg-hover transition-colors cursor-pointer flex flex-col items-center justify-center h-[100px]"
          onClick={onAddRepo}
        >
          <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center mb-1.5">
            <svg
              className="h-4 w-4 text-primary"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
          </div>
          <h3 className="font-medium text-sm mb-0.5">{t('wiki.add_repository')}</h3>
          <p className="text-xs text-text-muted text-center">{t('wiki.add_repository_desc')}</p>
        </Card>

        {/* Empty state message - shown when no projects */}
        {projects.length === 0 && (
          <div className="col-span-1 md:col-span-1 lg:col-span-2 flex items-center justify-center h-[100px]">
            <div className="text-center text-text-muted">
              <p className="text-sm">{t('wiki.no_projects')}</p>
            </div>
          </div>
        )}

        {/* Project card list */}
        {filteredProjects.map(project => {
          // Check if project is currently generating (RUNNING or PENDING)
          const isGenerating =
            project.generations &&
            project.generations.length > 0 &&
            (project.generations[0].status === 'RUNNING' ||
              project.generations[0].status === 'PENDING');
          const taskId = isGenerating ? project.generations![0].task_id : null;

          return (
            <Card
              key={project.id}
              padding="sm"
              className="hover:bg-hover transition-colors cursor-pointer h-[100px] flex flex-col"
              onClick={() => {
                if (isGenerating && taskId) {
                  // Navigate to task page when generating
                  onTaskClick(taskId);
                } else {
                  // Navigate to wiki detail page when completed
                  onProjectClick(project.id);
                }
              }}
            >
              {/* Project header */}
              <div className="flex items-start mb-1.5 flex-shrink-0">
                <div className="w-4 h-4 mr-1.5 flex-shrink-0 text-text-muted mt-0.5">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h3 className="font-medium text-sm leading-tight line-clamp-1">
                  {(() => {
                    const displayName = getProjectDisplayName(project);
                    if (displayName.hasSlash) {
                      return (
                        <span className="flex items-center flex-wrap">
                          <span className="text-text-muted text-xs">{displayName.parts[0]}</span>
                          <span className="mx-0.5 text-text-muted font-normal">/</span>
                          <span>{displayName.parts[1]}</span>
                        </span>
                      );
                    }
                    return <span>{displayName.parts[0]}</span>;
                  })()}
                </h3>
              </div>

              {/* Project info - takes remaining space */}
              <div className="text-xs text-text-muted flex-1 min-h-0">
                <p className="flex items-center">
                  <span className="mr-1">{t('wiki.source')}:</span>
                  <span className="capitalize">{project.source_type}</span>
                </p>
                {project.description && (
                  <p className="mt-0.5 line-clamp-1">{project.description}</p>
                )}
              </div>

              {/* Wiki generation status - only show when indexing */}
              {project.generations &&
                project.generations.length > 0 &&
                (project.generations[0].status === 'RUNNING' ||
                  project.generations[0].status === 'PENDING') && (
                  <div className="mt-auto pt-1.5 border-t border-border flex-shrink-0">
                    <div className="flex items-center justify-between">
                      {/* Status indicator */}
                      <span className="px-1.5 py-0.5 text-xs rounded-full bg-primary/10 text-primary flex items-center gap-1">
                        <span className="w-1 h-1 rounded-full bg-primary animate-pulse"></span>
                        {t('wiki.indexing')}
                      </span>
                      {/* Cancel button */}
                      <button
                        className="px-1.5 py-0.5 text-xs rounded-full text-text-muted border border-border hover:bg-hover hover:text-error transition-colors"
                        onClick={e => onCancelClick(project.id, e)}
                        title={t('wiki.cancel_title')}
                        disabled={cancellingIds.has(project.generations[0].id)}
                      >
                        {cancellingIds.has(project.generations[0].id)
                          ? t('wiki.cancelling')
                          : t('wiki.cancel')}
                      </button>
                    </div>
                  </div>
                )}
            </Card>
          );
        })}
        {/* Load more trigger - invisible element that triggers loading when scrolled into view */}
        {hasMore && onLoadMore && <div ref={loadMoreTriggerRef} className="col-span-full h-10" />}

        {/* Loading more indicator */}
        {loadingMore && (
          <div className="col-span-full flex justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
        )}
      </div>
    </div>
  );
}
