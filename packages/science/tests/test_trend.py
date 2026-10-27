import math
import pytest
from tumor_dynamics.models import Sample
from tumor_dynamics.forecasting import PredictorInput


def sample(time, counts):
    return Sample(id=f's-{time}', culture_id='culture', scope='whole', time=time, counts=counts)


def test_damped_trend_matches_hand_checked_odds_at_half_damping():
    from tumor_dynamics.forecasting import predict_damped_trend
    inputs = PredictorInput(observations=[sample(0, {'A':1,'__unknown__':0}), sample(1, {'A':0,'__unknown__':1})], cutoff=1, targets=[1+math.log(2)])
    prediction = predict_damped_trend(inputs).predictions[0]
    # Smoothed odds move 3 -> 1/3; half an interval's log-odds trend yields 1/9.
    assert prediction.proportions == pytest.approx({'A':.1,'__unknown__':.9})


def test_trend_unavailable_with_one_input_and_does_not_fall_back():
    from tumor_dynamics.demo import demo_experiment
    from tumor_dynamics.forecasting import RunConfiguration, eligibility, prepare_forecast
    configuration = RunConfiguration(snapshot_id='a'*64,culture_id='culture-01',scope='whole culture',cutoff=0,targets=[3],method='damped_trend')
    outcome = eligibility(demo_experiment(), configuration)
    assert outcome.available is False
    assert 'two distinct' in outcome.reason
    with pytest.raises(ValueError, match='two distinct'):
        prepare_forecast(demo_experiment(), configuration)
    assert configuration.method == 'damped_trend'


def test_trend_uses_last_interval_with_bounded_damping_and_smoothed_short_horizon():
    from tumor_dynamics.forecasting import predict_damped_trend
    inputs = PredictorInput(observations=[sample(-5, {'A':10,'__unknown__':10}), sample(0, {'A':1,'__unknown__':0}),sample(10, {'A':0,'__unknown__':1})],cutoff=10,targets=[10+1e-9,10+10*math.log(2),10000])
    result = predict_damped_trend(inputs)
    assert result.predictions[0].proportions['A'] == pytest.approx(.25,abs=1e-9)
    assert result.predictions[1].proportions['A'] == pytest.approx(.1)
    assert result.predictions[2].proportions['A'] == pytest.approx(1/28)
    assert predict_damped_trend(inputs) == result
    for prediction in result.predictions:
        assert all(math.isfinite(p) and p >= 0 for p in prediction.proportions.values())
        assert sum(prediction.proportions.values()) == pytest.approx(1)


def test_trend_retains_previously_observed_lineage_after_non_detection_and_ignores_future():
    from tumor_dynamics.demo import demo_experiment
    from tumor_dynamics.forecasting import RunConfiguration, prepare_forecast, predict_damped_trend
    experiment = demo_experiment()
    configuration = RunConfiguration(snapshot_id='a'*64,culture_id='culture-01',scope='whole culture',cutoff=7,targets=[14,21],method='damped_trend')
    result = predict_damped_trend(prepare_forecast(experiment,configuration))
    assert result.input_categories == ['A','B','C','__unknown__']
    assert all(p.proportions['C'] > 0 for p in result.predictions)
    for observation in experiment.samples:
        if observation.time > 7:
            observation.counts = {'FUTURE-IDENTITY':900,'__unknown__':100}
            observation.cell_state_summary = 'Future data must stay outside prediction'
    assert predict_damped_trend(prepare_forecast(experiment,configuration)) == result


def test_trend_runs_through_saved_queue_with_fixed_version_and_settings(tmp_path):
    from tumor_dynamics.demo import setup_demo
    from tumor_dynamics.storage import Store
    from tumor_dynamics.runs import RunRepository
    from tumor_dynamics.forecasting import RunConfiguration, predict_last_observed, prepare_forecast
    from tumor_dynamics.worker import process_next
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    configuration = RunConfiguration(snapshot_id=snapshot.id,culture_id='culture-01',scope='whole culture',cutoff=7,targets=[14,21],method='damped_trend')
    queued = RunRepository(store).enqueue(configuration)
    assert queued.method_version == 'damped-trend-v1'
    assert queued.settings == {'alpha':.5,'damping':'1-exp(-h/delta)'}
    assert process_next(store) == queued.id
    reopened = RunRepository(Store(tmp_path)).get(queued.id)
    assert reopened.status == 'succeeded'
    assert reopened.configuration == configuration
    assert reopened.deterministic is True
    assert reopened.crosses_withdrawal is True
    assert reopened.result != predict_last_observed(prepare_forecast(snapshot.experiment,configuration))
    assert RunRepository(store).get(queued.id) == reopened
