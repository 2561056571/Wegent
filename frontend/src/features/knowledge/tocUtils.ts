// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

import type { ReactNode, ReactElement } from 'react'
import type { WikiContent, WikiTocItem } from '@/types/wiki'

/**
 * Get TOC from WikiContent, only using backend-provided ext.toc.
 * No frontend parsing fallback - if TOC is not provided by backend, returns empty array.
 * This ensures TOC IDs are consistent with the rendered heading IDs.
 * @param content - WikiContent object
 * @returns Array of TOC items from backend, or empty array if not available
 */
export function getTocFromContent(content: WikiContent | null): WikiTocItem[] {
  if (!content) return []

  // Only use backend-provided TOC, no fallback parsing
  if (content.ext?.toc && Array.isArray(content.ext.toc) && content.ext.toc.length > 0) {
    return content.ext.toc
  }

  // Return empty array if no TOC data from backend
  // This prevents ID mismatch issues between TOC and rendered headings
  return []
}

/**
 * Get only H2 level items from TOC (for left sidebar secondary navigation).
 * @param toc - Full TOC items array
 * @returns Array of H2 level TOC items only
 */
export function getH2TocItems(toc: WikiTocItem[]): WikiTocItem[] {
  return toc.filter((item) => item.level === 2)
}

/**
 * Extract text content from React children (for heading ID generation).
 * @param children - React children
 * @returns Plain text string
 */
export function getTextContent(children: ReactNode): string {
  if (typeof children === 'string') {
    return children
  }

  if (Array.isArray(children)) {
    return children.map(getTextContent).join('')
  }

  if (children && typeof children === 'object' && 'props' in children) {
    const element = children as ReactElement<{ children?: ReactNode }>
    return getTextContent(element.props.children)
  }

  return ''
}
