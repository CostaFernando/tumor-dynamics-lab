'use client';
import { useState } from 'react';
import type { RunRecord, Snapshot } from '@tdl/api-client';
import { evidenceSelectionSchema } from '@/lib/validation';
import { NativeSelect, NativeSelectOption } from './ui/native-select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { categoryLabel, CompositionBar } from './composition-bar';

const percentage = (value:number)=>(value*100).toFixed(1)+'%';
const signedDifference = (value:number)=>(value<0?'−':value>0?'+':'')+Math.abs(value).toFixed(1)+' pp';

export function EvidenceView({run,snapshot}:{run:RunRecord;snapshot?:Snapshot}) {
 const evaluations = run.result?.evaluations ?? [];
 const [time,setTime] = useState(evaluations[0]?.time);
 const [unseenOnly,setUnseenOnly] = useState(false);
 const evidence = evaluations.find(value=>value.time===time) ?? evaluations[0];
 if(!evidence) return <p className="quiet">Held-out evaluation is unavailable for this recorded attempt. Existing saved predictions are preserved without recomputation.</p>;
 const unit = snapshot?.experiment.time_unit ?? 'time units';
 const visible = evidence.categories.filter(row=>!unseenOnly||row.previously_unseen);
 const inputIds = new Set(run.result?.input_observations.map(sample=>sample.id));
 const inputs = snapshot?.observations.filter(observation=>inputIds.has(observation.sample.id)) ?? [];
 function changeSelection(nextTime:number,nextUnseenOnly:boolean) {
  const next = evidenceSelectionSchema.parse({time:nextTime,unseenOnly:nextUnseenOnly});
  setTime(next.time);setUnseenOnly(next.unseenOnly);
 }
 return <section aria-label="Saved held-out evidence" className="stack">
  <h3>Held-out comparison</h3>
  <label className="field inline-field">Evidence target time<NativeSelect value={evidence.time} onChange={event=>changeSelection(Number(event.target.value),unseenOnly)}>{evaluations.map(value=><NativeSelectOption key={value.time} value={value.time}>{value.time} {unit}</NativeSelectOption>)}</NativeSelect></label>
  <div className="evidence-metrics"><div aria-label="Total variation distance"><small>Total variation distance</small><strong>{evidence.total_variation_distance.toFixed(3)}</strong></div><div aria-label="Previously unseen lineage share"><small>Previously unseen lineage share</small><strong>{percentage(evidence.previously_unseen_share)}</strong></div></div>
  <p className="muted small">Observed sample {evidence.sample_id} · total {evidence.observed_total} cells</p>
  <div className="stack"><div><p className="small">Forecast · saved prediction</p><CompositionBar categories={evidence.categories.map(row=>[row.category,row.predicted_proportion])} label="Forecast composition"/></div><div><p className="small">Held-out observation · {evidence.time} {unit}</p><CompositionBar categories={evidence.categories.map(row=>[row.category,row.observed_proportion])} label="Held-out observed composition"/></div></div>
  <label className="small row"><input type="checkbox" checked={unseenOnly} onChange={event=>changeSelection(evidence.time,event.target.checked)}/>Show only previously unseen lineages in table</label>
  <Table aria-label="Per-category held-out comparison"><TableHeader><TableRow><TableHead>Category</TableHead><TableHead>Forecast</TableHead><TableHead>Observed</TableHead><TableHead>Difference</TableHead><TableHead>Observed count / total</TableHead></TableRow></TableHeader><TableBody>{visible.map(row=><TableRow key={row.category}><TableCell>{categoryLabel(row.category)}{row.previously_unseen&&<small className="unseen-label"> Previously unseen</small>}</TableCell><TableCell>{percentage(row.predicted_proportion)}</TableCell><TableCell>{percentage(row.observed_proportion)}</TableCell><TableCell>{signedDifference(row.difference_percentage_points)}</TableCell><TableCell>{row.observed_count} / {evidence.observed_total}</TableCell></TableRow>)}</TableBody></Table>
  {visible.length===0&&<p>No previously unseen identified lineages at this target.</p>}
  <p className="muted small">Differences are forecast minus observed, in percentage points. Total variation distance is half the sum of absolute proportion differences over every category (0 means identical; 1 means disjoint). Table filtering does not change scores, chart proportions or denominators. Previously unseen identified lineages receive zero prediction; unknown ancestry remains a separate category.</p>
  <details><summary>Recorded input observations through cutoff {run.configuration.cutoff} {unit}</summary><div className="stack">{inputs.map(observation=><div key={observation.sample.id}><p>{observation.sample.id} · {observation.sample.time} {unit} · total {observation.total} cells</p><Table aria-label={`Recorded input ${observation.sample.id}`}><TableHeader><TableRow><TableHead>Category</TableHead><TableHead>Count</TableHead><TableHead>Proportion</TableHead></TableRow></TableHeader><TableBody>{Object.entries(observation.sample.counts).map(([category,count])=><TableRow key={category}><TableCell>{categoryLabel(category)}</TableCell><TableCell>{count}</TableCell><TableCell>{percentage(observation.proportions[category]??0)}</TableCell></TableRow>)}</TableBody></Table></div>)}</div></details>
  <p className="muted small">Observed proportions do not establish absolute abundance; non-detection does not establish extinction. {snapshot?.experiment.synthetic?'These fictional comparisons exercise software behavior and do not establish biological validity.':''}</p>
 </section>;
}
