// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

import type { ReactNode, ReactElement } from 'react'
import type { WikiContent, WikiTocItem } from '@/types/wiki'

/**
 * Generate a slug from heading text (must match backend implementation).
 * @param text - Heading text
 * @returns Slug string for anchor ID
 */
export function generateHeadingSlug(text: string): string {
  // Convert to lowercase and trim
  let slug = text.toLowerCase().trim()

  // Remove special characters except hyphens and alphanumerics
  slug = slug.replace(/[^\w\s-]/g, '')

  // Replace whitespace with hyphens
  slug = slug.replace(/[\s_]+/g, '-')

  // Remove consecutive hyphens
  slug = slug.replace(/-+/g, '-')

  // Remove leading/trailing hyphens
  slug = slug.replace(/^-+|-+$/g, '')

  return slug || 'heading'
}

/**
 * ID generator class to handle duplicate heading IDs consistently.
 * Used to ensure the same ID is generated for the same heading text
 * across TOC parsing and WikiContent rendering.
 */
export class HeadingIdGenerator {
  private existingIds: Set<string> = new Set()

  /**
   * Generate a unique ID for a heading text.
   * If the same text appears multiple times, it will get -1, -2, etc. suffix.
   */
  generateId(text: string): string {
    const baseId = generateHeadingSlug(text)
    let id = baseId
    let counter = 1

    while (this.existingIds.has(id)) {
      id = `${baseId}-${counter}`
      counter++
    }

    this.existingIds.add(id)
    return id
  }

  /**
   * Reset the generator state.
   */
  reset(): void {
    this.existingIds.clear()
  }
}

/**
 * Parse table of contents from Markdown content (frontend fallback).
 * Used when backend does not provide TOC data.
 * @param content - Markdown text content
 * @param maxLevel - Maximum heading level to parse (default 3)
 * @returns Array of TOC items
 */
export function parseTocFromMarkdown(content: string, maxLevel: number = 3): WikiTocItem[] {
  if (!content) return []

  const tocItems: WikiTocItem[] = []
  const idGenerator = new HeadingIdGenerator()

  // Match Markdown headings (## and ###)
  const headingRegex = /^(#{2,3})\s+(.+?)(?:\s*{#[\w-]+})?\s*$/gm
  let match

  while ((match = headingRegex.exec(content)) !== null) {
    const hashes = match[1]
    let text = match[2].trim()
    const level = hashes.length

    // Only include headings up to maxLevel
    if (level > maxLevel) continue

    // Clean up the heading text (remove inline formatting markers)
    text = text.replace(/\*\*(.+?)\*\*/g, '$1') // Remove bold
    text = text.replace(/\*(.+?)\*/g, '$1') // Remove italic
    text = text.replace(/`(.+?)`/g, '$1') // Remove inline code
    text = text.replace(/\[(.+?)\]\(.+?\)/g, '$1') // Remove links

    const id = idGenerator.generateId(text)
    tocItems.push({ id, text, level })
  }

  return tocItems
}

/**
 * Get TOC from WikiContent, using ext.toc if available, otherwise parse from content.
 * @param content - WikiContent object
 * @returns Array of TOC items
 */
export function getTocFromContent(content: WikiContent | null): WikiTocItem[] {
  if (!content) return []

  // Prefer backend-provided TOC
  if (content.ext?.toc && Array.isArray(content.ext.toc) && content.ext.toc.length > 0) {
    return content.ext.toc
  }

  // Fallback: parse from content
  return parseTocFromMarkdown(content.content)
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
