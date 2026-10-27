"""A separate CPU worker; browser lifetime has no role in execution."""
from .forecasting import prepare_forecast, predict_last_observed, predict_damped_trend
from .evaluation import evaluate_forecast
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
        predictor = predict_damped_trend if run.configuration.method == 'damped_trend' else predict_last_observed
        result = predictor(inputs)
        held_out = [sample for sample in snapshot.experiment.samples if sample.culture_id == run.configuration.culture_id and sample.scope == run.configuration.scope and sample.time in run.configuration.targets]
        result = result.model_copy(update={"evaluations":evaluate_forecast(result,held_out)})
        repository.complete(run.id, result)
    except Exception as error:
        repository.fail(run.id, str(error))
    return run.id
