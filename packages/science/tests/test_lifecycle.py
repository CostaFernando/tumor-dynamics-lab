import pytest
from tumor_dynamics.demo import setup_demo
from tumor_dynamics.forecasting import RunConfiguration
from tumor_dynamics.runs import RunRepository
from tumor_dynamics.storage import Store
from tumor_dynamics.worker import process_next


def queued_attempt(tmp_path):
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    repository = RunRepository(store)
    configuration = RunConfiguration(snapshot_id=snapshot.id, culture_id='culture-01', scope='whole culture', cutoff=7, targets=[14])
    return store, repository, repository.enqueue(configuration)


def test_queued_cancel_survives_restart_and_retry_has_new_identity(tmp_path):
    store, repository, original = queued_attempt(tmp_path)
    cancelled = repository.cancel(original.id)
    assert cancelled.status == 'cancelled'
    assert cancelled.result is None
    assert process_next(store) is None
    reopened = RunRepository(Store(tmp_path))
    assert reopened.get(original.id) == cancelled
    retry = reopened.retry(original.id)
    assert retry.id != original.id
    assert retry.configuration == original.configuration
    assert retry.status == 'queued'
    assert reopened.get(original.id) == cancelled
    assert process_next(store) == retry.id
    assert reopened.get(retry.id).status == 'succeeded'
    with pytest.raises(ValueError, match='failed or cancelled'):
        reopened.retry(retry.id)


def test_running_cancel_wins_before_publication_and_completion_wins_after(tmp_path):
    from tumor_dynamics.worker import Worker
    store, repository, original = queued_attempt(tmp_path)
    with Worker(store) as worker:
        assert worker.process_next(before_complete=lambda run: repository.cancel(run.id)) == original.id
        cancelled = repository.get(original.id)
        assert cancelled.status == 'cancelled'
        assert cancelled.result is None
        retry = repository.retry(original.id)
        assert worker.process_next() == retry.id
        succeeded = repository.get(retry.id)
        assert succeeded.status == 'succeeded'
        assert repository.cancel(retry.id) == succeeded
        assert repository.cancel(original.id) == cancelled


def test_only_worker_owner_recovers_interrupted_attempts(tmp_path):
    from tumor_dynamics.worker import Worker
    store, repository, original = queued_attempt(tmp_path)
    # A previous worker claimed this run, then disappeared before finalization.
    assert repository.claim().id == original.id
    with Worker(store) as first:
        interrupted = repository.get(original.id)
        assert interrupted.status == 'failed'
        assert 'interrupted' in interrupted.error.lower()
        retry = repository.retry(original.id)
        def second_worker_must_not_recover(run):
            with pytest.raises(RuntimeError, match='already running'):
                with Worker(Store(tmp_path)):
                    pass
            assert repository.get(run.id).status == 'running'
        assert first.process_next(before_complete=second_worker_must_not_recover) == retry.id
        assert repository.get(retry.id).status == 'succeeded'


def test_abrupt_worker_death_releases_ownership_and_preserves_other_attempts(tmp_path):
    import os
    import select
    import subprocess
    import sys
    store, repository, original = queued_attempt(tmp_path)
    second = repository.enqueue(original.configuration)
    code = '''
from tumor_dynamics.storage import Store
from tumor_dynamics.worker import Worker
import sys
with Worker(Store()) as worker:
    worker.process_next(before_complete=lambda run: (print(run.id, flush=True), sys.stdin.read()))
'''
    child = subprocess.Popen([sys.executable, '-c', code], env={**os.environ, 'TDL_DATA_DIR':str(tmp_path)}, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        ready, _, _ = select.select([child.stdout], [], [], 10)
        assert ready, 'Worker failed to reach deterministic completion checkpoint'
        assert child.stdout.readline().strip() == original.id
        assert repository.get(original.id).status == 'running'
        competing = subprocess.run([sys.executable, '-m', 'tumor_dynamics.cli', 'worker', '--once'], env={**os.environ, 'TDL_DATA_DIR':str(tmp_path)}, capture_output=True, text=True, timeout=10)
        assert competing.returncode == 1
        assert 'already running' in competing.stderr
        assert repository.get(original.id).status == 'running'
        child.kill()
        child.wait(timeout=10)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
        child.stdin.close()
        child.stdout.close()
        child.stderr.close()
    assert process_next(Store(tmp_path)) == second.id
    interrupted = repository.get(original.id)
    assert interrupted.status == 'failed'
    assert 'interrupted' in interrupted.error.lower()
    assert interrupted.result is None
    completed = repository.get(second.id)
    assert completed.status == 'succeeded'
    retry = repository.retry(original.id)
    assert retry.id not in {original.id, second.id}
    assert retry.configuration == original.configuration
    assert process_next(Store(tmp_path)) == retry.id
    assert RunRepository(Store(tmp_path)).get(second.id) == completed
