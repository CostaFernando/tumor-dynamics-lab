from .models import Observation, Sample


def composition(sample: Sample) -> Observation:
    """Observed composition; unknown ancestry remains in the denominator."""
    total = sum(sample.counts.values())
    return Observation(sample=sample, total=total,
                       proportions={lineage: count / total for lineage, count in sample.counts.items()})
