'use client';
import { useState } from 'react';
import type { Snapshot, Observation, RunConfiguration } from '@tdl/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { contextSchema } from '@/lib/validation';
import { ForecastSetup } from './forecast-setup';
import { SavedRun } from './saved-run';
import { RunHistory, useRunHistory } from './run-history';

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
  const [guideStep,setGuideStep] = useState(0);
  const [draftCutoff,setDraftCutoff] = useState<number | null>(null);
  const [draftTargets,setDraftTargets] = useState<number[] | null>(null);
  const [draftMethod,setDraftMethod] = useState<NonNullable<RunConfiguration['method']>>('last_observed');
  const history = useRunHistory();
  function resetDraft(){setDraftCutoff(null);setDraftTargets(null);}
  if (!snapshot) return <main className="empty-workspace"><h1>Tumor Dynamics Lab</h1><p>No experiment snapshots yet.</p><p>Initialize the fictional experiment with <code>pnpm demo</code>, or import a prepared local folder through the CLI.</p><Button onClick={()=>location.reload()}>Refresh experiments</Button></main>;
  const {experiment} = snapshot;
  const culture = experiment.cultures.find(c=>c.id===cultureId) ?? experiment.cultures[0];
  const scopes = [...new Set(experiment.samples.filter(s=>s.culture_id===culture.id).map(s=>s.scope))];
  const activeScope = scopes.includes(scope) ? scope : scopes[0];
  const observations = snapshot.observations.filter(o=>o.sample.culture_id===culture.id && o.sample.scope===activeScope).sort((a,b)=>a.sample.time-b.sample.time);
  const observation = observations.find(o=>o.sample.id===sampleId) ?? observations[0];
  const times = observations.map(o=>o.sample.time);
  const cutoff = draftCutoff !== null && times.includes(draftCutoff) ? draftCutoff : (times[Math.max(0,times.length-3)] ?? 0);
  const targets = draftTargets === null ? times.filter(time=>time>cutoff) : draftTargets;
  const configuration:RunConfiguration = {snapshot_id:snapshot.id,culture_id:culture.id,scope:activeScope??'',cutoff,targets,method:draftMethod};
  const start = Math.min(...times,...(culture.treatments??[]).map(t=>t.start));
  const end = Math.max(...times,...(culture.treatments??[]).map(t=>t.end));
  const position = (time:number) => (time-start)/Math.max(end-start,1)*100;
  function changeSnapshot(value:string) {
    contextSchema.parse({snapshot:value});
    const next = snapshots.find(s=>s.id===value)!;
    setSnapshotId(value); setCultureId(next.experiment.cultures[0].id); setScope(next.experiment.samples[0].scope); setSampleId(''); resetDraft();
  }
  return <>
    <header className="topbar"><div className="brand"><span className="brand-mark">∿</span>Tumor Dynamics Lab</div><div className="row"><span>Local research workspace</span><span className="badge">{experiment.synthetic?'SYNTHETIC DEMO':'PREPARED EXPERIMENT'}</span></div></header>
    <main className="workbench">
      <div className="workspace-heading"><div><p className="eyebrow">{guided?'Guided walkthrough':'Research workbench'}</p><h1>{experiment.name}</h1><p className="muted">{experiment.description}</p></div><Button variant="outline" onClick={()=>setGuided(!guided)}>{guided?'Return to workbench':'Start guided walkthrough'}</Button></div>
      {guided && <section className="guidance" aria-label="Guided forecast workflow"><nav className="row" aria-label="Walkthrough steps"><Button variant={guideStep===0?'secondary':'outline'} onClick={()=>setGuideStep(0)}>1. Inspect experiment</Button><Button variant={guideStep===1?'secondary':'outline'} onClick={()=>setGuideStep(1)}>2. Define forecast</Button><Button variant={guideStep===2?'secondary':'outline'} onClick={()=>setGuideStep(2)}>3. Review evidence</Button></nav><h2>{guideStep===0?'1. Inspect experiment':guideStep===1?'2. Define forecast':'3. Review evidence'}</h2><p>{guideStep===0?'Start with culture, sampling scope, time units, raw counts and unknown ancestry.':guideStep===1?'Choose an observed cutoff and later measured targets. Create a recorded attempt; the separate worker continues even when the browser closes.':'Open a successful saved attempt, select a target, and compare its forecast with held-out observations. Review total variation distance, previously unseen lineage share, counts and signed differences.'}</p><p className="muted">Return to the workbench or reopen guidance without losing the editable draft or selected saved run. Saved evidence stays associated with the selected attempt, even when the draft changes.</p></section>}
      <div className="work-grid">
        <aside className="stack">
          <Card><CardHeader><CardTitle>Experiment context</CardTitle></CardHeader><CardContent className="stack">
            <label className="field">Experiment snapshot<NativeSelect value={snapshot.id} onChange={e=>changeSnapshot(e.target.value)}>{snapshots.map(s=><NativeSelectOption key={s.id} value={s.id}>{s.experiment.name} · {s.id.slice(0,8)}</NativeSelectOption>)}</NativeSelect></label>
            <label className="field">Culture<NativeSelect value={culture.id} onChange={e=>{contextSchema.parse({culture:e.target.value});setCultureId(e.target.value);setSampleId('');resetDraft();}}>{experiment.cultures.map(c=><NativeSelectOption value={c.id} key={c.id}>{c.name}</NativeSelectOption>)}</NativeSelect></label>
            <label className="field">Sampling scope<NativeSelect value={activeScope} onChange={e=>{contextSchema.parse({scope:e.target.value});setScope(e.target.value);setSampleId('');resetDraft();}}>{scopes.map(s=><NativeSelectOption value={s} key={s}>{s}</NativeSelectOption>)}</NativeSelect></label>
            <p className="muted small">Time unit: {experiment.time_unit}</p><p className="snapshot-id">Snapshot {snapshot.id}</p>
          </CardContent></Card>
          <Card><CardHeader><CardTitle>Forecast setup</CardTitle></CardHeader><CardContent><ForecastSetup configuration={configuration} times={times} timeUnit={experiment.time_unit} onCutoff={value=>{setDraftCutoff(value);setDraftTargets(targets.filter(time=>time>value));}} onTargets={setDraftTargets} onMethod={setDraftMethod} onCreated={history.created}/></CardContent></Card>
        </aside>
        <section className="stack">
          {history.selected && <SavedRun run={history.selected} snapshots={snapshots} onChanged={history.created}/>}
          {!observation ? <Card><CardHeader><CardTitle>Culture observations</CardTitle></CardHeader><CardContent><p>No samples in this culture.</p><p className="muted">Choose a sampled culture, or prepare a new snapshot through the CLI. Cultures and sampling scopes are never pooled.</p></CardContent></Card> : <>
          <Card><CardHeader><CardTitle>Experimental timeline</CardTitle></CardHeader><CardContent>
            <p className="muted small">Editable draft timeline · {culture.name} · {activeScope} · {experiment.time_unit}</p>
            <div className="timeline" style={{minHeight:140+(culture.treatments?.length??0)*28}}>
              {(culture.treatments??[]).map((t,i)=><div key={`${t.name}-${i}`} className="treatment" style={{left:`${position(t.start)}%`,width:`${position(t.end)-position(t.start)}%`,top:i*28}} title={t.dose??undefined}>{t.name} exposure · {t.start}–{t.end}</div>)}
              {(culture.treatments??[]).map((t,i)=><div className="withdrawal" key={`${t.name}-withdrawal-${i}`} style={{left:`${position(t.end)}%`,top:(culture.treatments?.length??0)*28+8}}>Withdrawal {t.end}</div>)}
              <div className="timeline-axis" style={{top:(culture.treatments?.length??0)*28+50}}>{observations.map(o=><button key={o.sample.id} className={`sample-dot ${o.sample.id===observation.sample.id?'selected':''}`} style={{left:`${position(o.sample.time)}%`}} onClick={()=>setSampleId(o.sample.id)} aria-label={`Inspect sample at ${o.sample.time} ${experiment.time_unit}`}><span/><small>{o.sample.time}</small><small>{o.sample.time===cutoff?'Cutoff':o.sample.time<cutoff?'Input':'Held out'}</small></button>)}</div>
            </div><p className="muted small">Sampling times are positioned on a linear time scale. Recovery follows treatment withdrawal.</p>
          </CardContent></Card>
          <Card><CardHeader><CardTitle>Observed lineage composition</CardTitle></CardHeader><CardContent className="stack">
            <label className="field inline-field">Inspect sample<NativeSelect value={observation.sample.id} onChange={e=>{contextSchema.parse({sample:e.target.value});setSampleId(e.target.value);}}>{observations.map(o=><NativeSelectOption key={o.sample.id} value={o.sample.id}>{o.sample.time} {experiment.time_unit} · {o.sample.id}</NativeSelectOption>)}</NativeSelect></label>
            <p className="muted small">{observation.sample.time>cutoff?'Held-out observation':observation.sample.time===cutoff?'Input observation at cutoff':'Input observation before cutoff'} · draft cutoff {cutoff} {experiment.time_unit}</p>
            <CompositionBar observation={observation}/>
            <Table><TableHeader><TableRow><TableHead>Category</TableHead><TableHead>Observed count</TableHead><TableHead>Observed proportion</TableHead></TableRow></TableHeader><TableBody>{Object.entries(observation.sample.counts).map(([name,count])=><TableRow key={name}><TableCell>{categoryLabel(name)}</TableCell><TableCell>{count}</TableCell><TableCell>{((observation.proportions[name]??0)*100).toFixed(1)}%</TableCell></TableRow>)}<TableRow><TableCell>Sample total</TableCell><TableCell>{observation.total}</TableCell><TableCell>100.0%</TableCell></TableRow></TableBody></Table>
            {observation.sample.cell_state_summary && <div className="quiet"><strong>Descriptive cell-state information</strong><p>{observation.sample.cell_state_summary}</p><p>Cell state is separate from lineage identity.</p></div>}
            <p className="muted small">Proportions describe sampled composition, not absolute abundance. Non-detection does not establish extinction. Unknown ancestry stays in the denominator.</p>
          </CardContent></Card>
          </>}
        </section>
        <aside className="stack"><Card><CardHeader><CardTitle>Run history</CardTitle></CardHeader><CardContent><RunHistory runs={history.runs} selectedId={history.selected?.id} onOpen={history.open} error={history.error}/></CardContent></Card><Card><CardHeader><CardTitle>Reading this experiment</CardTitle></CardHeader><CardContent><p className="muted">Lineage describes shared ancestry. A lineage can contain several cell states.</p><p className="notice">{experiment.synthetic?'Fictional data exercises software behavior. Synthetic results do not establish biological validity.':'Separate cultures are not automatically biologically independent.'}</p><p className="muted small">Prepared snapshots are imported through the CLI.</p></CardContent></Card></aside>
      </div>
    </main>
  </>;
}
