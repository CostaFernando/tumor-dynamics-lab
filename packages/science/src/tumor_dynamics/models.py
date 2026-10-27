"""Shared strict input models for prepared data, CLI, API and worker."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

UNKNOWN_ANCESTRY = '__unknown__'
Identifier = Annotated[str, Field(min_length=1, max_length=200)]
Count = Annotated[StrictInt, Field(ge=0)]


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class Treatment(Model):
    name: Identifier
    start: float
    end: float
    dose: str | None = None

    @model_validator(mode='after')
    def ordered(self):
        if self.end <= self.start:
            raise ValueError('Treatment end must be after start')
        return self


class Culture(Model):
    id: Identifier
    name: Identifier
    treatments: list[Treatment] = Field(default_factory=list)


class Sample(Model):
    id: Identifier
    culture_id: Identifier
    scope: Identifier
    time: float
    counts: dict[Identifier, Count]
    cell_state_summary: str | None = None

    @model_validator(mode='after')
    def valid_counts(self):
        if UNKNOWN_ANCESTRY not in self.counts:
            raise ValueError('Each sample requires explicit __unknown__ ancestry count (zero allowed)')
        if sum(self.counts.values()) == 0:
            raise ValueError('Sample total must be greater than zero')
        return self


class Experiment(Model):
    format_version: Literal['1'] = '1'
    id: Identifier
    name: Identifier
    synthetic: bool
    time_unit: Literal['hours', 'days']
    description: str = ''
    acquisition: str = ''
    redistribution: str = ''
    cultures: list[Culture] = Field(min_length=1)
    samples: list[Sample] = Field(min_length=1)

    @model_validator(mode='after')
    def consistent_references(self):
        culture_ids = [c.id for c in self.cultures]
        if len(set(culture_ids)) != len(culture_ids):
            raise ValueError('Duplicate culture identifier')
        sample_ids = [s.id for s in self.samples]
        if len(set(sample_ids)) != len(sample_ids):
            raise ValueError('Duplicate sample identifier')
        seen = set()
        for sample in self.samples:
            if sample.culture_id not in culture_ids:
                raise ValueError(f'Sample {sample.id}: unresolved culture {sample.culture_id}')
            key = (sample.culture_id, sample.scope, sample.time)
            if key in seen:
                raise ValueError('Multiple samples at the same culture/scope/time; prepare technical replicates explicitly')
            seen.add(key)
        return self


class Observation(Model):
    sample: Sample
    total: int
    proportions: dict[str, float]


class Snapshot(Model):
    id: str
    experiment: Experiment
    observations: list[Observation]
