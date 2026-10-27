"""Forecast boundary: predictors receive only cutoff-bounded observations."""
from typing import Literal
from pydantic import Field, model_validator
from .models import Model, Identifier, Experiment, Sample, UNKNOWN_ANCESTRY
from .composition import composition
from .evaluation_models import TargetEvaluation


class RunConfiguration(Model):
    snapshot_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    culture_id: Identifier
    scope: Identifier
    cutoff: float
    targets: list[float] = Field(min_length=1)
    method: Literal['last_observed', 'damped_trend'] = 'last_observed'


class PredictorInput(Model):
    observations: list[Sample] = Field(min_length=1)
    cutoff: float
    targets: list[float] = Field(min_length=1)

    @model_validator(mode='after')
    def input_boundary(self):
        if any(s.time > self.cutoff for s in self.observations):
            raise ValueError('Predictor observations must not exceed cutoff')
        if max(s.time for s in self.observations) != self.cutoff:
            raise ValueError('Predictor cutoff must be an observed time')
        if len({(s.culture_id,s.scope) for s in self.observations}) != 1:
            raise ValueError('Predictor observations require one culture and comparable sampling scope')
        if len({s.time for s in self.observations}) != len(self.observations):
            raise ValueError('Predictor requires distinct sampling times')
        if any(t <= self.cutoff for t in self.targets):
            raise ValueError('Targets must be strictly after cutoff')
        if len(set(self.targets)) != len(self.targets):
            raise ValueError('Duplicate target times')
        return self


class TargetPrediction(Model):
    time: float
    proportions: dict[str, float]


class ForecastResult(Model):
    input_categories: list[str]
    input_observations: list[Sample]
    predictions: list[TargetPrediction]
    evaluations: list[TargetEvaluation] = Field(default_factory=list)


def prepare_forecast(experiment: Experiment, configuration: RunConfiguration) -> PredictorInput:
    if configuration.culture_id not in {c.id for c in experiment.cultures}:
        raise ValueError('Choose an existing culture')
    selected = sorted((s for s in experiment.samples if s.culture_id == configuration.culture_id and s.scope == configuration.scope), key=lambda s:s.time)
    if not selected:
        raise ValueError('No observations in the selected culture/scope; comparable sampling scope is required')
    if configuration.cutoff not in {s.time for s in selected}:
        raise ValueError('Cutoff must be an observed time in the selected culture/scope')
    if any(t not in {s.time for s in selected} for t in configuration.targets):
        raise ValueError('Targets must be measured times in the selected culture/scope')
    inputs = PredictorInput(observations=[s for s in selected if s.time <= configuration.cutoff], cutoff=configuration.cutoff, targets=configuration.targets)
    if configuration.method == 'damped_trend' and len(inputs.observations) < 2:
        raise ValueError('Damped trend requires at least two distinct input sampling times')
    return inputs


def _input_history(inputs: PredictorInput) -> tuple[list[Sample], list[str]]:
    observations = sorted(inputs.observations, key=lambda sample: sample.time)
    categories = sorted({category for sample in observations for category, count in sample.counts.items() if count > 0} | {UNKNOWN_ANCESTRY})
    return observations, categories


def predict_last_observed(inputs: PredictorInput) -> ForecastResult:
    observations, categories = _input_history(inputs)
    latest = composition(observations[-1])
    proportions = {category:latest.proportions.get(category,0.0) for category in categories}
    return ForecastResult(input_categories=categories, input_observations=observations,
        predictions=[TargetPrediction(time=time,proportions=proportions) for time in inputs.targets])


class Eligibility(Model):
    available: bool
    reason: str | None = None


def eligibility(experiment: Experiment, configuration: RunConfiguration) -> Eligibility:
    try:
        prepare_forecast(experiment, configuration)
    except ValueError as error:
        return Eligibility(available=False, reason=str(error))
    return Eligibility(available=True)


def predict_damped_trend(inputs: PredictorInput) -> ForecastResult:
    """Fixed-alpha centered-log trend with bounded exponential damping."""
    import math
    observations, categories = _input_history(inputs)
    if len(observations) < 2:
        raise ValueError('Damped trend requires at least two distinct input sampling times')
    earlier, latest = observations[-2:]
    def centered_log(sample: Sample) -> list[float]:
        counts = [sample.counts.get(category, 0) + 0.5 for category in categories]
        total = sum(counts)
        logs = [math.log(count / total) for count in counts]
        mean = math.fsum(logs) / len(logs)
        return [value - mean for value in logs]
    z0, z1 = centered_log(earlier), centered_log(latest)
    delta = latest.time - earlier.time
    predictions = []
    for target in inputs.targets:
        damping = -math.expm1(-(target - latest.time) / delta)
        logits = [current + damping * (current - previous) for previous, current in zip(z0, z1, strict=True)]
        largest = max(logits)
        weights = [math.exp(value - largest) for value in logits]
        total = math.fsum(weights)
        predictions.append(TargetPrediction(time=target, proportions=dict(zip(categories, (weight / total for weight in weights), strict=True))))
    return ForecastResult(input_categories=categories, input_observations=observations, predictions=predictions)
