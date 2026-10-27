import { afterEach, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { RunRecord } from '@tdl/api-client';
import { RunActions } from './run-actions';

const queued:RunRecord = {id:'a'.repeat(32),configuration:{snapshot_id:'b'.repeat(64),culture_id:'culture-01',scope:'whole culture',cutoff:7,targets:[14],method:'last_observed'},status:'queued',created_at:'2026-10-27',method_version:'last-observed-v1',software_version:'0.1.0',settings:{smoothing:false},deterministic:true,crosses_withdrawal:true,result:null};
afterEach(()=>vi.unstubAllGlobals());

it('cancels the selected attempt and selects a distinct retry while showing failures', async()=>{
  const user=userEvent.setup();
  const changed=vi.fn();
  let fail=false;
  const cancelled={...queued,status:'cancelled' as const,error:'Cancelled by researcher'};
  vi.stubGlobal('fetch',vi.fn(async(request:Request)=>{
    if(fail)return Response.json({detail:'Worker storage unavailable'},{status:409});
    return Response.json(request.url.endsWith('/cancel')?cancelled:{...queued,id:'c'.repeat(32)},{status:request.url.endsWith('/cancel')?200:201});
  }));
  const {rerender}=render(<RunActions run={queued} onChanged={changed}/>);
  await user.click(screen.getByRole('button',{name:'Cancel attempt'}));
  expect(changed).toHaveBeenLastCalledWith(expect.objectContaining({id:queued.id,status:'cancelled'}));
  rerender(<RunActions run={cancelled} onChanged={changed}/>);
  expect(screen.queryByRole('button',{name:'Cancel attempt'})).not.toBeInTheDocument();
  await user.click(screen.getByRole('button',{name:'Retry as new attempt'}));
  expect(changed).toHaveBeenLastCalledWith(expect.objectContaining({id:'c'.repeat(32),status:'queued'}));
  fail=true;
  await user.click(screen.getByRole('button',{name:'Retry as new attempt'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Worker storage unavailable');
  rerender(<RunActions run={{...queued,status:'succeeded'}} onChanged={changed}/>);
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});
