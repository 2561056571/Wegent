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
import { Textarea } from '@/components/ui/textarea';
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
import {
  adminApis,
  AdminPublicRetriever,
  RetrieverCRD,
} from '@/apis/admin';
import UnifiedAddButton from '@/components/common/UnifiedAddButton';

interface RetrieverFormData {
  name: string;
  displayName: string;
  namespace: string;
  storageType: 'elasticsearch' | 'qdrant';
  url: string;
  username: string;
  apiKey: string;
  indexMode: 'fixed' | 'per_user';
  fixedName: string;
  prefix: string;
  description: string;
}

const defaultFormData: RetrieverFormData = {
  name: '',
  displayName: '',
  namespace: 'default',
  storageType: 'elasticsearch',
  url: '',
  username: '',
  apiKey: '',
  indexMode: 'per_user',
  fixedName: '',
  prefix: 'kb_',
  description: '',
};

const PublicRetrieverList: React.FC = () => {
  const { t } = useTranslation('admin');
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

  const fetchRetrievers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await adminApis.getPublicRetrievers(page, 100);
      setRetrievers(response.items);
      setTotal(response.total);
    } catch (_error) {
      toast({
        variant: 'destructive',
        title: t('public_retrievers.errors.load_failed'),
      });
    } finally {
      setLoading(false);
    }
  }, [page, toast, t]);

  useEffect(() => {
    fetchRetrievers();
  }, [fetchRetrievers]);

  const formToRetrieverCRD = (data: RetrieverFormData): RetrieverCRD => {
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
          username: data.username || undefined,
          apiKey: data.apiKey || undefined,
          indexStrategy: {
            mode: data.indexMode,
            fixedName: data.indexMode === 'fixed' ? data.fixedName : undefined,
            prefix: data.indexMode === 'per_user' ? data.prefix : undefined,
          },
        },
        description: data.description || undefined,
      },
    };
  };

  const retrieverToFormData = (retriever: AdminPublicRetriever): RetrieverFormData => {
    const json = retriever.json as RetrieverCRD;
    const spec = json?.spec || {};
    const storageConfig = spec?.storageConfig || {};
    const indexStrategy = storageConfig?.indexStrategy || {};

    return {
      name: retriever.name,
      displayName: retriever.displayName || '',
      namespace: retriever.namespace,
      storageType: (storageConfig.type as 'elasticsearch' | 'qdrant') || 'elasticsearch',
      url: storageConfig.url || '',
      username: storageConfig.username || '',
      apiKey: storageConfig.apiKey || '',
      indexMode: (indexStrategy.mode as 'fixed' | 'per_user') || 'per_user',
      fixedName: indexStrategy.fixedName || '',
      prefix: indexStrategy.prefix || 'kb_',
      description: spec.description || '',
    };
  };

  const handleCreateRetriever = async () => {
    if (!formData.name.trim()) {
      toast({
        variant: 'destructive',
        title: t('public_retrievers.errors.name_required'),
      });
      return;
    }

    if (!formData.url.trim()) {
      toast({
        variant: 'destructive',
        title: t('public_retrievers.errors.url_required'),
      });
      return;
    }

    setSaving(true);
    try {
      const retrieverData = formToRetrieverCRD(formData);
      await adminApis.createPublicRetriever(retrieverData);
      toast({ title: t('public_retrievers.success.created') });
      setIsCreateDialogOpen(false);
      resetForm();
      fetchRetrievers();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: t('public_retrievers.errors.create_failed'),
        description: (error as Error).message,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateRetriever = async () => {
    if (!selectedRetriever) return;

    if (!formData.url.trim()) {
      toast({
        variant: 'destructive',
        title: t('public_retrievers.errors.url_required'),
      });
      return;
    }

    setSaving(true);
    try {
      const retrieverData = formToRetrieverCRD(formData);
      await adminApis.updatePublicRetriever(selectedRetriever.id, retrieverData);
      toast({ title: t('public_retrievers.success.updated') });
      setIsEditDialogOpen(false);
      resetForm();
      fetchRetrievers();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: t('public_retrievers.errors.update_failed'),
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
      toast({ title: t('public_retrievers.success.deleted') });
      setIsDeleteDialogOpen(false);
      setSelectedRetriever(null);
      fetchRetrievers();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: t('public_retrievers.errors.delete_failed'),
        description: (error as Error).message,
      });
    } finally {
      setSaving(false);
    }
  };

  const resetForm = () => {
    setFormData(defaultFormData);
    setSelectedRetriever(null);
  };

  const openEditDialog = (retriever: AdminPublicRetriever) => {
    setSelectedRetriever(retriever);
    setFormData(retrieverToFormData(retriever));
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
    <div className="space-y-4 py-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">{t('public_retrievers.form.name')} *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            placeholder={t('public_retrievers.form.name_placeholder')}
            disabled={isEditDialogOpen}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="displayName">{t('public_retrievers.form.display_name')}</Label>
          <Input
            id="displayName"
            value={formData.displayName}
            onChange={e => setFormData({ ...formData, displayName: e.target.value })}
            placeholder={t('public_retrievers.form.display_name_placeholder')}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="storageType">{t('public_retrievers.form.storage_type')} *</Label>
        <Select
          value={formData.storageType}
          onValueChange={(value: 'elasticsearch' | 'qdrant') =>
            setFormData({ ...formData, storageType: value })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder={t('public_retrievers.form.storage_type_placeholder')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="elasticsearch">Elasticsearch</SelectItem>
            <SelectItem value="qdrant">Qdrant</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="url">{t('public_retrievers.form.url')} *</Label>
        <Input
          id="url"
          value={formData.url}
          onChange={e => setFormData({ ...formData, url: e.target.value })}
          placeholder={t('public_retrievers.form.url_placeholder')}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="username">{t('public_retrievers.form.username')}</Label>
          <Input
            id="username"
            value={formData.username}
            onChange={e => setFormData({ ...formData, username: e.target.value })}
            placeholder={t('public_retrievers.form.username_placeholder')}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="apiKey">{t('public_retrievers.form.api_key')}</Label>
          <Input
            id="apiKey"
            type="password"
            value={formData.apiKey}
            onChange={e => setFormData({ ...formData, apiKey: e.target.value })}
            placeholder={t('public_retrievers.form.api_key_placeholder')}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="indexMode">{t('public_retrievers.form.index_strategy')}</Label>
        <Select
          value={formData.indexMode}
          onValueChange={(value: 'fixed' | 'per_user') =>
            setFormData({ ...formData, indexMode: value })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder={t('public_retrievers.form.index_strategy_placeholder')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="per_user">{t('public_retrievers.form.per_user')}</SelectItem>
            <SelectItem value="fixed">{t('public_retrievers.form.fixed')}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {formData.indexMode === 'fixed' && (
        <div className="space-y-2">
          <Label htmlFor="fixedName">{t('public_retrievers.form.fixed_name')}</Label>
          <Input
            id="fixedName"
            value={formData.fixedName}
            onChange={e => setFormData({ ...formData, fixedName: e.target.value })}
            placeholder={t('public_retrievers.form.fixed_name_placeholder')}
          />
        </div>
      )}

      {formData.indexMode === 'per_user' && (
        <div className="space-y-2">
          <Label htmlFor="prefix">{t('public_retrievers.form.prefix')}</Label>
          <Input
            id="prefix"
            value={formData.prefix}
            onChange={e => setFormData({ ...formData, prefix: e.target.value })}
            placeholder={t('public_retrievers.form.prefix_placeholder')}
          />
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="description">{t('public_retrievers.form.description')}</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={e => setFormData({ ...formData, description: e.target.value })}
          placeholder={t('public_retrievers.form.description_placeholder')}
          className="min-h-[80px]"
        />
      </div>
    </div>
  );

  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-text-primary mb-1">
          {t('public_retrievers.title')}
        </h2>
        <p className="text-sm text-text-muted">{t('public_retrievers.description')}</p>
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
            <p className="text-text-muted">{t('public_retrievers.no_retrievers')}</p>
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
                          {t('public_retrievers.form.name')}: {retriever.name}
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
                      title={t('public_retrievers.edit_retriever')}
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
                      title={t('public_retrievers.delete_retriever')}
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
              <UnifiedAddButton onClick={() => setIsCreateDialogOpen(true)}>
                {t('public_retrievers.create_retriever')}
              </UnifiedAddButton>
            </div>
          </div>
        )}
      </div>

      {/* Create Retriever Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t('public_retrievers.create_retriever')}</DialogTitle>
            <DialogDescription>{t('public_retrievers.description')}</DialogDescription>
          </DialogHeader>
          <RetrieverFormFields />
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleCreateRetriever} disabled={saving}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t('common.create')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Retriever Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t('public_retrievers.edit_retriever')}</DialogTitle>
          </DialogHeader>
          <RetrieverFormFields />
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleUpdateRetriever} disabled={saving}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t('common.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('public_retrievers.confirm.delete_title')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('public_retrievers.confirm.delete_message', { name: selectedRetriever?.name })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteRetriever} className="bg-error hover:bg-error/90">
              {t('common.delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default PublicRetrieverList;
