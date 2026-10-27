'use client';
import { useEffect, useState } from 'react';
import type { Eligibility, RunConfiguration, RunRecord } from '@tdl/api-client';
import { Button } from './ui/button';
import { NativeSelect, NativeSelectOption } from './ui/native-select';
import { runConfigurationSchema, methodSchema, eligibilitySchema, runRecordSchema } from '@/lib/validation';
import { apiError, runApi } from '@/lib/run-api';

export function ForecastSetup({configuration,times,timeUnit,onCutoff,onTargets,onMethod,onCreated}: {
  configuration:RunConfiguration;times:number[];timeUnit:string;onCutoff:(value:number)=>void;onTargets:(values:number[])=>void;onMethod:(value:NonNullable<RunConfiguration['method']>)=>void;onCreated:(run:RunRecord)=>void;
}) {
  const [eligibility,setEligibility] = useState<Eligibility | null>(null);
  const [error,setError] = useState('');
  const [submitting,setSubmitting] = useState(false);
  const serialized = JSON.stringify(configuration);
  const valid = runConfigurationSchema.safeParse(configuration);
  useEffect(()=>{
    let active = true;
    setEligibility(null);setError('');
    const parsed = runConfigurationSchema.safeParse(JSON.parse(serialized));
    if(parsed.success) runApi().POST('/forecast/eligibility',{body:parsed.data}).then(({data,error})=>{
      if(error) throw new Error(apiError(error));
      const result = eligibilitySchema.parse(data);
      if(active) setEligibility(result);
    }).catch(e=>{if(active)setError(e instanceof Error?e.message:'Could not check forecast eligibility.');});
    return ()=>{active=false;};
  },[serialized]);
  async function createRun() {
    if(!valid.success) return;
    setSubmitting(true);setError('');
    try {
      const {data,error} = await runApi().POST('/runs',{body:valid.data});
      if(error) throw new Error(apiError(error));
      onCreated(runRecordSchema.parse(data));
    } catch(e) {setError(e instanceof Error?e.message:'Could not create forecast run.');}
    finally {setSubmitting(false);}
  }
  return <div className="stack">
    <p className="eyebrow">Editable draft</p>
    <label className="field">Forecasting cutoff<NativeSelect value={configuration.cutoff} disabled={!times.length} onChange={e=>onCutoff(Number(e.target.value))}>{times.map(time=><NativeSelectOption key={time} value={time}>{time} {timeUnit}</NativeSelectOption>)}</NativeSelect></label>
    <fieldset className="target-times"><legend>Measured target times</legend>{times.filter(time=>time>configuration.cutoff).map(time=><label key={time}><input type="checkbox" checked={configuration.targets.includes(time)} onChange={e=>onTargets(e.target.checked?[...configuration.targets,time]:configuration.targets.filter(value=>value!==time))}/>{time} {timeUnit}</label>)}</fieldset>
    <label className="field">Baseline method<NativeSelect value={configuration.method} onChange={e=>onMethod(methodSchema.parse(e.target.value))}><NativeSelectOption value="last_observed">Last observed composition</NativeSelectOption><NativeSelectOption value="damped_trend">Damped trend extrapolation</NativeSelectOption></NativeSelect></label>
    <p className="muted small">{configuration.method==='damped_trend'?'Uses the last two input times with a fixed 0.5 pseudocount and bounded exponential damping. Smoothing differs from the unsmoothed last-observed composition.':'Preserves the latest observed composition without smoothing.'}</p>
    {!valid.success ? <p role="status">Choose at least one measured target after the cutoff.</p> : error ? <p role="alert">{error}</p> : !eligibility ? <p role="status">Checking forecast eligibility…</p> : !eligibility.available ? <p role="status">{eligibility.reason}</p> : <p className="muted small">Eligible for this culture and sampling scope.</p>}
    <Button onClick={createRun} disabled={!valid.success||!eligibility?.available||submitting}>{submitting?'Creating run…':'Create forecast run'}</Button>
    <p className="notice">This baseline does not model biological effects of treatment changes, including withdrawal. Crossing withdrawal is allowed.</p>
  </div>;
}
