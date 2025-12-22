// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client';

import { useEffect, useState } from 'react';
import { Label } from '@/components/ui/label';
import { SearchableSelect } from '@/components/ui/searchable-select';
import { Input } from '@/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { useTranslation } from '@/hooks/useTranslation';
import { useRetrievers } from '../hooks/useRetrievers';
import { useEmbeddingModels } from '../hooks/useEmbeddingModels';
import { useRetrievalMethods } from '../hooks/useRetrievalMethods';
import Link from 'next/link';

export interface RetrievalConfig {
  retriever_name: string;
  retriever_namespace: string;
  embedding_config: {
    model_name: string;
    model_namespace: string;
  };
  retrieval_mode?: 'vector' | 'keyword' | 'hybrid';
  top_k?: number;
  score_threshold?: number;
  hybrid_weights?: {
    vector_weight: number;
    keyword_weight: number;
  };
}

interface RetrievalSettingsSectionProps {
  config: Partial<RetrievalConfig>;
  onChange: (config: Partial<RetrievalConfig>) => void;
  readOnly?: boolean;
  scope?: 'personal' | 'group' | 'all';
  groupName?: string;
}

export function RetrievalSettingsSection({
  config,
  onChange,
  readOnly = false,
  scope,
  groupName,
}: RetrievalSettingsSectionProps) {
  const { t } = useTranslation();
  const { retrievers, loading: loadingRetrievers } = useRetrievers(scope, groupName);
  const { models: embeddingModels, loading: loadingModels } = useEmbeddingModels();
  const { methods: retrievalMethods } = useRetrievalMethods();

  const [vectorWeight, setVectorWeight] = useState(
    config.hybrid_weights?.vector_weight ?? 0.7
  );
  const [keywordWeight, setKeywordWeight] = useState(
    config.hybrid_weights?.keyword_weight ?? 0.3
  );

  // Get available retrieval modes for selected retriever
  const selectedRetriever = retrievers.find(r => r.name === config.retriever_name);
  const availableModes = selectedRetriever
    ? retrievalMethods[selectedRetriever.storageType] || ['vector']
    : ['vector'];

  // Ensure vector mode is selected if current mode is not available
  useEffect(() => {
    if (config.retrieval_mode && !availableModes.includes(config.retrieval_mode)) {
      onChange({ ...config, retrieval_mode: 'vector' });
    }
  }, [availableModes, config, onChange]);

  const handleRetrieverChange = (value: string) => {
    const retriever = retrievers.find(r => r.name === value);
    if (retriever) {
      onChange({
        ...config,
        retriever_name: retriever.name,
        retriever_namespace: retriever.namespace,
      });
    }
  };

  const handleEmbeddingModelChange = (value: string) => {
    const model = embeddingModels.find(m => m.name === value);
    if (model) {
      onChange({
        ...config,
        embedding_config: {
          model_name: model.name,
          model_namespace: model.namespace || 'default',
        },
      });
    }
  };

  const handleRetrievalModeChange = (value: string) => {
    onChange({
      ...config,
      retrieval_mode: value as 'vector' | 'keyword' | 'hybrid',
    });
  };

  const handleVectorWeightChange = (value: number) => {
    setVectorWeight(value);
    const newKeywordWeight = Math.round((1 - value) * 100) / 100;
    setKeywordWeight(newKeywordWeight);
    onChange({
      ...config,
      hybrid_weights: {
        vector_weight: value,
        keyword_weight: newKeywordWeight,
      },
    });
  };

  const handleKeywordWeightChange = (value: number) => {
    setKeywordWeight(value);
    const newVectorWeight = Math.round((1 - value) * 100) / 100;
    setVectorWeight(newVectorWeight);
    onChange({
      ...config,
      hybrid_weights: {
        vector_weight: newVectorWeight,
        keyword_weight: value,
      },
    });
  };

  return (
    <div className="space-y-4">
      {/* Retriever Selection */}
      <div className="space-y-2">
        <Label htmlFor="retriever">{t('knowledge.document.retrieval.retriever')}</Label>
        {loadingRetrievers ? (
          <div className="text-sm text-text-secondary">
            {t('actions.loading')}
          </div>
        ) : retrievers.length === 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-warning">
              {t('knowledge.document.retrieval.noRetriever')}
            </p>
            <Link href="/settings" className="text-sm text-primary hover:underline">
              {t('knowledge.document.goToSettings')}
            </Link>
          </div>
        ) : (
          <>
            <SearchableSelect
              value={config.retriever_name || ''}
              onValueChange={handleRetrieverChange}
              placeholder={t('knowledge.document.retrieval.retrieverSelect')}
              disabled={readOnly}
            >
              {retrievers.map(retriever => (
                <option key={retriever.name} value={retriever.name}>
                  {retriever.displayName || retriever.name}
                </option>
              ))}
            </SearchableSelect>
            <p className="text-xs text-text-muted">
              {t('knowledge.document.retrieval.retrieverHint')}
            </p>
          </>
        )}
      </div>

      {/* Embedding Model Selection */}
      <div className="space-y-2">
        <Label htmlFor="embedding-model">
          {t('knowledge.document.retrieval.embeddingModel')}
        </Label>
        {loadingModels ? (
          <div className="text-sm text-text-secondary">
            {t('actions.loading')}
          </div>
        ) : embeddingModels.length === 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-warning">
              {t('knowledge.document.retrieval.noEmbeddingModel')}
            </p>
            <Link href="/settings" className="text-sm text-primary hover:underline">
              {t('knowledge.document.goToSettings')}
            </Link>
          </div>
        ) : (
          <>
            <SearchableSelect
              value={config.embedding_config?.model_name || ''}
              onValueChange={handleEmbeddingModelChange}
              placeholder={t('knowledge.document.retrieval.embeddingModelSelect')}
              disabled={readOnly}
            >
              {embeddingModels.map(model => (
                <option key={model.name} value={model.name}>
                  {model.displayName || model.name}
                </option>
              ))}
            </SearchableSelect>
            <p className="text-xs text-text-muted">
              {t('knowledge.document.retrieval.embeddingModelHint')}
            </p>
          </>
        )}
      </div>

      {/* Retrieval Mode */}
      <div className="space-y-2">
        <Label>{t('knowledge.document.retrieval.retrievalMode')}</Label>
        <RadioGroup
          value={config.retrieval_mode || 'vector'}
          onValueChange={handleRetrievalModeChange}
          disabled={readOnly}
        >
          {availableModes.includes('vector') && (
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="vector" id="mode-vector" />
              <Label htmlFor="mode-vector" className="font-normal cursor-pointer">
                {t('knowledge.document.retrieval.vector')}
              </Label>
            </div>
          )}
          {availableModes.includes('keyword') && (
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="keyword" id="mode-keyword" />
              <Label htmlFor="mode-keyword" className="font-normal cursor-pointer">
                {t('knowledge.document.retrieval.keyword')}
              </Label>
            </div>
          )}
          {availableModes.includes('hybrid') && (
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="hybrid" id="mode-hybrid" />
              <Label htmlFor="mode-hybrid" className="font-normal cursor-pointer">
                {t('knowledge.document.retrieval.hybrid')}
              </Label>
            </div>
          )}
        </RadioGroup>
      </div>

      {/* Top K */}
      <div className="space-y-2">
        <Label htmlFor="top-k">{t('knowledge.document.retrieval.topK')}</Label>
        <Input
          id="top-k"
          type="number"
          min={1}
          max={10}
          value={config.top_k ?? 5}
          onChange={e => onChange({ ...config, top_k: parseInt(e.target.value) })}
          disabled={readOnly}
        />
        <p className="text-xs text-text-muted">
          {t('knowledge.document.retrieval.topKHint')}
        </p>
      </div>

      {/* Score Threshold */}
      <div className="space-y-2">
        <Label htmlFor="score-threshold">
          {t('knowledge.document.retrieval.scoreThreshold')}
        </Label>
        <Input
          id="score-threshold"
          type="number"
          min={0}
          max={1}
          step={0.1}
          value={config.score_threshold ?? 0.7}
          onChange={e => onChange({ ...config, score_threshold: parseFloat(e.target.value) })}
          disabled={readOnly}
        />
        <p className="text-xs text-text-muted">
          {t('knowledge.document.retrieval.scoreThresholdHint')}
        </p>
      </div>

      {/* Hybrid Weights (only when hybrid mode is selected) */}
      {config.retrieval_mode === 'hybrid' && (
        <div className="space-y-4 p-4 border border-border rounded-md bg-bg-muted">
          <Label>{t('knowledge.document.retrieval.hybridWeights')}</Label>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="vector-weight" className="text-sm font-normal">
                {t('knowledge.document.retrieval.semanticWeight')}
              </Label>
              <span className="text-sm text-text-secondary">{vectorWeight.toFixed(2)}</span>
            </div>
            <Input
              id="vector-weight"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={vectorWeight}
              onChange={e => handleVectorWeightChange(parseFloat(e.target.value))}
              disabled={readOnly}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="keyword-weight" className="text-sm font-normal">
                {t('knowledge.document.retrieval.keywordWeight')}
              </Label>
              <span className="text-sm text-text-secondary">{keywordWeight.toFixed(2)}</span>
            </div>
            <Input
              id="keyword-weight"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={keywordWeight}
              onChange={e => handleKeywordWeightChange(parseFloat(e.target.value))}
              disabled={readOnly}
              className="w-full"
            />
          </div>

          <p className="text-xs text-text-muted">
            {t('knowledge.document.retrieval.weightSum')}
          </p>
        </div>
      )}
    </div>
  );
}
