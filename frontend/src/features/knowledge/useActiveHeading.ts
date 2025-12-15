// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client'

import { useEffect, useState, RefObject, useCallback } from 'react'

/**
 * Hook to track the currently visible heading using Intersection Observer.
 * @param headingIds - Array of heading IDs to track
 * @param containerRef - Reference to the scrollable container
 * @param options - Observer options
 * @returns Currently active heading ID
 */
export function useActiveHeading(
  headingIds: string[],
  containerRef: RefObject<HTMLElement | null>,
  options: { rootMargin?: string; threshold?: number } = {}
): string | null {
  const [activeId, setActiveId] = useState<string | null>(null)

  const { rootMargin = '-80px 0px -80% 0px', threshold = 0 } = options

  const handleIntersection = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      // Find the first visible heading from top
      const visibleEntries = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => {
          // Sort by top position
          const aTop = a.boundingClientRect.top
          const bTop = b.boundingClientRect.top
          return aTop - bTop
        })

      if (visibleEntries.length > 0) {
        setActiveId(visibleEntries[0].target.id)
      }
    },
    []
  )

  useEffect(() => {
    if (headingIds.length === 0) return

    const observer = new IntersectionObserver(handleIntersection, {
      root: containerRef.current,
      rootMargin,
      threshold,
    })

    // Observe all heading elements
    headingIds.forEach((id) => {
      const element = document.getElementById(id)
      if (element) {
        observer.observe(element)
      }
    })

    return () => {
      observer.disconnect()
    }
  }, [headingIds, containerRef, rootMargin, threshold, handleIntersection])

  // Set initial active heading
  useEffect(() => {
    if (headingIds.length > 0 && !activeId) {
      setActiveId(headingIds[0])
    }
  }, [headingIds, activeId])

  return activeId
}
