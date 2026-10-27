import { expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EvidenceView } from './evidence-view';
import { runRecordSchema, snapshotSchema } from '../lib/validation';
import fixture from '../test-fixtures/evaluated-run.json';
import snapshotFixture from '../test-fixtures/snapshot.json';

it('selects one saved target and labels unseen lineage separately from unknown ancestry', async()=>{
 const user = userEvent.setup();
 render(<EvidenceView run={runRecordSchema.parse(fixture)} snapshot={snapshotSchema.parse(snapshotFixture)}/>);
 const evidence = screen.getByRole('region',{name:'Saved held-out evidence'});
 expect(within(evidence).getByText('0.200')).toBeVisible();
 expect(within(screen.getByLabelText('Previously unseen lineage share')).getByText('10.0%')).toBeVisible();
 const table = within(evidence).getByRole('table',{name:'Per-category held-out comparison'});
 const unseen = within(table).getByRole('row',{name:/Lineage D.*Previously unseen/});
 expect(within(unseen).getByText('−10.0 pp')).toBeVisible();
 expect(within(table).getByRole('row',{name:/Unknown ancestry/})).toBeVisible();
 await user.selectOptions(within(evidence).getByLabelText('Evidence target time'),'21');
 expect(within(evidence).getByText('0.350')).toBeVisible();
 expect(within(screen.getByLabelText('Previously unseen lineage share')).getByText('15.0%')).toBeVisible();
 expect(within(evidence).getByText('Observed sample day-21 · total 100 cells')).toBeVisible();
});

it('keeps full scores and denominators when the display table is filtered',async()=>{
 const user = userEvent.setup();
 render(<EvidenceView run={runRecordSchema.parse(fixture)} snapshot={snapshotSchema.parse(snapshotFixture)}/>);
 await user.click(screen.getByLabelText('Show only previously unseen lineages in table'));
 const table = screen.getByRole('table',{name:'Per-category held-out comparison'});
 expect(within(table).queryByText('Unknown ancestry')).not.toBeInTheDocument();
 expect(within(table).getByText('10 / 100')).toBeVisible();
 expect(screen.getByText('0.200')).toBeVisible();
 expect(within(screen.getByLabelText('Previously unseen lineage share')).getByText('10.0%')).toBeVisible();
 expect(screen.getByRole('img',{name:'Forecast composition'})).toBeVisible();
});
