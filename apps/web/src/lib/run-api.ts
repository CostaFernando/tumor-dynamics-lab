import { createApiClient } from '@tdl/api-client';
export const runApi = () => createApiClient(new URL('/api', window.location.href).href);
export function apiError(error: unknown): string {
  if (typeof error === 'object' && error && 'detail' in error) {
    const detail = (error as {detail: unknown}).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map(value=>typeof value?.msg==='string'?value.msg:'Invalid request').join('; ');
  }
  return 'The local API could not complete this request. Check the API and research storage.';
}
