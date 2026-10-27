'use client';
import { useState } from 'react';
import type { RunRecord } from '@tdl/api-client';
import { runApi, apiError } from '@/lib/run-api';
import { exportRequestSchema } from '@/lib/validation';
import { Button } from './ui/button';

export function ExportAction({run}:{run:RunRecord}) {
  const [pending,setPending]=useState(false);
  const [error,setError]=useState('');
  const reason=run.status!=='succeeded'||!run.result
    ?'Export requires a successful completed run. Wait for completion or retry a failed/cancelled attempt.'
    :!run.result.evaluations?.length||run.result.evaluations.length!==run.configuration.targets.length
      ?'This saved run has no complete recorded evaluation. Create a new forecast to export complete evidence.'
      :'';
  async function download() {
    setPending(true);setError('');
    try {
      const {run_id}=exportRequestSchema.parse({run_id:run.id});
      const response=await runApi().GET('/runs/{run_id}/export',{params:{path:{run_id}},parseAs:'blob'});
      if(response.error) {
        const detail=response.error instanceof Blob?JSON.parse(await response.error.text()):response.error;
        throw new Error(apiError(detail));
      }
      if(!response.data)throw new Error('No evidence bundle was returned. Try downloading this saved run again.');
      const url=URL.createObjectURL(response.data);
      const link=document.createElement('a');
      link.href=url;link.download=`evidence-${run_id}.zip`;
      document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
    } catch(value) {setError(value instanceof Error?value.message:'Could not download the saved evidence.');}
    finally {setPending(false);}
  }
  return <div className="stack"><Button variant="outline" disabled={pending||!!reason} onClick={download}>{pending?'Preparing download…':'Download evidence bundle'}</Button><p className="muted small">{reason||`Exports recorded evidence for run ${run.id}. The source dataset is not included.`}</p>{error&&<p role="alert">{error}</p>}</div>;
}
