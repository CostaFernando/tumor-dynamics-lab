from tumor_dynamics.models import Sample
from tumor_dynamics.composition import composition


def test_unknown_ancestry_stays_in_sample_denominator():
    sample = Sample(id='s1', culture_id='c1', scope='whole culture', time=0,
                    counts={'A': 6, 'B': 2, '__unknown__': 2})
    observation = composition(sample)
    assert observation.total == 10
    assert observation.proportions == {'A': 0.6, 'B': 0.2, '__unknown__': 0.2}
