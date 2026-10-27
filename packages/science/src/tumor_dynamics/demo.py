"""Fixed fictional inputs, with no claim of biological validity."""
from .models import Culture, Experiment, Sample, Treatment
from .storage import Store


def demo_experiment() -> Experiment:
    counts = [
        {'A': 40, 'B': 30, 'C': 20, '__unknown__': 10},
        {'A': 50, 'B': 25, 'C': 15, '__unknown__': 10},
        {'A': 65, 'B': 25, 'C': 0, '__unknown__': 10},
        {'A': 45, 'B': 25, 'C': 10, 'D': 10, '__unknown__': 10},
        {'A': 30, 'B': 25, 'C': 20, 'D': 15, '__unknown__': 10},
    ]
    return Experiment(
        id='fictional-recovery-v1', name='Fictional recovery study', synthetic=True, time_unit='days',
        description='Fixed synthetic observations across exposure, withdrawal and recovery. Not SUM159PT biology.',
        acquisition='Original fictional counts authored for this demonstration.', redistribution='MIT; no external dataset.',
        cultures=[Culture(id='culture-01', name='Culture 01', treatments=[Treatment(name='Fictional treatment', start=0, end=10, dose='Illustrative dose')])],
        samples=[Sample(id=f'day-{time}', culture_id='culture-01', scope='whole culture', time=time, counts=count)
                 for time, count in zip([0, 3, 7, 14, 21], counts, strict=True)],
    )


def setup_demo(store: Store):
    return store.save_snapshot(demo_experiment())
