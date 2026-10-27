import pytest
from tumor_dynamics.demo import demo_experiment
from tumor_dynamics.forecasting import RunConfiguration, prepare_forecast, predict_last_observed


def config(**changes):
    return RunConfiguration(snapshot_id='a'*64, culture_id='culture-01', scope='whole culture', cutoff=7, targets=[14,21], **changes)


def test_last_observed_keeps_history_categories_unknown_denominator_and_no_future():
    experiment = demo_experiment()
    inputs = prepare_forecast(experiment, config())
    result = predict_last_observed(inputs)
    assert result.input_categories == ['A','B','C','__unknown__']
    assert [p.time for p in result.predictions] == [14,21]
    assert result.predictions[0].proportions == {'A':.65,'B':.25,'C':0,'__unknown__':.1}
    experiment.samples[-1].counts = {'FUTURE':900,'__unknown__':100}
    experiment.samples[-2].counts = {'OTHER':20,'__unknown__':80}
    assert predict_last_observed(prepare_forecast(experiment, config())) == result

@pytest.mark.parametrize('changes,reason', [
    ({'culture_id':'missing'},'culture'),
    ({'scope':'selected fraction'},'scope'),
    ({'cutoff':6},'observed'),
    ({'targets':[7]},'after'),
    ({'targets':[15]},'measured'),
    ({'targets':[14,14]},'Duplicate'),
])
def test_invalid_forecast_configuration_is_rejected(changes,reason):
    request = config().model_copy(update=changes)
    with pytest.raises(ValueError,match=reason):
        prepare_forecast(demo_experiment(),request)


def test_predictor_rejects_observations_beyond_cutoff_even_without_api():
    from tumor_dynamics.forecasting import PredictorInput
    with pytest.raises(ValueError,match='cutoff'):
        PredictorInput(observations=demo_experiment().samples,cutoff=7,targets=[14])
