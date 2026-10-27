import { RunActions } from './run-actions';
import { ExportAction } from './export-action';
import type { RunRecord, Snapshot } from '@tdl/api-client';
import { EvidenceView } from './evidence-view';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
const label = (category:string)=>category==='__unknown__'?'Unknown ancestry':`Lineage ${category}`;
export function SavedRun({run,snapshots,onChanged}:{run:RunRecord;snapshots:Snapshot[];onChanged?:(run:RunRecord)=>void}) {
  const snapshot = snapshots.find(value=>value.id===run.configuration.snapshot_id);
  const unit = snapshot?.experiment.time_unit ?? 'time units';
  const culture = snapshot?.experiment.cultures.find(value=>value.id===run.configuration.culture_id);
  return <section aria-label="Selected saved run"><Card><CardHeader><CardTitle>Selected saved run</CardTitle></CardHeader><CardContent className="stack">
    <div className="saved-run-context"><p><strong>Recorded evidence · {run.id}</strong></p><p>Status: {run.status}</p><p>{snapshot?.experiment.name??'Recorded experiment'} · {culture?.name??run.configuration.culture_id} · {run.configuration.scope}</p><p className="snapshot-id">Snapshot {run.configuration.snapshot_id}</p><p>Cutoff: {run.configuration.cutoff} {unit}</p><p>Targets: {run.configuration.targets.join(', ')} {unit}</p><p>Method: {run.configuration.method==='damped_trend'?'Damped trend extrapolation':'Last observed composition'}</p><p className="muted small">{run.method_version} · software {run.software_version} · deterministic</p></div>
    {run.crosses_withdrawal && <p className="notice">This forecast crosses treatment withdrawal. The baseline does not model its biological effect.</p>}
    {(run.status==='queued'||run.status==='running') && <p role="status">{run.status==='queued'?'Queued for the separate local worker.':'The local worker is processing this attempt.'} Closing the browser does not cancel execution.</p>}
    {run.error && <p role="alert">{run.error}</p>}
    {onChanged && <RunActions key={`actions-${run.id}`} run={run} onChanged={onChanged}/>}
    <ExportAction key={`export-${run.id}`} run={run}/>
    {run.result && <EvidenceView key={`evidence-${run.id}`} run={run} snapshot={snapshot}/>}
    {run.result && <details><summary>Saved prediction values</summary><div className="stack"><h3>Saved predictions</h3><p className="muted small">Input sampling times: {run.result.input_observations.map(observation=>observation.time).join(', ')} {unit}. Measurements after the recorded cutoff were excluded from the predictor.</p>{run.result.predictions.map(prediction=><div key={prediction.time}><h3>Forecast at {prediction.time} {unit}</h3><Table><TableHeader><TableRow><TableHead>Category</TableHead><TableHead>Predicted proportion</TableHead></TableRow></TableHeader><TableBody>{Object.entries(prediction.proportions).map(([category,value])=><TableRow key={category}><TableCell>{label(category)}</TableCell><TableCell>{(value*100).toFixed(1)}%</TableCell></TableRow>)}</TableBody></Table></div>)}<p className="muted small">These saved values reopen without recomputation. Held-out comparison is recorded separately from these predictions.</p></div></details>}
  </CardContent></Card></section>;
}
