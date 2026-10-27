"""Measure fixed-demo scientific execution and process RSS; no acceptance thresholds."""
import json
import platform
import resource
import statistics
import sys
import tempfile
import time

from tumor_dynamics.demo import demo_experiment, setup_demo
from tumor_dynamics.evaluation import evaluate_forecast
from tumor_dynamics.forecasting import RunConfiguration, prepare_forecast, predict_last_observed, predict_damped_trend
from tumor_dynamics.storage import Store


def main():
    experiment = demo_experiment()
    with tempfile.TemporaryDirectory(prefix='tdl-benchmark-') as directory:
        snapshot = setup_demo(Store(directory))
        samples = []
        for _ in range(5):
            started = time.perf_counter()
            for method, predictor in [('last_observed', predict_last_observed), ('damped_trend', predict_damped_trend)]:
                configuration = RunConfiguration(snapshot_id=snapshot.id, culture_id='culture-01', scope='whole culture', cutoff=7, targets=[14, 21], method=method)
                result = predictor(prepare_forecast(experiment, configuration))
                evaluate_forecast(result, [sample for sample in experiment.samples if sample.time in configuration.targets])
            samples.append(time.perf_counter() - started)
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_bytes = rss if sys.platform == 'darwin' else rss * 1024
        print(json.dumps(dict(scope='scientific Python process; both predictors and two-target evaluation per sample',
            snapshot_id=snapshot.id, python=platform.python_version(), platform=platform.platform(),
            seconds=samples, median_seconds=statistics.median(samples), process_max_rss_mib=rss_bytes / 1024**2,
            memory_includes='imports, fixture and preparation; excludes API, frontend, browser and Docker VM',
            deterministic=True, thresholds=None), indent=2))


if __name__ == '__main__':
    main()
