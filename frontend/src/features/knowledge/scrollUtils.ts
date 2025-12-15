// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

/**
 * Smooth scroll to a heading element by ID.
 * @param id - Target element ID
 * @param offset - Top offset in pixels (for fixed navigation)
 */
export function scrollToHeading(id: string, offset: number = 80): void {
  const element = document.getElementById(id)
  if (!element) return

  const elementPosition = element.getBoundingClientRect().top
  const offsetPosition = elementPosition + window.scrollY - offset

  window.scrollTo({
    top: offsetPosition,
    behavior: 'smooth',
  })
}

/**
 * Smooth scroll to a heading element within a container.
 * @param id - Target element ID
 * @param container - Scrollable container element
 * @param offset - Top offset in pixels
 */
export function scrollToHeadingInContainer(
  id: string,
  container: HTMLElement | null,
  offset: number = 80
): void {
  if (!container) {
    scrollToHeading(id, offset)
    return
  }

  const element = document.getElementById(id)
  if (!element) return

  const containerRect = container.getBoundingClientRect()
  const elementRect = element.getBoundingClientRect()

  const offsetPosition = elementRect.top - containerRect.top + container.scrollTop - offset

  container.scrollTo({
    top: offsetPosition,
    behavior: 'smooth',
  })
}
