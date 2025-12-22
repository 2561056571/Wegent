// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from 'react';
import { retrieverApis, type UnifiedRetriever } from '@/apis/retrievers';

export function useRetrievers(scope?: 'personal' | 'group' | 'all', groupName?: string) {
  const [retrievers, setRetrievers] = useState<UnifiedRetriever[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchRetrievers = async () => {
      try {
        setLoading(true);
        const response = await retrieverApis.getUnifiedRetrievers(scope, groupName);
        setRetrievers(response.data || []);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchRetrievers();
  }, [scope, groupName]);

  return { retrievers, loading, error };
}
