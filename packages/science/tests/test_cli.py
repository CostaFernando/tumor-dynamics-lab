import json
import os
import subprocess
import sys


def test_cli_demo_is_idempotent_and_inspectable(tmp_path):
    env = dict(os.environ, TDL_DATA_DIR=str(tmp_path))
    def run(*args):
        return subprocess.run([sys.executable, '-m', 'tumor_dynamics.cli', *args], env=env, text=True, capture_output=True, check=True)
    first = json.loads(run('demo').stdout)
    second = json.loads(run('demo').stdout)
    assert first['snapshot_id'] == second['snapshot_id']
    inspected = json.loads(run('inspect', first['snapshot_id']).stdout)
    assert inspected['experiment']['synthetic'] is True
    assert inspected['observations'][0]['proportions']['__unknown__'] == 0.1
