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
