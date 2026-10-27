import pytest
from tumor_dynamics.forecasting import PredictorInput, predict_last_observed
from tumor_dynamics.models import Sample
from tumor_dynamics.evaluation import evaluate_forecast


def sample(time, counts, **changes):
    return Sample(id=f's-{time}',culture_id='culture',scope='whole culture',time=time,counts=counts,**changes)


def test_evaluation_aligns_unseen_lineages_without_mutating_prediction():
    inputs = PredictorInput(observations=[sample(0,{'A':40,'B':30,'C':20,'__unknown__':10}),sample(7,{'A':25,'B':60,'C':0,'__unknown__':15})],cutoff=7,targets=[14,21])
    forecast = predict_last_observed(inputs)
    original = forecast.model_dump_json()
    observations = [sample(14,{'A':15,'B':55,'C':10,'D':10,'__unknown__':10}),sample(21,{'A':25,'B':60,'__unknown__':15})]
    results = evaluate_forecast(forecast,observations)
    first = results[0]
    assert first.time == 14
    assert first.total_variation_distance == pytest.approx(.2)
    assert first.previously_unseen_share == pytest.approx(.1)
    assert first.observed_total == 100
    rows = {row.category:row for row in first.categories}
    assert rows['D'].predicted_proportion == 0
    assert rows['D'].previously_unseen is True
    assert rows['D'].difference_percentage_points == pytest.approx(-10)
    assert rows['C'].previously_unseen is False
    assert rows['__unknown__'].previously_unseen is False
    assert rows['__unknown__'].observed_count == 10
    assert rows['__unknown__'].observed_proportion == .1
    assert rows['A'].difference_percentage_points == pytest.approx(10)
    assert results[1].time == 21
    assert results[1].total_variation_distance == 0
    assert results[1].previously_unseen_share == 0
    assert forecast.model_dump_json() == original


@pytest.mark.parametrize('change',[{'scope':'selected fraction'},{'culture_id':'other culture'},{'time':15}])
def test_evaluation_rejects_incomparable_or_unrequested_observations(change):
    from pydantic import ValidationError
    inputs = PredictorInput(observations=[sample(7,{'A':9,'__unknown__':1})],cutoff=7,targets=[14])
    forecast = predict_last_observed(inputs)
    target = sample(14,{'A':5,'__unknown__':5}).model_copy(update=change)
    with pytest.raises((ValueError,ValidationError),match='scope|culture|target'):
        evaluate_forecast(forecast,[target])


def test_evaluation_rejects_duplicate_targets_and_invalid_prediction_composition():
    inputs = PredictorInput(observations=[sample(7,{'A':9,'__unknown__':1})],cutoff=7,targets=[14])
    forecast = predict_last_observed(inputs)
    target = sample(14,{'A':5,'__unknown__':5})
    with pytest.raises(ValueError,match='Duplicate'):
        evaluate_forecast(forecast,[target,target])
    forecast.predictions[0].proportions = {'A':.5,'__unknown__':.1}
    with pytest.raises(ValueError,match='normalized'):
        evaluate_forecast(forecast,[target])


def test_worker_persists_evaluation_with_immutable_saved_prediction(tmp_path):
    from tumor_dynamics.demo import setup_demo
    from tumor_dynamics.storage import Store
    from tumor_dynamics.runs import RunRepository
    from tumor_dynamics.forecasting import RunConfiguration
    from tumor_dynamics.worker import process_next
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    request = RunConfiguration(snapshot_id=snapshot.id,culture_id='culture-01',scope='whole culture',cutoff=7,targets=[14,21])
    run = RunRepository(store).enqueue(request)
    process_next(Store(tmp_path))
    saved = RunRepository(Store(tmp_path)).get(run.id)
    assert saved.status == 'succeeded'
    assert saved.result.evaluations[0].total_variation_distance == pytest.approx(.2)
    assert saved.result.evaluations[1].total_variation_distance == pytest.approx(.35)
    assert 'D' not in saved.result.predictions[0].proportions
    evidence_bytes = (tmp_path/'runs'/f'{run.id}.json').read_bytes()
    assert RunRepository(Store(tmp_path)).get(run.id) == saved
    assert (tmp_path/'runs'/f'{run.id}.json').read_bytes() == evidence_bytes
