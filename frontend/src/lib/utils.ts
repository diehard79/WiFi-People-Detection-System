import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format timestamp to human-readable string
 */
export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * Format confidence score to percentage
 */
export function formatConfidence(confidence: number): string {
  return `${(confidence * 100).toFixed(1)}%`
}

/**
 * Get color based on count
 */
export function getCountColor(count: number): string {
  if (count === 0) return 'text-gray-400'
  if (count <= 3) return 'text-green-600'
  if (count <= 6) return 'text-yellow-600'
  return 'text-red-600'
}

/**
 * Get background color class based on count
 */
export function getCountBgColor(count: number): string {
  if (count === 0) return 'bg-gray-400'
  if (count <= 3) return 'bg-green-500'
  if (count <= 6) return 'bg-yellow-500'
  return 'bg-red-500'
}

/**
 * Validate detection data
 */
export function isValidDetection(data: any): boolean {
  return (
    data &&
    typeof data.timestamp === 'string' &&
    typeof data.presence === 'boolean' &&
    typeof data.presence_confidence === 'number' &&
    typeof data.count === 'number' &&
    typeof data.count_confidence === 'number' &&
    typeof data.scenario === 'string' &&
    typeof data.features === 'object'
  )
}
