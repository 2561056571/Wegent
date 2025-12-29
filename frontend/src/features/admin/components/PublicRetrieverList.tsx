// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Tag } from '@/components/ui/tag';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CircleStackIcon,
  PencilIcon,
  TrashIcon,
  GlobeAltIcon,
  EyeIcon,
  EyeSlashIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useTranslation } from '@/hooks/useTranslation';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { adminApis, AdminPublicRetriever, RetrieverCRD } from '@/apis/admin';
import { retrieverApis, RetrievalMethodType } from '@/apis/retrievers';
import UnifiedAddButton from '@/components/common/UnifiedAddButton';

// Storage type configuration for extensibility
const STORAGE_TYPE_CONFIG = {
  elasticsearch: {
    defaultUrl: 'http://elasticsearch:9200',
    recommendedIndexMode: 'per_user' as const,
    authFields: {
      supportsUsernamePassword: true,
      supportsApiKey: false,
    },
    fallbackRetrievalMethods: ['vector', 'keyword', 'hybrid'] as const,
  },
  qdrant: {
    defaultUrl: 'http://localhost:6333',
    recommendedIndexMode: 'per_dataset' as const,
    authFields: {
      supportsUsernamePassword: false,
      supportsApiKey: true,
    },
    fallbackRetrievalMethods: ['vector'] as const,
  },
} as const;

// Retrieval method labels for display
const RETRIEVAL_METHOD_LABELS: Record<string, string> = {
  vector: 'retrievers.retrieval_method_vector',
  keyword: 'retrievers.retrieval_method_keyword',
  hybrid: 'retrievers.retrieval_method_hybrid',
};

type IndexModeType = 'fixed' | 'rolling' | 'per_dataset' | 'per_user';

interface RetrieverFormData {
  name: string;
  displayName: string;
  namespace: string;
  storageType: 'elasticsearch' | 'qdrant';
  url: string;
  username: string;
  password: string;
  apiKey: string;
  indexMode: IndexModeType;
  fixedName: string;
  rollingStep: string;
  prefix: string;
  enabledRetrievalMethods: RetrievalMethodType[];
}

const defaultFormData: RetrieverFormData = {
  name: '',
  displayName: '',
  namespace: 'default',
  storageType: 'elasticsearch',
  url: '',
  username: '',
  password: '',
  apiKey: '',
  indexMode: 'per_user',
  fixedName: '',
  rollingStep: '5000',
  prefix: 'wegent',
  enabledRetrievalMethods: ['vector', 'keyword', 'hybrid'],
};

