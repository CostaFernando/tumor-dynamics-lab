import { describe, expect, it } from 'vitest';
import { contextSchema, snapshotsSchema } from './validation';

describe('inspection input boundaries', () => {
  it('rejects invalid query state and malformed API payloads', () => {
    expect(contextSchema.safeParse({snapshot:'../escape'}).success).toBe(false);
    expect(contextSchema.parse({sample:'day-7'}).sample).toBe('day-7');
    expect(snapshotsSchema.safeParse([{id:'x',experiment:{}}]).success).toBe(false);
  });
});
