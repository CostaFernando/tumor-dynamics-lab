"""Release seam: exercise installed CLI, real HTTP API, worker and evidence bundle."""
import json
from pathlib import Path
import subprocess
import sys


def test_prepared_experiment_completes_both_baselines_through_release_command():
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run([sys.executable, str(root / 'scripts' / 'verify_release.py')], cwd=root,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['methods'] == ['last_observed', 'damped_trend']
    assert report['successful_exports'] == 2
    assert report['retry_preserved_original'] is True
