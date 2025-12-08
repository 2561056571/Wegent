// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client';

import Modal from '@/features/common/Modal';
import { GitRepoInfo, Team } from '@/types/api';
import { useUser } from '@/features/common/UserContext';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { paths } from '@/config/paths';
import { useTranslation } from 'react-i18next';
import RepositorySelector from '@/features/tasks/components/RepositorySelector';
import TeamSelector from '@/features/tasks/components/TeamSelector';
import ModelSelector, { Model } from '@/features/tasks/components/ModelSelector';

interface AddRepoModalProps {
  isOpen: boolean;
  onClose: () => void;
  formData: {
    source_url: string;
    branch_name: string;
    language: string;
  };
  formErrors: Record<string, string>;
  isSubmitting: boolean;
  onRepoChange: (repo: GitRepoInfo | null) => void;
  onLanguageChange: (language: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  selectedRepo: GitRepoInfo | null;
  // Team and Model props
  teams: Team[];
  teamsLoading: boolean;
  selectedTeam: Team | null;
  onTeamChange: (team: Team | null) => void;
  selectedModel: Model | null;
  onModelChange: (model: Model | null) => void;
  forceOverride: boolean;
  onForceOverrideChange: (force: boolean) => void;
  defaultTeamId: number | null;
}

export default function AddRepoModal({
  isOpen,
  onClose,
  formData,
  formErrors,
  isSubmitting,
  onRepoChange,
  onLanguageChange,
  onSubmit,
  selectedRepo,
  teams,
  teamsLoading,
  selectedTeam,
  onTeamChange,
  selectedModel,
  onModelChange,
  forceOverride,
  onForceOverrideChange,
}: AddRepoModalProps) {
  const { t } = useTranslation();
  const { user } = useUser();
  const router = useRouter();

  const hasGitInfo = () => {
    return user && user.git_info && user.git_info.length > 0;
  };

  const handleGoToSettings = () => {
    onClose();
    router.push(paths.settings.integrations.getHref());
  };

  // Check if user has git info configured
  if (!hasGitInfo()) {
    return (
      <Modal isOpen={isOpen} onClose={onClose} title={t('wiki.add_repository')} maxWidth="md">
        <div className="flex flex-col items-center py-8">
          <p className="text-sm text-text-secondary mb-6 text-center leading-relaxed">
            {t('guide.description')}
          </p>
          <Button variant="default" size="sm" onClick={handleGoToSettings}>
            {t('branches.set_token')}
          </Button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t('wiki.add_repository')} maxWidth="lg">
      <form onSubmit={onSubmit} className="space-y-5">
        {formErrors.submit && <div className="text-red-500 text-sm mb-4">{formErrors.submit}</div>}

        {/* Repository Selector */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">
            {t('wiki.repository')}
          </label>
          <div className="px-3 py-2 border border-border rounded-md bg-base">
            <RepositorySelector
              selectedRepo={selectedRepo}
              handleRepoChange={onRepoChange}
              disabled={isSubmitting}
              fullWidth
            />
          </div>
          {formErrors.source_url && (
            <p className="mt-1 text-sm text-red-500">{formErrors.source_url}</p>
          )}
        </div>

        {/* Team and Model Selector - Same Row */}
        <div className="grid grid-cols-2 gap-4">
          {/* Team Selector */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              {t('wiki.team', 'Team')}
            </label>
            <div className="px-3 py-2 border border-border rounded-md bg-base">
              <TeamSelector
                selectedTeam={selectedTeam}
                setSelectedTeam={onTeamChange}
                teams={teams}
                disabled={isSubmitting}
                isLoading={teamsLoading}
                hideSettingsLink
              />
            </div>
          </div>

          {/* Model Selector */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              {t('wiki.model', 'Model')}
            </label>
            <div className="px-3 py-2 border border-border rounded-md bg-base">
              {selectedTeam ? (
                <ModelSelector
                  selectedModel={selectedModel}
                  setSelectedModel={onModelChange}
                  forceOverride={forceOverride}
                  setForceOverride={onForceOverrideChange}
                  selectedTeam={selectedTeam}
                  disabled={isSubmitting}
                />
              ) : (
                <span className="text-sm text-text-muted">
                  {t('wiki.select_team_first', 'Select a team first')}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Document Language - Radio Buttons */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">
            {t('wiki.document_language')}
          </label>
          <div className="flex items-center space-x-6">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                name="language"
                value="en"
                checked={formData.language === 'en'}
                onChange={e => onLanguageChange(e.target.value)}
                className="w-4 h-4 text-primary border-border focus:ring-primary/40"
              />
              <span className="text-sm text-text-primary">{t('wiki.language_en')}</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                name="language"
                value="zh"
                checked={formData.language === 'zh'}
                onChange={e => onLanguageChange(e.target.value)}
                className="w-4 h-4 text-primary border-border focus:ring-primary/40"
              />
              <span className="text-sm text-text-primary">{t('wiki.language_zh')}</span>
            </label>
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-text-primary bg-surface border border-border rounded-md hover:bg-surface-hover focus:outline-none focus:ring-2 focus:ring-primary/40"
            disabled={isSubmitting}
          >
            {t('actions.cancel')}
          </button>
          <button
            type="submit"
            className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-50"
            disabled={isSubmitting || !selectedRepo}
          >
            {isSubmitting ? (
              <div className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                {t('wiki.adding')}
              </div>
            ) : (
              t('wiki.add_repository')
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
