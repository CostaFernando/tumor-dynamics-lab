'use client';
import { useState } from 'react';
import type { Snapshot, Observation } from '@tdl/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { contextSchema } from '@/lib/validation';

export const categoryLabel = (name: string) => name === '__unknown__' ? 'Unknown ancestry' : `Lineage ${name}`;
const colors = ['#216d62','#8ca959','#bc8a50','#706c98','#769da9','#a67882'];

export function CompositionBar({observation}: {observation: Observation}) {
  return <div className="composition-bar" role="img" aria-label={`Observed composition, sample ${observation.sample.id}`}>
    {Object.entries(observation.proportions).map(([name,value],index) => <span key={name} style={{width:`${value*100}%`,background:colors[index%colors.length]}} title={`${categoryLabel(name)}: ${(value*100).toFixed(1)}%`}>{value>=.1 ? categoryLabel(name) : ''}</span>)}
  </div>;
}

export function Workbench({snapshots}: {snapshots: Snapshot[]}) {
  const [snapshotId,setSnapshotId] = useState(snapshots[0]?.id ?? '');
  const snapshot = snapshots.find(s => s.id === snapshotId);
  const [cultureId,setCultureId] = useState(snapshot?.experiment.cultures[0]?.id ?? '');
  const [scope,setScope] = useState(snapshot?.experiment.samples[0]?.scope ?? '');
  const [sampleId,setSampleId] = useState('');
  const [guided,setGuided] = useState(false);
  if (!snapshot) return <main className="empty-workspace"><h1>Tumor Dynamics Lab</h1><p>No experiment snapshots yet.</p><p>Initialize the fictional experiment with <code>pnpm demo</code>, or import a prepared local folder through the CLI.</p><Button onClick={()=>location.reload()}>Refresh experiments</Button></main>;
  const {experiment} = snapshot;
  const culture = experiment.cultures.find(c=>c.id===cultureId) ?? experiment.cultures[0];
  const scopes = [...new Set(experiment.samples.filter(s=>s.culture_id===culture.id).map(s=>s.scope))];
  const activeScope = scopes.includes(scope) ? scope : scopes[0];
  const observations = snapshot.observations.filter(o=>o.sample.culture_id===culture.id && o.sample.scope===activeScope).sort((a,b)=>a.sample.time-b.sample.time);
  const observation = observations.find(o=>o.sample.id===sampleId) ?? observations[0];
  const times = observations.map(o=>o.sample.time);
  const start = Math.min(...times,...(culture.treatments??[]).map(t=>t.start));
  const end = Math.max(...times,...(culture.treatments??[]).map(t=>t.end));
  const position = (time:number) => (time-start)/Math.max(end-start,1)*100;
  function changeSnapshot(value:string) {
    contextSchema.parse({snapshot:value});
    const next = snapshots.find(s=>s.id===value)!;
    setSnapshotId(value); setCultureId(next.experiment.cultures[0].id); setScope(next.experiment.samples[0].scope); setSampleId('');
  }
  return <>
    <header className="topbar"><div className="brand"><span className="brand-mark">∿</span>Tumor Dynamics Lab</div><div className="row"><span>Local research workspace</span><span className="badge">{experiment.synthetic?'SYNTHETIC DEMO':'PREPARED EXPERIMENT'}</span></div></header>
    <main className="workbench">
      <div className="workspace-heading"><div><p className="eyebrow">{guided?'Guided walkthrough':'Research workbench'}</p><h1>{experiment.name}</h1><p className="muted">{experiment.description}</p></div><Button variant="outline" onClick={()=>setGuided(!guided)}>{guided?'Return to workbench':'Start guided walkthrough'}</Button></div>
      {guided && <section className="guidance" aria-label="Guided inspection"><h2>1. Inspect experiment</h2><p>Start with the culture, sampling scope and time units. Inspect observed counts and unknown ancestry before defining a forecast.</p><p className="muted">Forecast configuration and evidence review become available as run capabilities are added. You can return to the workbench without losing your selection.</p></section>}
      <div className="work-grid">
        <aside className="stack">
          <Card><CardHeader><CardTitle>Experiment context</CardTitle></CardHeader><CardContent className="stack">
            <label className="field">Experiment snapshot<NativeSelect value={snapshot.id} onChange={e=>changeSnapshot(e.target.value)}>{snapshots.map(s=><NativeSelectOption key={s.id} value={s.id}>{s.experiment.name} · {s.id.slice(0,8)}</NativeSelectOption>)}</NativeSelect></label>
            <label className="field">Culture<NativeSelect value={culture.id} onChange={e=>{contextSchema.parse({culture:e.target.value});setCultureId(e.target.value);setSampleId('');}}>{experiment.cultures.map(c=><NativeSelectOption value={c.id} key={c.id}>{c.name}</NativeSelectOption>)}</NativeSelect></label>
            <label className="field">Sampling scope<NativeSelect value={activeScope} onChange={e=>{contextSchema.parse({scope:e.target.value});setScope(e.target.value);setSampleId('');}}>{scopes.map(s=><NativeSelectOption value={s} key={s}>{s}</NativeSelectOption>)}</NativeSelect></label>
            <p className="muted small">Time unit: {experiment.time_unit}</p><p className="snapshot-id">Snapshot {snapshot.id}</p>
          </CardContent></Card>
          <Card><CardHeader><CardTitle>Forecast setup</CardTitle></CardHeader><CardContent><p className="muted">Forecast configuration is not available in this initial inspection view.</p></CardContent></Card>
        </aside>
        <section className="stack">
          <Card><CardHeader><CardTitle>Experimental timeline</CardTitle></CardHeader><CardContent>
            <p className="muted small">{culture.name} · {activeScope} · {experiment.time_unit}</p>
            <div className="timeline" style={{minHeight:140+(culture.treatments?.length??0)*28}}>
              {(culture.treatments??[]).map((t,i)=><div key={`${t.name}-${i}`} className="treatment" style={{left:`${position(t.start)}%`,width:`${position(t.end)-position(t.start)}%`,top:i*28}} title={t.dose??undefined}>{t.name} exposure · {t.start}–{t.end}</div>)}
              {(culture.treatments??[]).map((t,i)=><div className="withdrawal" key={`${t.name}-withdrawal-${i}`} style={{left:`${position(t.end)}%`,top:(culture.treatments?.length??0)*28+8}}>Withdrawal {t.end}</div>)}
              <div className="timeline-axis" style={{top:(culture.treatments?.length??0)*28+50}}>{observations.map(o=><button key={o.sample.id} className={`sample-dot ${o.sample.id===observation.sample.id?'selected':''}`} style={{left:`${position(o.sample.time)}%`}} onClick={()=>setSampleId(o.sample.id)} aria-label={`Inspect sample at ${o.sample.time} ${experiment.time_unit}`}><span/><small>{o.sample.time}</small></button>)}</div>
            </div><p className="muted small">Sampling times are positioned on a linear time scale. Recovery follows treatment withdrawal.</p>
          </CardContent></Card>
          <Card><CardHeader><CardTitle>Observed lineage composition</CardTitle></CardHeader><CardContent className="stack">
            <label className="field inline-field">Inspect sample<NativeSelect value={observation.sample.id} onChange={e=>{contextSchema.parse({sample:e.target.value});setSampleId(e.target.value);}}>{observations.map(o=><NativeSelectOption key={o.sample.id} value={o.sample.id}>{o.sample.time} {experiment.time_unit} · {o.sample.id}</NativeSelectOption>)}</NativeSelect></label>
            <CompositionBar observation={observation}/>
            <Table><TableHeader><TableRow><TableHead>Category</TableHead><TableHead>Observed count</TableHead><TableHead>Observed proportion</TableHead></TableRow></TableHeader><TableBody>{Object.entries(observation.sample.counts).map(([name,count])=><TableRow key={name}><TableCell>{categoryLabel(name)}</TableCell><TableCell>{count}</TableCell><TableCell>{((observation.proportions[name]??0)*100).toFixed(1)}%</TableCell></TableRow>)}<TableRow><TableCell>Sample total</TableCell><TableCell>{observation.total}</TableCell><TableCell>100.0%</TableCell></TableRow></TableBody></Table>
            {observation.sample.cell_state_summary && <div className="quiet"><strong>Descriptive cell-state information</strong><p>{observation.sample.cell_state_summary}</p><p>Cell state is separate from lineage identity.</p></div>}
            <p className="muted small">Proportions describe sampled composition, not absolute abundance. Non-detection does not establish extinction. Unknown ancestry stays in the denominator.</p>
          </CardContent></Card>
        </section>
        <aside className="stack"><Card><CardHeader><CardTitle>Run history</CardTitle></CardHeader><CardContent><div className="empty"><h3>No forecast runs yet</h3><p className="muted small">Saved attempts will appear here when forecast execution is available.</p></div></CardContent></Card><Card><CardHeader><CardTitle>Reading this experiment</CardTitle></CardHeader><CardContent><p className="muted">Lineage describes shared ancestry. A lineage can contain several cell states.</p><p className="notice">{experiment.synthetic?'Fictional data exercises software behavior. Synthetic results do not establish biological validity.':'Separate cultures are not automatically biologically independent.'}</p><p className="muted small">Prepared snapshots are imported through the CLI.</p></CardContent></Card></aside>
      </div>
    </main>
  </>;
}
