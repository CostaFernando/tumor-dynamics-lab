import { afterEach, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Workbench } from './workbench';
import { snapshotsSchema } from '../lib/validation';
import snapshot from '../test-fixtures/snapshot.json';
import run from '../test-fixtures/evaluated-run.json';
afterEach(()=>vi.unstubAllGlobals());

it('retains selected target evidence and the recorded cutoff through guidance and draft edits',async()=>{
 const user = userEvent.setup();
 vi.stubGlobal('fetch',vi.fn(async(request:Request)=>Response.json(request.url.endsWith('/forecast/eligibility')?{available:true}:request.url.endsWith('/runs/'+run.id)?run:[run])));
 render(<Workbench snapshots={snapshotsSchema.parse([snapshot])}/>);
 await user.click(await screen.findByRole('button',{name:new RegExp('Open '+run.id)}));
 const selected = await screen.findByRole('region',{name:'Selected saved run'});
 await user.selectOptions(screen.getByLabelText('Evidence target time'),'21');
 await user.selectOptions(screen.getByLabelText('Forecasting cutoff'),'3');
 await user.click(screen.getByRole('button',{name:'Start guided walkthrough'}));
 await user.click(screen.getByRole('button',{name:'3. Review evidence'}));
 expect(within(selected).getByText('Cutoff: 7 days')).toBeVisible();
 expect(within(selected).getByRole('button',{name:'Download evidence bundle'})).toBeEnabled();
 expect(within(selected).getByText(new RegExp('Exports recorded evidence for run '+run.id))).toBeVisible();
 expect(screen.getByLabelText('Evidence target time')).toHaveValue('21');
 await user.click(screen.getByRole('button',{name:'Return to workbench'}));
 expect(screen.getByLabelText('Forecasting cutoff')).toHaveValue('3');
 expect(screen.getByText('0.350')).toBeVisible();
});
