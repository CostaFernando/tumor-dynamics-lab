import createClient from 'openapi-fetch';
import type { paths, components } from './schema';
export type { paths, components } from './schema';
export type Snapshot = components['schemas']['Snapshot'];
export type Observation = components['schemas']['Observation'];
export const createApiClient = (baseUrl = '/api') => createClient<paths>({baseUrl});
