import csv
import io
import json
import zipfile

from tumor_dynamics.demo import setup_demo
from tumor_dynamics.forecasting import RunConfiguration
from tumor_dynamics.runs import RunRepository
from tumor_dynamics.storage import Store
from tumor_dynamics.worker import process_next
from tumor_dynamics.exports import ExportRequest, export_evidence


def test_export_preserves_saved_predictions_comparisons_and_provenance(tmp_path):
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    repository = RunRepository(store)
    run = repository.enqueue(RunConfiguration(snapshot_id=snapshot.id, culture_id='culture-01', scope='whole culture', cutoff=7, targets=[14, 21]))
    process_next(store)
    saved = repository.get(run.id)
    bundle = export_evidence(store, ExportRequest(run_id=run.id))
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['run_id'] == run.id
        assert manifest['input_snapshot']['id'] == snapshot.id
        assert manifest['input_snapshot']['managed_relative_path'] == f'snapshots/{snapshot.id}.json'
        assert manifest['synthetic'] is True
        assert manifest['source_dataset_included'] is False
        assert manifest['deterministic'] is True
        assert manifest['random_seeds'] is None
        assert manifest['method_version'] == 'last-observed-v1'
        assert manifest['software_version'] == saved.software_version
        assert manifest['settings'] == {'smoothing': False}
        assert manifest['time_unit'] == 'days'
        assert json.loads(archive.read('configuration.json')) == saved.configuration.model_dump(mode='json')
        assert json.loads(archive.read('predictions.json')) == [prediction.model_dump(mode='json') for prediction in saved.result.predictions]
        comparisons = list(csv.DictReader(io.StringIO(archive.read('comparisons.csv').decode())))
        unseen = next(row for row in comparisons if row['time'] == '14.0' and row['category'] == 'D')
        assert unseen['predicted_proportion'] == '0.0'
        assert unseen['observed_count'] == '10'
        assert unseen['previously_unseen'] == 'True'
        assert any(row['category'] == '__unknown__' and row['observed_total'] == '100' for row in comparisons)
        scores = list(csv.DictReader(io.StringIO(archive.read('scores.csv').decode())))
        assert float(scores[0]['total_variation_distance']) == .2
        assert float(scores[0]['previously_unseen_share']) == .1
        assert 'access to the identified managed input snapshot' in archive.read('README.txt').decode()
        assert not any(name.startswith('snapshots/') or name == 'input_observations.json' for name in archive.namelist())
    assert export_evidence(Store(tmp_path), ExportRequest(run_id=run.id)) == bundle
    assert RunRepository(Store(tmp_path)).get(run.id) == saved


def test_export_rejects_legacy_success_without_complete_saved_evaluation(tmp_path):
    import pytest
    from tumor_dynamics.forecasting import prepare_forecast, predict_last_observed
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    repository = RunRepository(store)
    configuration = RunConfiguration(snapshot_id=snapshot.id, culture_id='culture-01', scope='whole culture', cutoff=7, targets=[14])
    run = repository.enqueue(configuration)
    repository.claim()
    # A public completion with predictions only represents a pre-evaluation saved attempt.
    repository.complete(run.id, predict_last_observed(prepare_forecast(snapshot.experiment, configuration)))
    with pytest.raises(ValueError, match='no complete recorded evaluation'):
        export_evidence(store, ExportRequest(run_id=run.id))
