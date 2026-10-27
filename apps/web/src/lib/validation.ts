import { z } from 'zod';
import type { Snapshot, RunRecord, RunConfiguration, Eligibility } from '@tdl/api-client';

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

export const methodSchema = z.enum(['last_observed','damped_trend']);
export const runConfigurationSchema: z.ZodType<RunConfiguration> = z.object({
  snapshot_id:z.string().regex(/^[a-f0-9]{64}$/), culture_id:identifier, scope:identifier,
  cutoff:z.number().finite(), targets:z.array(z.number().finite()).min(1).refine(values=>new Set(values).size===values.length,'Choose each target once.'),
  method:methodSchema,
});
export const eligibilitySchema: z.ZodType<Eligibility> = z.object({available:z.boolean(),reason:z.string().nullable().optional()});
export const runRecordSchema: z.ZodType<RunRecord> = z.object({
  id:identifier,configuration:runConfigurationSchema,status:z.enum(['queued','running','succeeded','failed','cancelled']),
  created_at:z.string(),method_version:z.string(),software_version:z.string(),settings:z.record(z.string(),z.union([z.boolean(),z.number().finite(),z.string()])),
  deterministic:z.boolean(),crosses_withdrawal:z.boolean(),error:z.string().nullable().optional(),
  result:z.object({input_categories:z.array(z.string()),input_observations:z.array(sample),predictions:z.array(z.object({time:z.number().finite(),proportions:z.record(z.string(),z.number().finite().min(0).max(1))}))}).nullable().optional(),
});
export const runRecordsSchema = z.array(runRecordSchema);

export const lifecycleActionSchema = z.object({run_id:z.string().regex(/^[a-f0-9]{32}$/,'Choose a valid recorded run.')});
