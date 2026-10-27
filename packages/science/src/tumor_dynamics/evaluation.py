"""Held-out evaluation is separate from prediction and never edits it."""
import math
from pydantic import Field, model_validator
from .composition import composition
from .evaluation_models import CategoryComparison, TargetEvaluation
from .forecasting import ForecastResult
from .models import Model, Sample, UNKNOWN_ANCESTRY


class EvaluationInput(Model):
    forecast: ForecastResult
    observations: list[Sample] = Field(min_length=1)

    @model_validator(mode='after')
    def comparable_targets(self):
        inputs = self.forecast.input_observations
        if not inputs or len({(sample.culture_id,sample.scope) for sample in inputs}) != 1:
            raise ValueError('Evaluation requires one input culture and sampling scope')
        context = (inputs[0].culture_id,inputs[0].scope)
        if any((sample.culture_id,sample.scope) != context for sample in self.observations):
            raise ValueError('Evaluation observations must have the same culture and sampling scope as inputs')
        times = [sample.time for sample in self.observations]
        predicted_times = [prediction.time for prediction in self.forecast.predictions]
        if len(set(times)) != len(times) or len(set(predicted_times)) != len(predicted_times):
            raise ValueError('Duplicate evaluation target times')
        if set(times) != set(predicted_times) or any(time <= max(sample.time for sample in inputs) for time in times):
            raise ValueError('Evaluation observations must match the later forecast target times')
        for prediction in self.forecast.predictions:
            values = list(prediction.proportions.values())
            if not values or any(not math.isfinite(value) or not 0 <= value <= 1 for value in values) or not math.isclose(sum(values),1,abs_tol=1e-9):
                raise ValueError('Evaluation requires finite normalized prediction proportions')
        return self


def evaluate_forecast(forecast: ForecastResult, observations: list[Sample]) -> list[TargetEvaluation]:
    request = EvaluationInput(forecast=forecast,observations=observations)
    by_time = {sample.time:sample for sample in request.observations}
    results = []
    for prediction in forecast.predictions:
        sample = by_time[prediction.time]
        observed = composition(sample)
        categories = sorted(set(forecast.input_categories) | set(prediction.proportions) | set(sample.counts) | {UNKNOWN_ANCESTRY})
        rows = []
        for category in categories:
            predicted = prediction.proportions.get(category,0.0)
            actual = observed.proportions.get(category,0.0)
            rows.append(CategoryComparison(category=category,predicted_proportion=predicted,
                observed_proportion=actual,observed_count=sample.counts.get(category,0),
                difference_percentage_points=100*(predicted-actual),
                previously_unseen=category != UNKNOWN_ANCESTRY and category not in forecast.input_categories and sample.counts.get(category,0)>0))
        results.append(TargetEvaluation(time=prediction.time,sample_id=sample.id,observed_total=observed.total,
            total_variation_distance=.5*sum(abs(row.predicted_proportion-row.observed_proportion) for row in rows),
            previously_unseen_share=sum(row.observed_proportion for row in rows if row.previously_unseen),categories=rows))
    return results
