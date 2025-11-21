/**
 * API URL configuration and helper functions
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

/**
 * Get the full API URL for a given endpoint (synchronous)
 * @param endpoint - The API endpoint path (e.g., '/api/status')
 * @returns The full API URL
 */
export function getApiUrlSync(endpoint: string): string {
  // Remove leading slash if present to avoid double slashes
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  return `${API_BASE_URL}/${normalizedEndpoint}`
}

/**
 * Get the base API URL
 * @returns The base API URL
 */
export function getApiBaseUrl(): string {
  return API_BASE_URL
}


