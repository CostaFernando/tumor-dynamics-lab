'use client';
import { useState } from 'react';
import type { RunRecord } from '@tdl/api-client';
import { runApi, apiError } from '@/lib/run-api';
import { lifecycleActionSchema, runRecordSchema } from '@/lib/validation';
import { Button } from './ui/button';

export function RunActions({run,onChanged}:{run:RunRecord;onChanged:(run:RunRecord)=>void}) {
  const [pending,setPending]=useState(false);
  const [error,setError]=useState('');
  const canCancel=run.status==='queued'||run.status==='running';
  const canRetry=run.status==='failed'||run.status==='cancelled';
  async function act(action:'cancel'|'retry') {
    setPending(true);setError('');
    try {
      const {run_id}=lifecycleActionSchema.parse({run_id:run.id});
      const response=action==='cancel'
        ?await runApi().POST('/runs/{run_id}/cancel',{params:{path:{run_id}}})
        :await runApi().POST('/runs/{run_id}/retry',{params:{path:{run_id}}});
      if(response.error)throw new Error(apiError(response.error));
      onChanged(runRecordSchema.parse(response.data));
    } catch(value) {setError(value instanceof Error?value.message:'Could not update this attempt.');}
    finally {setPending(false);}
  }
  return <div className="stack">{canCancel&&<Button variant="outline" disabled={pending} onClick={()=>act('cancel')}>Cancel attempt</Button>}{canRetry&&<><p className="muted small">Retry preserves this attempt and creates a new run with the same recorded input and configuration.</p><Button disabled={pending} onClick={()=>act('retry')}>Retry as new attempt</Button></>}{error&&<p role="alert">{error}</p>}</div>;
}
