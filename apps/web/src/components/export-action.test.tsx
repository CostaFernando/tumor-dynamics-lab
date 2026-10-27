import { afterEach, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExportAction } from './export-action';
import { runRecordSchema } from '../lib/validation';
import fixture from '../test-fixtures/evaluated-run.json';

afterEach(()=>{vi.unstubAllGlobals();vi.restoreAllMocks();});

it('downloads the selected successful run and explains unavailable attempts', async()=>{
 const user=userEvent.setup();
 const run=runRecordSchema.parse(fixture);
 const fetchMock=vi.fn(async(_request:Request)=>new Response(new Uint8Array([80,75,3,4]),{headers:{'Content-Type':'application/zip'}}));
 vi.stubGlobal('fetch',fetchMock);
 const createUrl=vi.fn(()=> 'blob:evidence');
 Object.defineProperty(URL,'createObjectURL',{configurable:true,value:createUrl});
 Object.defineProperty(URL,'revokeObjectURL',{configurable:true,value:vi.fn()});
 let filename='';
 vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this:HTMLAnchorElement){filename=this.download;});
 const {rerender}=render(<ExportAction run={run}/>);
 await user.click(screen.getByRole('button',{name:'Download evidence bundle'}));
 expect(fetchMock.mock.calls[0][0]).toHaveProperty('url',expect.stringContaining(`/runs/${run.id}/export`));
 expect(filename).toBe(`evidence-${run.id}.zip`);
 expect(createUrl).toHaveBeenCalledWith(expect.objectContaining({size:4,type:'application/zip'}));
 rerender(<ExportAction run={{...run,status:'cancelled',result:null}}/>);
 expect(screen.getByRole('button',{name:'Download evidence bundle'})).toBeDisabled();
 expect(screen.getByText(/Export requires a successful completed run/)).toBeVisible();
 rerender(<ExportAction run={{...run,result:{...run.result!,evaluations:[]}}}/>);
 expect(screen.getByRole('button',{name:'Download evidence bundle'})).toBeDisabled();
 expect(screen.getByText(/no complete recorded evaluation/)).toBeVisible();
});
