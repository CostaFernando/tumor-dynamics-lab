import { afterEach, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Workbench } from './workbench';
import snapshot from '../test-fixtures/snapshot.json';
import { snapshotsSchema } from '../lib/validation';

const saved = {
  id:'recorded-run',configuration:{snapshot_id:snapshot.id,culture_id:'culture-01',scope:'whole culture',cutoff:7,targets:[14,21],method:'last_observed'},
  status:'succeeded',created_at:'2026-10-27T00:00:00Z',method_version:'last-observed-v1',software_version:'0.1.0',settings:{smoothing:false},deterministic:true,crosses_withdrawal:true,error:null,
  result:{input_categories:['A','B','C','__unknown__'],input_observations:snapshot.experiment.samples.filter(s=>s.time<=7),predictions:[{time:14,proportions:{A:.65,B:.25,C:0,__unknown__:.1}},{time:21,proportions:{A:.65,B:.25,C:0,__unknown__:.1}}]},
};
afterEach(()=>vi.unstubAllGlobals());

it('keeps the editable draft separate from reopened saved evidence and retains both through guidance', async () => {
  const user = userEvent.setup();
  const calls:string[]=[];
  vi.stubGlobal('fetch',vi.fn(async (request:Request)=>{
    calls.push(`${request.method} ${new URL(request.url).pathname}`);
    if(request.url.endsWith('/forecast/eligibility')) return Response.json({available:true});
    if(request.url.endsWith('/runs/recorded-run')) return Response.json(saved);
    return Response.json([saved]);
  }));
  render(<Workbench snapshots={snapshotsSchema.parse([snapshot])}/>);
  await user.click(await screen.findByRole('button',{name:/Open recorded-run/}));
  const evidence = await screen.findByRole('region',{name:'Selected saved run'});
  expect(within(evidence).getByText('Cutoff: 7 days')).toBeVisible();
  await user.selectOptions(screen.getByLabelText('Forecasting cutoff'),'3');
  expect(within(evidence).getByText('Cutoff: 7 days')).toBeVisible();
  await user.click(screen.getByRole('button',{name:'Start guided walkthrough'}));
  await user.click(screen.getByRole('button',{name:'2. Define forecast'}));
  expect(screen.getByLabelText('Forecasting cutoff')).toHaveValue('3');
  await user.click(screen.getByRole('button',{name:'Return to workbench'}));
  expect(within(evidence).getByText('Cutoff: 7 days')).toBeVisible();
  expect(calls.filter(c=>c.startsWith('POST /api/runs'))).toHaveLength(0);
});

it('blocks creation with the backend eligibility explanation instead of substituting a method', async () => {
  vi.stubGlobal('fetch',vi.fn(async(request:Request)=>Response.json(request.url.endsWith('/forecast/eligibility')?{available:false,reason:'Targets require comparable sampling scope'}:[])));
  render(<Workbench snapshots={snapshotsSchema.parse([snapshot])}/>);
  expect(await screen.findByText('Targets require comparable sampling scope')).toBeVisible();
  expect(screen.getByRole('button',{name:'Create forecast run'})).toBeDisabled();
});

it('creates a persisted queued run from the draft and exposes API rejection errors', async () => {
  const user = userEvent.setup();
  let created=false;
  let submitted:unknown;
  vi.stubGlobal('fetch',vi.fn(async(request:Request)=>{
    if(request.url.endsWith('/forecast/eligibility')) return Response.json({available:true});
    if(request.method==='POST') {
      submitted=await request.json();
      if(created) return Response.json({detail:'The selected sampling scope has no measured targets'},{status:422});
      created=true;
      return Response.json({...saved,status:'queued',result:null},{status:201});
    }
    return Response.json(created?[{...saved,status:'queued',result:null}]:[]);
  }));
  render(<Workbench snapshots={snapshotsSchema.parse([snapshot])}/>);
  const button=screen.getByRole('button',{name:'Create forecast run'});
  await waitFor(()=>expect(button).toBeEnabled());
  await user.click(button);
  expect(submitted).toEqual(saved.configuration);
  expect(await screen.findByText('Queued for the separate local worker. Closing the browser does not cancel execution.')).toBeVisible();
  expect(screen.getByRole('button',{name:'Open recorded-run · queued'})).toBeVisible();
  await user.click(button);
  expect(await screen.findByText('The selected sampling scope has no measured targets')).toBeVisible();
});

it('keeps a cancelled attempt in history while retry selects a new recorded attempt',async()=>{
  const user=userEvent.setup();
  const original={...saved,id:'d'.repeat(32),status:'cancelled',error:'Cancelled by researcher',result:null};
  const retry={...original,id:'e'.repeat(32),status:'queued',error:null};
  let retried=false;
  vi.stubGlobal('fetch',vi.fn(async(request:Request)=>{
    if(request.url.endsWith('/forecast/eligibility'))return Response.json({available:true});
    if(request.url.endsWith('/retry')){retried=true;return Response.json(retry,{status:201});}
    if(request.url.endsWith(`/runs/${original.id}`))return Response.json(original);
    return Response.json(retried?[retry,original]:[original]);
  }));
  render(<Workbench snapshots={snapshotsSchema.parse([snapshot])}/>);
  await user.click(await screen.findByRole('button',{name:`Open ${original.id} · cancelled`}));
  expect(await screen.findByText('Cancelled by researcher')).toBeVisible();
  await user.click(screen.getByRole('button',{name:'Retry as new attempt'}));
  const evidence=screen.getByRole('region',{name:'Selected saved run'});
  expect(within(evidence).getByText(`Recorded evidence · ${retry.id}`)).toBeVisible();
  expect(screen.getByRole('button',{name:`Open ${original.id} · cancelled`})).toBeVisible();
  expect(screen.getByRole('button',{name:`Open ${retry.id} · queued`})).toBeVisible();
});
