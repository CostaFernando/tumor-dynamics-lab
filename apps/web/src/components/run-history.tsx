'use client';
import { useEffect, useState } from 'react';
import type { RunRecord } from '@tdl/api-client';
import { runApi, apiError } from '@/lib/run-api';
import { runRecordSchema, runRecordsSchema } from '@/lib/validation';
import { Button } from './ui/button';

export function useRunHistory() {
  const [runs,setRuns] = useState<RunRecord[]>([]);
  const [selectedId,setSelectedId] = useState<string | null>(null);
  const [error,setError] = useState('');
  useEffect(()=>{
    let active=true;
    async function refresh() {
      try {
        const {data,error} = await runApi().GET('/runs');
        if(error) throw new Error(apiError(error));
        const recorded = runRecordsSchema.parse(data);
        if(active){setRuns(recorded);setError('');}
      } catch(e) {if(active)setError(e instanceof Error?e.message:'Could not load saved runs.');}
    }
    void refresh();
    const timer=setInterval(refresh,1000);
    return ()=>{active=false;clearInterval(timer);};
  },[]);
  function created(run:RunRecord) {setRuns(previous=>[run,...previous.filter(value=>value.id!==run.id)]);setSelectedId(run.id);}
  async function open(id:string) {
    try {
      const {data,error} = await runApi().GET('/runs/{run_id}',{params:{path:{run_id:id}}});
      if(error) throw new Error(apiError(error));
      created(runRecordSchema.parse(data));setError('');
    } catch(e) {setError(e instanceof Error?e.message:'Could not reopen this run.');}
  }
  return {runs,selected:runs.find(run=>run.id===selectedId),error,created,open};
}

export function RunHistory({runs,selectedId,onOpen,error}:{runs:RunRecord[];selectedId?:string;onOpen:(id:string)=>void;error:string}) {
  return <div className="stack">{error&&<p role="alert">{error}</p>}{!runs.length?<div className="empty"><h3>No forecast runs yet</h3><p className="muted small">Create a forecast from the editable draft. Saved attempts remain available after restart.</p></div>:runs.map(run=><Button key={run.id} variant={run.id===selectedId?'secondary':'outline'} className="history-entry" onClick={()=>onOpen(run.id)} aria-label={`Open ${run.id} · ${run.status}`}><span>{run.id.slice(0,12)}<small>{run.configuration.cutoff} → {run.configuration.targets.join(', ')}</small></span><span>{run.status}</span></Button>)}</div>;
}
