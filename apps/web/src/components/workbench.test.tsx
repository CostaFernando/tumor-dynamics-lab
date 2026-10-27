import { expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Workbench } from './workbench';
import snapshot from '../test-fixtures/snapshot.json';
import { snapshotsSchema } from '../lib/validation';

it('inspects persisted counts and preserves the selected sample when leaving guidance', async () => {
  const user = userEvent.setup();
  render(<Workbench snapshots={snapshotsSchema.parse([snapshot])} />);
  expect(screen.getByRole('heading',{name:'Fictional recovery study'})).toBeVisible();
  expect(screen.getByText('No forecast runs yet')).toBeVisible();
  await user.selectOptions(screen.getByLabelText('Inspect sample'), 'day-7');
  expect(screen.getByRole('cell',{name:'65'})).toBeVisible();
  expect(screen.getByRole('cell',{name:'Unknown ancestry'})).toBeVisible();
  await user.click(screen.getByRole('button',{name:'Start guided walkthrough'}));
  expect(screen.getByRole('heading',{name:'1. Inspect experiment'})).toBeVisible();
  await user.click(screen.getByRole('button',{name:'Return to workbench'}));
  expect(screen.getByLabelText('Inspect sample')).toHaveValue('day-7');
});

it('explains a prepared culture without samples instead of showing another culture data', async () => {
  const user = userEvent.setup();
  const prepared = snapshotsSchema.parse([structuredClone(snapshot)])[0];
  prepared.experiment.cultures.push({id:'unsampled',name:'Not yet sampled',treatments:[]});
  render(<Workbench snapshots={snapshotsSchema.parse([prepared])}/>);
  await user.selectOptions(screen.getByLabelText('Culture'), 'unsampled');
  expect(screen.getByText('No samples in this culture.')).toBeVisible();
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
});

it('switches prepared snapshot, culture and scope together without leaking observations or cell states', async () => {
  const user = userEvent.setup();
  const prepared = snapshotsSchema.parse([structuredClone(snapshot)])[0];
  prepared.id = 'a'.repeat(64);
  prepared.experiment.id = 'unrelated';
  prepared.experiment.name = 'Prepared independent study';
  prepared.experiment.synthetic = false;
  prepared.experiment.cultures = [
    {id:'c1',name:'Prepared culture',treatments:[]},
    {id:'c2',name:'Separate culture',treatments:[]},
  ];
  const first = {id:'p1',culture_id:'c1',scope:'whole',time:2,counts:{A:1,__unknown__:3},cell_state_summary:'Descriptive stress program'};
  const sorted = {id:'p2',culture_id:'c1',scope:'sorted fraction',time:5,counts:{A:3,__unknown__:1},cell_state_summary:null};
  const other = {id:'p3',culture_id:'c2',scope:'whole',time:8,counts:{A:2,__unknown__:2},cell_state_summary:null};
  // Explicit backend-like observations, not a second frontend composition calculation.
  prepared.experiment.samples = [first,sorted,other];
  prepared.observations = [
    {sample:first,total:4,proportions:{A:.25,__unknown__:.75}},
    {sample:sorted,total:4,proportions:{A:.75,__unknown__:.25}},
    {sample:other,total:4,proportions:{A:.5,__unknown__:.5}},
  ];
  render(<Workbench snapshots={snapshotsSchema.parse([snapshot,prepared])}/>);
  await user.selectOptions(screen.getByLabelText('Inspect sample'),'day-7');
  await user.selectOptions(screen.getByLabelText('Experiment snapshot'),prepared.id);
  expect(screen.getByRole('heading',{name:'Prepared independent study'})).toBeVisible();
  expect(screen.getByLabelText('Culture')).toHaveValue('c1');
  expect(screen.getByLabelText('Sampling scope')).toHaveValue('whole');
  expect(screen.getByLabelText('Inspect sample')).toHaveValue('p1');
  expect(screen.getByText('Descriptive cell-state information')).toBeVisible();
  expect(screen.getByText('Cell state is separate from lineage identity.')).toBeVisible();
  expect(screen.getByRole('cell',{name:'25.0%'})).toBeVisible();
  await user.selectOptions(screen.getByLabelText('Sampling scope'),'sorted fraction');
  expect(screen.getByLabelText('Inspect sample')).toHaveValue('p2');
  expect(screen.queryByText('Descriptive stress program')).not.toBeInTheDocument();
  await user.selectOptions(screen.getByLabelText('Culture'),'c2');
  expect(screen.getByLabelText('Sampling scope')).toHaveValue('whole');
  expect(screen.getByLabelText('Inspect sample')).toHaveValue('p3');
  expect(screen.getAllByRole('cell',{name:'50.0%'})).toHaveLength(2);
  await user.selectOptions(screen.getByLabelText('Experiment snapshot'),snapshot.id);
  expect(screen.getByLabelText('Inspect sample')).toHaveValue('day-0');
  expect(screen.getByRole('cell',{name:'40.0%'})).toBeVisible();
});

it('explains CLI initialization/import when no prepared snapshots exist', () => {
  render(<Workbench snapshots={[]}/>);
  expect(screen.getByText('No experiment snapshots yet.')).toBeVisible();
  expect(screen.getByText(/import a prepared local folder through the CLI/)).toBeVisible();
});
