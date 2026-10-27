import { z } from 'zod';
import type { Snapshot } from '@tdl/api-client';

const identifier = z.string().min(1).max(200);
const treatment = z.object({name:identifier,start:z.number().finite(),end:z.number().finite(),dose:z.string().nullable().optional()});
const sample = z.object({id:identifier,culture_id:identifier,scope:identifier,time:z.number().finite(),counts:z.record(z.string(),z.number().int().nonnegative()),cell_state_summary:z.string().nullable().optional()});
// Compile-time agreement with the Python-generated contract; Zod validates runtime data.
export const snapshotSchema: z.ZodType<Snapshot> = z.object({
  id:z.string().regex(/^[a-f0-9]{64}$/),
  experiment:z.object({format_version:z.literal('1'),id:identifier,name:identifier,synthetic:z.boolean(),time_unit:z.enum(['hours','days']),description:z.string(),acquisition:z.string(),redistribution:z.string(),cultures:z.array(z.object({id:identifier,name:identifier,treatments:z.array(treatment).optional()})),samples:z.array(sample)}),
  observations:z.array(z.object({sample,total:z.number().int().positive(),proportions:z.record(z.string(),z.number().finite().min(0).max(1))})),
});
export const snapshotsSchema = z.array(snapshotSchema);
export const contextSchema = z.object({snapshot:z.string().regex(/^[a-f0-9]{64}$/).optional(),culture:identifier.optional(),scope:identifier.optional(),sample:identifier.optional()});
