from tumor_dynamics.demo import setup_demo
from tumor_dynamics.storage import Store
from tumor_dynamics.forecasting import RunConfiguration
from tumor_dynamics.runs import RunRepository
from tumor_dynamics.worker import process_next


def test_persistent_queue_runs_without_browser_and_reopens_exact_saved_results(tmp_path):
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    repository = RunRepository(store)
    request = RunConfiguration(snapshot_id=snapshot.id,culture_id='culture-01',scope='whole culture',cutoff=7,targets=[14,21])
    run = repository.enqueue(request)
    assert run.status == 'queued'
    assert run.method_version == 'last-observed-v1'
    assert run.settings == {'smoothing':False}
    assert run.crosses_withdrawal is True
    assert RunRepository(Store(tmp_path)).get(run.id) == run
    # A separately instantiated worker/store owns execution; there is no browser.
    assert process_next(Store(tmp_path)) == run.id
    saved = RunRepository(Store(tmp_path)).get(run.id)
    assert saved.status == 'succeeded'
    assert saved.result.predictions[0].proportions == {'A':.65,'B':.25,'C':0,'__unknown__':.1}
    assert process_next(Store(tmp_path)) is None
    assert RunRepository(Store(tmp_path)).get(run.id) == saved
    second = repository.enqueue(request)
    assert second.id != run.id
    assert repository.get(run.id) == saved
    assert len(repository.list()) == 2


def test_rejected_request_leaves_no_run_and_worker_failure_has_persisted_explanation(tmp_path):
    import pytest
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    repository = RunRepository(store)
    request = RunConfiguration(snapshot_id=snapshot.id,culture_id='culture-01',scope='selected fraction',cutoff=7,targets=[14])
    with pytest.raises(ValueError,match='scope'):
        repository.enqueue(request)
    assert repository.list() == []
    request.scope = 'whole culture'
    run = repository.enqueue(request)
    path = tmp_path/'snapshots'/f'{snapshot.id}.json'
    path.chmod(0o644)
    path.write_text('{}')
    assert process_next(Store(tmp_path)) == run.id
    failed = RunRepository(Store(tmp_path)).get(run.id)
    assert failed.status == 'failed'
    assert 'identity verification' in failed.error
    assert failed.result is None
