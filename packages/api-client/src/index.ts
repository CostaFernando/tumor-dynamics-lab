import createClient from 'openapi-fetch';
import type { paths, components } from './schema';
export type { paths, components } from './schema';
export type Snapshot = components['schemas']['Snapshot'];
export type Observation = components['schemas']['Observation'];
export const createApiClient = (baseUrl = '/api') => createClient<paths>({baseUrl});
export type RunConfiguration = components['schemas']['RunConfiguration'];
export type RunRecord = components['schemas']['RunRecord'];
export type ForecastResult = components['schemas']['ForecastResult'];
export type Eligibility = components['schemas']['Eligibility'];

export type TargetEvaluation = components['schemas']['TargetEvaluation'];
export type CategoryComparison = components['schemas']['CategoryComparison'];
