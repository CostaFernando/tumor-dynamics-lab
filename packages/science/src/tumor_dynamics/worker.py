"""A separate CPU worker; browser lifetime has no role in execution."""
from .forecasting import prepare_forecast, predict_last_observed
from .runs import RunRepository
from .storage import Store


def process_next(store: Store) -> str | None:
    repository = RunRepository(store)
    run = repository.claim()
    if run is None:
        return None
    try:
        snapshot = store.get_snapshot(run.configuration.snapshot_id)
        inputs = prepare_forecast(snapshot.experiment, run.configuration)
        result = predict_last_observed(inputs)
        repository.complete(run.id, result)
    except Exception as error:
        repository.fail(run.id, str(error))
    return run.id