const PublicRetrieverList: React.FC = () => {
  const { t } = useTranslation(['admin', 'common', 'wizard']);
  const { toast } = useToast();
  const [retrievers, setRetrievers] = useState<AdminPublicRetriever[]>([]);
  const [_total, setTotal] = useState(0);
  const [page, _setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedRetriever, setSelectedRetriever] = useState<AdminPublicRetriever | null>(null);

  // Form states
  const [formData, setFormData] = useState<RetrieverFormData>(defaultFormData);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  // Retrieval methods state
  const [availableRetrievalMethods, setAvailableRetrievalMethods] = useState<RetrievalMethodType[]>([
    ...STORAGE_TYPE_CONFIG.elasticsearch.fallbackRetrievalMethods,
  ]);
  const [loadingRetrievalMethods, setLoadingRetrievalMethods] = useState(false);

  const fetchRetrievers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await adminApis.getPublicRetrievers(page, 100);
      setRetrievers(response.items);
      setTotal(response.total);
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: t('admin:public_retrievers.errors.load_failed'),
      });
    } finally {
      setLoading(false);
    }
  }, [page, toast, t]);

  useEffect(() => {
    fetchRetrievers();
  }, [fetchRetrievers]);

  // Fetch retrieval methods for a storage type from API
  const fetchRetrievalMethods = useCallback(
    async (type: 'elasticsearch' | 'qdrant') => {
      setLoadingRetrievalMethods(true);
      try {
        const response = await retrieverApis.getStorageTypeRetrievalMethods(type);
        const methods = response.retrieval_methods as RetrievalMethodType[];
        setAvailableRetrievalMethods(methods);
        return methods;
      } catch (error) {
        console.error('Failed to fetch retrieval methods:', error);
        const fallback = [...STORAGE_TYPE_CONFIG[type].fallbackRetrievalMethods];
        setAvailableRetrievalMethods(fallback);
        return fallback;
      } finally {
        setLoadingRetrievalMethods(false);
      }
    },
    []
  );

  // Handle retrieval method toggle
  const handleRetrievalMethodToggle = useCallback(
    (method: RetrievalMethodType, checked: boolean) => {
      setFormData(prev => {
        const currentMethods = prev.enabledRetrievalMethods;
        if (checked) {
          return {
            ...prev,
            enabledRetrievalMethods: currentMethods.includes(method)
              ? currentMethods
              : [...currentMethods, method],
          };
        } else {
          const newMethods = currentMethods.filter(m => m !== method);
          return {
            ...prev,
            enabledRetrievalMethods: newMethods.length > 0 ? newMethods : currentMethods,
          };
        }
      });
    },
    []
  );

  const formToRetrieverCRD = (data: RetrieverFormData): RetrieverCRD => {
    // Build retrieval methods config
    const retrievalMethodsConfig: RetrieverCRD['spec']['retrievalMethods'] = {
      vector: {
        enabled: data.enabledRetrievalMethods.includes('vector'),
        defaultWeight: 0.7,
      },
      keyword: {
        enabled: data.enabledRetrievalMethods.includes('keyword'),
        defaultWeight: 0.3,
      },
      hybrid: {
        enabled: data.enabledRetrievalMethods.includes('hybrid'),
      },
    };

    return {
      apiVersion: 'agent.wecode.io/v1',
      kind: 'Retriever',
      metadata: {
        name: data.name,
        namespace: data.namespace,
        displayName: data.displayName || undefined,
      },
      spec: {
        storageConfig: {
          type: data.storageType,
          url: data.url,
          ...(data.username && { username: data.username }),
          ...(data.password && { password: data.password }),
          ...(data.apiKey && { apiKey: data.apiKey }),
          indexStrategy: {
            mode: data.indexMode,
            ...(data.indexMode === 'fixed' && { fixedName: data.fixedName }),
            ...(data.indexMode === 'rolling' && { rollingStep: parseInt(data.rollingStep) }),
            ...(data.prefix && { prefix: data.prefix }),
          },
        },
        retrievalMethods: retrievalMethodsConfig,
      },
    };
  };

  const retrieverToFormData = (retriever: AdminPublicRetriever): RetrieverFormData => {
    const json = retriever.json as RetrieverCRD;
    const spec = json?.spec || {};
    const storageConfig = spec?.storageConfig || {};
    const indexStrategy = storageConfig?.indexStrategy || {};

    // Parse enabled retrieval methods
    const enabledMethods: RetrievalMethodType[] = [];
    if (spec.retrievalMethods) {
      if (spec.retrievalMethods.vector?.enabled) enabledMethods.push('vector');
      if (spec.retrievalMethods.keyword?.enabled) enabledMethods.push('keyword');
      if (spec.retrievalMethods.hybrid?.enabled) enabledMethods.push('hybrid');
    }
    if (enabledMethods.length === 0) {
      enabledMethods.push('vector');
    }

    return {
      name: retriever.name,
      displayName: retriever.displayName || '',
      namespace: retriever.namespace,
      storageType: (storageConfig.type as 'elasticsearch' | 'qdrant') || 'elasticsearch',
      url: storageConfig.url || '',
      username: storageConfig.username || '',
      password: (storageConfig as { password?: string }).password || '',
      apiKey: storageConfig.apiKey || '',
      indexMode: (indexStrategy.mode as IndexModeType) || 'per_user',
      fixedName: indexStrategy.fixedName || '',
      rollingStep: String(indexStrategy.rollingStep || 5000),
      prefix: indexStrategy.prefix || 'wegent',
      enabledRetrievalMethods: enabledMethods,
    };
  };

  const handleStorageTypeChange = async (value: 'elasticsearch' | 'qdrant') => {
    const config = STORAGE_TYPE_CONFIG[value];
    const availableMethods = await fetchRetrievalMethods(value);

    setFormData(prev => ({
      ...prev,
      storageType: value,
      url: config.defaultUrl,
      indexMode: config.recommendedIndexMode,
      enabledRetrievalMethods: [...availableMethods],
    }));
  };

  const handleTestConnection = async () => {
    if (!formData.url) {
      toast({
        variant: 'destructive',
        title: t('common:retrievers.url_required'),
      });
      return;
    }

    setTesting(true);
    try {
      const result = await retrieverApis.testConnection({
        storage_type: formData.storageType,
        url: formData.url,
        username: formData.username || undefined,
        password: formData.password || undefined,
        api_key: formData.apiKey || undefined,
      });

      if (result.success) {
        toast({
          title: t('common:retrievers.test_success'),
          description: result.message,
        });
      } else {
        toast({
          variant: 'destructive',
          title: t('common:retrievers.test_failed'),
          description: result.message,
        });
      }
    } catch (error) {
      toast({
        variant: 'destructive',
        title: t('common:retrievers.test_failed'),
        description: (error as Error).message,
      });
    } finally {
      setTesting(false);
    }
  };

  const validateForm = (): boolean => {
    if (!formData.name.trim()) {
      toast({
        variant: 'destructive',
        title: t('admin:public_retrievers.errors.name_required'),
      });
      return false;
    }

    const nameRegex = /^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$/;
    if (!nameRegex.test(formData.name)) {
      toast({
        variant: 'destructive',
        title: t('common:retrievers.name_invalid'),
        description: t('common:retrievers.name_invalid_hint'),
      });
      return false;
    }

    if (!formData.url.trim()) {
      toast({
        variant: 'destructive',
        title: t('admin:public_retrievers.errors.url_required'),
      });
      return false;
    }

    if (formData.indexMode === 'fixed' && !formData.fixedName.trim()) {
      toast({
        variant: 'destructive',
        title: t('common:retrievers.fixed_index_name_empty'),
      });
      return false;
    }

    if (formData.indexMode === 'rolling') {
      const step = parseInt(formData.rollingStep);
      if (isNaN(step) || step <= 0) {
        toast({
          variant: 'destructive',
          title: t('common:retrievers.rolling_step_invalid'),
        });
        return false;
      }
      if (!formData.prefix.trim()) {
        toast({
          variant: 'destructive',
          title: t('common:retrievers.rolling_prefix_required'),
        });
        return false;
      }
    }

    if (
      (formData.indexMode === 'per_dataset' || formData.indexMode === 'per_user') &&
      !formData.prefix.trim()
    ) {
      toast({
        variant: 'destructive',
        title: t('common:retrievers.per_dataset_prefix_required'),
      });
      return false;
    }

    return true;
  };

  const handleCreateRetriever = async () => {
    if (!validateForm()) return;

    setSaving(true);
    try {
      const retrieverData = formToRetrieverCRD(formData);
      await adminApis.createPublicRetriever(retrieverData);
      toast({ title: t('admin:public_retrievers.success.created') });
      setIsCreateDialogOpen(false);
      resetForm();
      fetchRetrievers();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: t('admin:public_retrievers.errors.create_failed'),
        description: (error as Error).message,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateRetriever = async () => {
    if (!selectedRetriever) return;
    if (!validateForm()) return;

    setSaving(true);
    try {
      const retrieverData = formToRetrieverCRD(formData);
      await adminApis.updatePublicRetriever(selectedRetriever.id, retrieverData);
      toast({ title: t('admin:public_retrievers.success.updated') });
      setIsEditDialogOpen(false);
      resetForm();
      fetchRetrievers();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: t('admin:public_retrievers.errors.update_failed'),
        description: (error as Error).message,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteRetriever = async () => {
    if (!selectedRetriever) return;

    setSaving(true);
    try {
      await adminApis.deletePublicRetriever(selectedRetriever.id);
      toast({ title: t('admin:public_retrievers.success.deleted') });
      setIsDeleteDialogOpen(false);
      setSelectedRetriever(null);
      fetchRetrievers();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: t('admin:public_retrievers.errors.delete_failed'),
        description: (error as Error).message,
      });
    } finally {
      setSaving(false);
    }
  };

  const resetForm = () => {
    setFormData(defaultFormData);
    setSelectedRetriever(null);
    setShowPassword(false);
    setShowApiKey(false);
  };

  const openCreateDialog = async () => {
    resetForm();
    const methods = await fetchRetrievalMethods('elasticsearch');
    setFormData(prev => ({
      ...prev,
      enabledRetrievalMethods: [...methods],
    }));
    setIsCreateDialogOpen(true);
  };

  const openEditDialog = async (retriever: AdminPublicRetriever) => {
    setSelectedRetriever(retriever);
    const formDataFromRetriever = retrieverToFormData(retriever);
    setFormData(formDataFromRetriever);
    await fetchRetrievalMethods(formDataFromRetriever.storageType);
    setIsEditDialogOpen(true);
  };

  const getDisplayName = (retriever: AdminPublicRetriever): string => {
    return retriever.displayName || retriever.name;
  };

  const getStorageTypeLabel = (storageType: string): string => {
    if (storageType === 'elasticsearch') return 'Elasticsearch';
    if (storageType === 'qdrant') return 'Qdrant';
    return storageType;
  };

  const RetrieverFormFields = () => (
    <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
      {/* Retriever Name and Display Name */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name" className="text-sm font-medium">
            {t('admin:public_retrievers.form.name')} *
          </Label>
          <Input
            id="name"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            placeholder={t('admin:public_retrievers.form.name_placeholder')}
            disabled={isEditDialogOpen}
            className="bg-base"
          />
          <p className="text-xs text-text-muted">
            {isEditDialogOpen
              ? t('common:retrievers.retriever_id_readonly')
              : t('common:retrievers.retriever_id_hint')}
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="displayName" className="text-sm font-medium">
            {t('admin:public_retrievers.form.display_name')}
          </Label>
          <Input
            id="displayName"
            value={formData.displayName}
            onChange={e => setFormData({ ...formData, displayName: e.target.value })}
            placeholder={t('admin:public_retrievers.form.display_name_placeholder')}
            className="bg-base"
          />
        </div>
      </div>

      {/* Storage Type */}
      <div className="space-y-2">
        <Label htmlFor="storageType" className="text-sm font-medium">
          {t('admin:public_retrievers.form.storage_type')} *
        </Label>
        <Select value={formData.storageType} onValueChange={handleStorageTypeChange}>
          <SelectTrigger className="bg-base">
            <SelectValue placeholder={t('admin:public_retrievers.form.storage_type_placeholder')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="elasticsearch">Elasticsearch</SelectItem>
            <SelectItem value="qdrant">Qdrant</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* URL */}
      <div className="space-y-2">
        <Label htmlFor="url" className="text-sm font-medium">
          {t('admin:public_retrievers.form.url')} *
        </Label>
        <Input
          id="url"
          value={formData.url}
          onChange={e => setFormData({ ...formData, url: e.target.value })}
          placeholder={t('admin:public_retrievers.form.url_placeholder')}
          className="bg-base"
        />
        <p className="text-xs text-text-muted">
          {formData.storageType === 'elasticsearch'
            ? t('common:retrievers.connection_url_hint_es')
            : t('common:retrievers.connection_url_hint_qdrant')}
        </p>
      </div>

      {/* Authentication - Username/Password (Elasticsearch) */}
      {STORAGE_TYPE_CONFIG[formData.storageType].authFields.supportsUsernamePassword && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="username" className="text-sm font-medium">
              {t('admin:public_retrievers.form.username')}
            </Label>
            <Input
              id="username"
              value={formData.username}
              onChange={e => setFormData({ ...formData, username: e.target.value })}
              placeholder={t('admin:public_retrievers.form.username_placeholder')}
              className="bg-base"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-medium">
              {t('common:retrievers.password')}
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={e => setFormData({ ...formData, password: e.target.value })}
                placeholder={t('common:retrievers.password_placeholder')}
                className="bg-base pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="w-4 h-4" />
                ) : (
                  <EyeIcon className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Authentication - API Key (Qdrant) */}
      {STORAGE_TYPE_CONFIG[formData.storageType].authFields.supportsApiKey && (
        <div className="space-y-2">
          <Label htmlFor="apiKey" className="text-sm font-medium">
            {t('admin:public_retrievers.form.api_key')}
          </Label>
          <div className="relative">
            <Input
              id="apiKey"
              type={showApiKey ? 'text' : 'password'}
              value={formData.apiKey}
              onChange={e => setFormData({ ...formData, apiKey: e.target.value })}
              placeholder={t('admin:public_retrievers.form.api_key_placeholder')}
              className="bg-base pr-10"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7"
              onClick={() => setShowApiKey(!showApiKey)}
            >
              {showApiKey ? (
                <EyeSlashIcon className="w-4 h-4" />
              ) : (
                <EyeIcon className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Index Strategy */}
      <div className="space-y-2">
        <Label htmlFor="indexMode" className="text-sm font-medium">
          {t('admin:public_retrievers.form.index_strategy')} *
        </Label>
        <Select
          value={formData.indexMode}
          onValueChange={(value: string) =>
            setFormData({ ...formData, indexMode: value as IndexModeType })
          }
        >
          <SelectTrigger className="bg-base">
            <SelectValue placeholder={t('admin:public_retrievers.form.index_strategy_placeholder')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="per_user">
              {t('common:retrievers.index_strategy_per_user')}
              {STORAGE_TYPE_CONFIG[formData.storageType].recommendedIndexMode === 'per_user' &&
                ` (${t('wizard:recommended')})`}
            </SelectItem>
            <SelectItem value="per_dataset">
              {t('common:retrievers.index_strategy_per_dataset')}
              {STORAGE_TYPE_CONFIG[formData.storageType].recommendedIndexMode === 'per_dataset' &&
                ` (${t('wizard:recommended')})`}
            </SelectItem>
            <SelectItem value="fixed">{t('common:retrievers.index_strategy_fixed')}</SelectItem>
            <SelectItem value="rolling">{t('common:retrievers.index_strategy_rolling')}</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-text-muted">
          {formData.indexMode === 'per_user' && t('common:retrievers.index_strategy_per_user_desc')}
          {formData.indexMode === 'per_dataset' &&
            t('common:retrievers.index_strategy_per_dataset_desc')}
          {formData.indexMode === 'fixed' && t('common:retrievers.index_strategy_fixed_desc')}
          {formData.indexMode === 'rolling' && t('common:retrievers.index_strategy_rolling_desc')}
        </p>
      </div>

      {/* Index Strategy Fields */}
      {formData.indexMode === 'fixed' && (
        <div className="space-y-2">
          <Label htmlFor="fixedName" className="text-sm font-medium">
            {t('admin:public_retrievers.form.fixed_name')} *
          </Label>
          <Input
            id="fixedName"
            value={formData.fixedName}
            onChange={e => setFormData({ ...formData, fixedName: e.target.value })}
            placeholder={t('admin:public_retrievers.form.fixed_name_placeholder')}
            className="bg-base"
          />
        </div>
      )}

      {formData.indexMode === 'rolling' && (
        <div className="space-y-2">
          <Label htmlFor="rollingStep" className="text-sm font-medium">
            {t('common:retrievers.rolling_step_required')}
          </Label>
          <Input
            id="rollingStep"
            type="number"
            value={formData.rollingStep}
            onChange={e => setFormData({ ...formData, rollingStep: e.target.value })}
            placeholder={t('common:retrievers.rolling_step_placeholder')}
            className="bg-base"
          />
          <p className="text-xs text-text-muted">{t('common:retrievers.rolling_step_hint')}</p>
        </div>
      )}

      {(formData.indexMode === 'rolling' ||
        formData.indexMode === 'per_dataset' ||
        formData.indexMode === 'per_user') && (
        <div className="space-y-2">
          <Label htmlFor="prefix" className="text-sm font-medium">
            {t('admin:public_retrievers.form.prefix')} *
          </Label>
          <Input
            id="prefix"
            value={formData.prefix}
            onChange={e => setFormData({ ...formData, prefix: e.target.value })}
            placeholder={t('admin:public_retrievers.form.prefix_placeholder')}
            className="bg-base"
          />
          <p className="text-xs text-text-muted">{t('common:retrievers.index_prefix_hint')}</p>
        </div>
      )}

      {/* Retrieval Methods */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">{t('common:retrievers.retrieval_methods')}</Label>
        <div className="flex flex-wrap gap-4">
          {loadingRetrievalMethods ? (
            <div className="flex items-center gap-2 text-text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">{t('common:retrievers.loading_retrieval_methods')}</span>
            </div>
          ) : (
            availableRetrievalMethods.map(method => (
              <div key={method} className="flex items-center space-x-2">
                <Checkbox
                  id={`retrieval-method-${method}`}
                  checked={formData.enabledRetrievalMethods.includes(method)}
                  onCheckedChange={checked =>
                    handleRetrievalMethodToggle(method, checked as boolean)
                  }
                  disabled={
                    formData.enabledRetrievalMethods.length === 1 &&
                    formData.enabledRetrievalMethods.includes(method)
                  }
                />
                <Label
                  htmlFor={`retrieval-method-${method}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {t(RETRIEVAL_METHOD_LABELS[method] || method)}
                </Label>
              </div>
            ))
          )}
        </div>
        <p className="text-xs text-text-muted">{t('common:retrievers.retrieval_methods_hint')}</p>
      </div>
    </div>
  );

  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-text-primary mb-1">
          {t('admin:public_retrievers.title')}
        </h2>
        <p className="text-sm text-text-muted">{t('admin:public_retrievers.description')}</p>
      </div>

      {/* Content Container */}
      <div className="bg-base border border-border rounded-md p-2 w-full max-h-[70vh] flex flex-col overflow-y-auto">
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-text-muted" />
          </div>
        )}

        {/* Empty State */}
        {!loading && retrievers.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <CircleStackIcon className="w-12 h-12 text-text-muted mb-4" />
            <p className="text-text-muted">{t('admin:public_retrievers.no_retrievers')}</p>
          </div>
        )}

        {/* Retriever List */}
        {!loading && retrievers.length > 0 && (
          <div className="flex-1 overflow-y-auto space-y-3 p-1">
            {retrievers.map(retriever => (
              <Card
                key={retriever.id}
                className="p-4 bg-base hover:bg-hover transition-colors border-l-2 border-l-primary"
              >
                <div className="flex items-center justify-between min-w-0">
                  <div className="flex items-center space-x-3 min-w-0 flex-1">
                    <GlobeAltIcon className="w-5 h-5 text-primary flex-shrink-0" />
                    <div className="flex flex-col justify-center min-w-0 flex-1">
                      <div className="flex items-center space-x-2 min-w-0">
                        <h3 className="text-base font-medium text-text-primary truncate">
                          {getDisplayName(retriever)}
                        </h3>
                        <Tag variant="info">{getStorageTypeLabel(retriever.storageType)}</Tag>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-text-muted">
                        <span>
                          {t('admin:public_retrievers.form.name')}: {retriever.name}
                        </span>
                        {retriever.description && (
                          <>
                            <span>•</span>
                            <span className="truncate max-w-[300px]">{retriever.description}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0 ml-3">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => openEditDialog(retriever)}
                      title={t('admin:public_retrievers.edit_retriever')}
                    >
                      <PencilIcon className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 hover:text-error"
                      onClick={() => {
                        setSelectedRetriever(retriever);
                        setIsDeleteDialogOpen(true);
                      }}
                      title={t('admin:public_retrievers.delete_retriever')}
                    >
                      <TrashIcon className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Add Button */}
        {!loading && (
          <div className="border-t border-border pt-3 mt-3 bg-base">
            <div className="flex justify-center">
              <UnifiedAddButton onClick={openCreateDialog}>
                {t('admin:public_retrievers.create_retriever')}
              </UnifiedAddButton>
            </div>
          </div>
        )}
      </div>

      {/* Create Retriever Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t('admin:public_retrievers.create_retriever')}</DialogTitle>
            <DialogDescription>{t('admin:public_retrievers.description')}</DialogDescription>
          </DialogHeader>
          <RetrieverFormFields />
          <DialogFooter className="flex items-center justify-between sm:justify-between">
            <Button
              variant="outline"
              onClick={handleTestConnection}
              disabled={testing || !formData.url}
            >
              {testing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <BeakerIcon className="w-4 h-4 mr-1" />
              {t('common:retrievers.test_connection')}
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                {t('admin:common.cancel')}
              </Button>
              <Button onClick={handleCreateRetriever} disabled={saving}>
                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {t('admin:common.create')}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Retriever Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t('admin:public_retrievers.edit_retriever')}</DialogTitle>
          </DialogHeader>
          <RetrieverFormFields />
          <DialogFooter className="flex items-center justify-between sm:justify-between">
            <Button
              variant="outline"
              onClick={handleTestConnection}
              disabled={testing || !formData.url}
            >
              {testing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <BeakerIcon className="w-4 h-4 mr-1" />
              {t('common:retrievers.test_connection')}
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                {t('admin:common.cancel')}
              </Button>
              <Button onClick={handleUpdateRetriever} disabled={saving}>
                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {t('admin:common.save')}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('admin:public_retrievers.confirm.delete_title')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('admin:public_retrievers.confirm.delete_message', {
                name: selectedRetriever?.name,
              })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('admin:common.cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteRetriever}
              className="bg-error hover:bg-error/90"
            >
              {t('admin:common.delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default PublicRetrieverList;
