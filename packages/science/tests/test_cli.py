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


def test_cli_import_exposes_valid_snapshot_and_actionable_rejection(tmp_path):
    from tumor_dynamics.demo import demo_experiment
    source = tmp_path / 'prepared'
    source.mkdir()
    data = demo_experiment().model_dump(mode='json')
    path = source / 'experiment.json'
    path.write_text(json.dumps(data))
    env = dict(os.environ, TDL_DATA_DIR=str(tmp_path / 'managed'))
    def run(*args):
        return subprocess.run([sys.executable, '-m', 'tumor_dynamics.cli', *args], env=env, text=True, capture_output=True)
    imported = run('import', str(source))
    assert imported.returncode == 0, imported.stderr
    identity = json.loads(imported.stdout)['snapshot_id']
    assert json.loads(run('inspect', identity).stdout)['experiment']['id'] == data['id']
    data['samples'][0]['counts']['A'] = -1
    path.write_text(json.dumps(data))
    rejected = run('import', str(source))
    assert rejected.returncode == 1
    assert 'samples.0.counts.A' in rejected.stderr
    assert 'greater than or equal to 0' in rejected.stderr
