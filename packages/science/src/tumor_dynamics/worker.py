"""A separate CPU worker with exclusive local ownership and explicit recovery."""
from collections.abc import Callable
import fcntl
from .forecasting import prepare_forecast, predict_last_observed, predict_damped_trend
from .evaluation import evaluate_forecast
from .runs import RunRepository, RunRecord
from .storage import Store


class Worker:
    def __init__(self, store: Store):
        self.store = store
        self.repository = RunRepository(store)
        self._lock = None

    def __enter__(self):
        lock = (self.store.root / 'worker.lock').open('a')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            lock.close()
            raise RuntimeError('A worker is already running for this research storage') from error
        self._lock = lock
        try:
            self.repository.recover_interrupted()
        except BaseException:
            lock.close()
            self._lock = None
            raise
        return self

    def __exit__(self, *exc):
        if self._lock is not None:
            # Includes graceful interruption at an execution checkpoint.
            try:
                self.repository.recover_interrupted()
            finally:
                self._lock.close()
                self._lock = None

    def process_next(self, *, before_complete: Callable[[RunRecord], None] | None = None) -> str | None:
        """Execute one attempt; optional checkpoint supports deterministic integration controls."""
        if self._lock is None:
            raise RuntimeError('Use Worker as an ownership context before processing')
        repository = self.repository
        run = repository.claim()
        if run is None:
            return None
        try:
            snapshot = self.store.get_snapshot(run.configuration.snapshot_id)
            inputs = prepare_forecast(snapshot.experiment, run.configuration)
            predictor = predict_damped_trend if run.configuration.method == 'damped_trend' else predict_last_observed
            result = predictor(inputs)
            held_out = [sample for sample in snapshot.experiment.samples if sample.culture_id == run.configuration.culture_id and sample.scope == run.configuration.scope and sample.time in run.configuration.targets]
            result = result.model_copy(update={"evaluations":evaluate_forecast(result,held_out)})
            if before_complete is not None:
                before_complete(run)
            repository.complete(run.id, result)
        except Exception as error:
            repository.fail(run.id, str(error))
        return run.id


def process_next(store: Store) -> str | None:
    with Worker(store) as worker:
        return worker.process_next()
