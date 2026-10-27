'use client';
import { useEffect, useState } from 'react';
import { createApiClient, type Snapshot } from '@tdl/api-client';
import { Workbench } from '@/components/workbench';
import { snapshotsSchema } from '@/lib/validation';
import { Button } from '@/components/ui/button';
export default function Home() {
  const [snapshots,setSnapshots] = useState<Snapshot[] | null>(null);
  const [error,setError] = useState('');
  useEffect(()=>{let active=true;createApiClient().GET('/snapshots').then(({data,error})=>{if(error)throw new Error('The API could not load experiments.');const valid=snapshotsSchema.parse(data);if(active)setSnapshots(valid);}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Could not load experiments.');});return()=>{active=false};},[]);
  if(error) return <main className="empty-workspace"><h1>Unable to open the workspace</h1><p role="alert">{error}</p><p>Start the local API and verify the configured research storage.</p><Button onClick={()=>location.reload()}>Try again</Button></main>;
  if(!snapshots) return <main className="empty-workspace" role="status">Loading experiment snapshots…</main>;
  return <Workbench snapshots={snapshots}/>;
}
