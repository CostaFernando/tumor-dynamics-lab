import { describe, expect, it } from 'vitest';
import { contextSchema, snapshotsSchema } from './validation';

describe('inspection input boundaries', () => {
  it('rejects invalid query state and malformed API payloads', () => {
    expect(contextSchema.safeParse({snapshot:'../escape'}).success).toBe(false);
    expect(contextSchema.parse({sample:'day-7'}).sample).toBe('day-7');
    expect(snapshotsSchema.safeParse([{id:'x',experiment:{}}]).success).toBe(false);
  });
});

it('validates a forecast form without coercion and rejects empty or repeated targets', async () => {
  const { runConfigurationSchema } = await import('./validation');
  const request = {snapshot_id:'a'.repeat(64),culture_id:'culture-01',scope:'whole culture',cutoff:7,targets:[14],method:'last_observed'};
  expect(runConfigurationSchema.parse(request)).toEqual(request);
  expect(runConfigurationSchema.safeParse({...request,cutoff:'7'}).success).toBe(false);
  expect(runConfigurationSchema.safeParse({...request,targets:[]}).success).toBe(false);
  expect(runConfigurationSchema.safeParse({...request,targets:[14,14]}).success).toBe(false);
});
