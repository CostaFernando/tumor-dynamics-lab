"""Persisted method-independent evidence; all numerical values are Python-owned."""
from pydantic import Field
from .models import Count, Identifier, Model


class CategoryComparison(Model):
    category: Identifier
    predicted_proportion: float = Field(ge=0, le=1)
    observed_proportion: float = Field(ge=0, le=1)
    observed_count: Count
    difference_percentage_points: float
    previously_unseen: bool


class TargetEvaluation(Model):
    time: float
    sample_id: Identifier
    observed_total: Count = Field(gt=0)
    total_variation_distance: float = Field(ge=0, le=1)
    previously_unseen_share: float = Field(ge=0, le=1)
    categories: list[CategoryComparison]
