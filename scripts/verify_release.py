"""Exercise the installed local release through CLI, HTTP API and a separate worker.

Uses only temporary fictional inputs/storage and localhost. Install dependencies first.
"""
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
import zipfile

from tumor_dynamics.demo import demo_experiment

ROOT = Path(__file__).resolve().parents[1]


def verify_release() -> dict:
    with tempfile.TemporaryDirectory(prefix='tdl-release-') as directory:
        temporary = Path(directory)
        source = temporary / 'prepared'
        source.mkdir()
        (source / 'experiment.json').write_text(demo_experiment().model_dump_json())
        environment = {**os.environ, 'TDL_DATA_DIR': str(temporary / 'storage')}

        def cli(*arguments):
            result = subprocess.run([sys.executable, '-m', 'tumor_dynamics.cli', *arguments],
                                    cwd=ROOT, env=environment, capture_output=True, text=True, timeout=15)
            if result.returncode:
                raise RuntimeError(result.stderr)
            return json.loads(result.stdout)

        snapshot_id = cli('import', str(source))['snapshot_id']
        # Mutating the prepared folder must not alter the managed input.
        changed = demo_experiment().model_dump(mode='json')
        changed['samples'][0]['counts']['A'] = 999
        (source / 'experiment.json').write_text(json.dumps(changed))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        base = f'http://127.0.0.1:{port}'

        def request(path, body=None, *, raw=False):
            payload = None if body is None else json.dumps(body).encode()
            req = Request(base + path, data=payload, headers={'Content-Type': 'application/json'})
            with urlopen(req, timeout=5) as response:
                data = response.read()
            return data if raw else json.loads(data)

        with tempfile.TemporaryFile() as log:
            api = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'tumor_api.app:app', '--host', '127.0.0.1', '--port', str(port)],
                                   cwd=ROOT, env=environment, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 15
                while True:
                    try:
                        snapshot = request(f'/snapshots/{snapshot_id}')
                        break
                    except URLError:
                        if api.poll() is not None or time.monotonic() >= deadline:
                            log.seek(0)
                            raise RuntimeError('Local API failed to start: ' + log.read().decode())
                        time.sleep(.05)
                assert snapshot['experiment']['samples'][0]['counts']['A'] == 40
                configuration = dict(snapshot_id=snapshot_id, culture_id='culture-01', scope='whole culture', cutoff=7.0, targets=[14.0, 21.0])
                methods = ['last_observed', 'damped_trend']
                exports = 0
                for method in methods:
                    run = request('/runs', {**configuration, 'method': method})
                    assert run['status'] == 'queued'
                    assert cli('worker', '--once')['processed_run'] == run['id']
                    saved = request('/runs/' + run['id'])
                    assert saved['status'] == 'succeeded'
                    evidence = saved['result']['evaluations'][0]
                    assert evidence['previously_unseen_share'] == .1
                    if method == 'last_observed':
                        assert abs(evidence['total_variation_distance'] - .2) < 1e-12
                    bundle = request('/runs/' + run['id'] + '/export', raw=True)
                    assert request('/runs/' + run['id'] + '/export', raw=True) == bundle
                    assert request('/runs/' + run['id']) == saved
                    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
                        manifest = json.loads(archive.read('manifest.json'))
                        assert manifest['input_snapshot']['id'] == snapshot_id
                        assert manifest['method'] == method and manifest['synthetic'] is True
                        assert json.loads(archive.read('evaluations.json')) == saved['result']['evaluations']
                    exports += 1
                cancelled = request('/runs', {**configuration, 'method': 'last_observed'})
                assert request('/runs/' + cancelled['id'] + '/cancel', {})['status'] == 'cancelled'
                retry = request('/runs/' + cancelled['id'] + '/retry', {})
                assert retry['id'] != cancelled['id']
                assert retry['configuration'] == cancelled['configuration']
                assert cli('worker', '--once')['processed_run'] == retry['id']
                assert request('/runs/' + retry['id'])['status'] == 'succeeded'
                assert request('/runs/' + cancelled['id'])['status'] == 'cancelled'
                return dict(snapshot_id=snapshot_id, methods=methods, successful_exports=exports,
                            retry_preserved_original=True, source_snapshot_immutable=True)
            finally:
                api.terminate()
                try:
                    api.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    api.kill()
                    api.wait()


if __name__ == '__main__':
    print(json.dumps(verify_release(), sort_keys=True))
