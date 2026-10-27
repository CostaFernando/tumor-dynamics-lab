"""Prepared-folder behavior tested through the public importer and snapshot API."""
import json
import pytest

from tumor_dynamics.demo import demo_experiment
from tumor_dynamics.prepared import import_prepared
from tumor_dynamics.storage import Store


def write_prepared(folder, data):
    folder.mkdir(exist_ok=True)
    (folder / 'experiment.json').write_text(json.dumps(data))
    return folder


def test_import_copies_valid_prepared_experiment_with_unknown_ancestry(tmp_path):
    data = demo_experiment().model_dump(mode='json')
    data.update(id='prepared-study', name='Prepared study', synthetic=False)
    folder = write_prepared(tmp_path / 'source', data)
    store = Store(tmp_path / 'managed')
    snapshot = import_prepared(folder, store)
    assert snapshot.experiment.id == 'prepared-study'
    assert snapshot.observations[0].total == 100
    assert snapshot.observations[0].proportions['__unknown__'] == 0.1
    assert import_prepared(folder, store).id == snapshot.id
    data['samples'][0]['counts']['A'] = 999
    write_prepared(folder, data)
    reopened = Store(tmp_path / 'managed').get_snapshot(snapshot.id)
    assert reopened.experiment.samples[0].counts['A'] == 40
    assert reopened.id == snapshot.id


def test_prepared_format_version_is_explicit_and_failed_import_is_not_usable(tmp_path):
    data = demo_experiment().model_dump(mode='json')
    del data['format_version']
    folder = write_prepared(tmp_path / 'source', data)
    store = Store(tmp_path / 'managed')
    with pytest.raises(ValueError, match='format_version'):
        import_prepared(folder, store)
    assert store.list_snapshots() == []


def test_duplicate_count_keys_are_rejected_instead_of_last_value_winning(tmp_path):
    data = demo_experiment().model_dump(mode='json')
    folder = write_prepared(tmp_path / 'source', data)
    path = folder / 'experiment.json'
    path.write_text(path.read_text().replace('"A": 40', '"A": 40, "A": 99'))
    store = Store(tmp_path / 'managed')
    with pytest.raises(ValueError, match='Duplicate JSON key.*A'):
        import_prepared(folder, store)
    assert store.list_snapshots() == []


@pytest.mark.parametrize(('change', 'message'), [
    (lambda d: d['samples'][0]['counts'].update(A=-1), 'greater than or equal'),
    (lambda d: d['samples'][0]['counts'].update(A=1.5), 'valid integer'),
    (lambda d: d['samples'][0]['counts'].update(A=True), 'valid integer'),
    (lambda d: d['samples'][0]['counts'].update(A='40'), 'valid integer'),
    (lambda d: d['samples'][0].update(culture_id='missing'), 'unresolved culture'),
    (lambda d: d['samples'].append(d['samples'][0].copy()), 'Duplicate sample identifier'),
    (lambda d: d['cultures'].append(d['cultures'][0].copy()), 'Duplicate culture identifier'),
    (lambda d: d['samples'][1].update(time=0), 'Multiple samples'),
    (lambda d: d['samples'][0].update(counts={'A': 0, '__unknown__': 0}), 'greater than zero'),
    (lambda d: d['samples'][0].update(counts={'A': 10}), 'explicit __unknown__'),
    (lambda d: d.update(time_unit='day'), 'time_unit'),
    (lambda d: d.update(format_version='2'), 'format_version'),
    (lambda d: d['samples'][0].update(time=float('nan')), 'finite number'),
    (lambda d: d['samples'][0].update(time=float('inf')), 'finite number'),
    (lambda d: d['cultures'][0]['treatments'][0].update(end=-1), 'end must be after start'),
])
def test_invalid_imports_leave_no_usable_partial_snapshot(tmp_path, change, message):
    data = demo_experiment().model_dump(mode='json')
    change(data)
    folder = write_prepared(tmp_path / 'source', data)
    store = Store(tmp_path / 'managed')
    with pytest.raises(ValueError, match=message):
        import_prepared(folder, store)
    assert Store(tmp_path / 'managed').list_snapshots() == []


def test_lineage_labels_and_cell_states_remain_scoped_to_each_experiment(tmp_path):
    store = Store(tmp_path / 'managed')
    first = demo_experiment().model_dump(mode='json')
    first['samples'][0]['cell_state_summary'] = 'Descriptive stress response; not a lineage identity.'
    a = import_prepared(write_prepared(tmp_path / 'one', first), store)
    second = demo_experiment().model_dump(mode='json')
    second['id'] = 'unrelated-experiment'
    second['samples'][0]['counts'] = {'A': 1, '__unknown__': 3}
    b = import_prepared(write_prepared(tmp_path / 'two', second), store)
    assert a.id != b.id
    assert store.get_snapshot(a.id).observations[0].proportions['A'] == 0.4
    assert store.get_snapshot(b.id).observations[0].proportions['A'] == 0.25
    assert store.get_snapshot(a.id).experiment.samples[0].cell_state_summary.startswith('Descriptive stress')
    assert store.get_snapshot(b.id).experiment.samples[0].cell_state_summary is None
