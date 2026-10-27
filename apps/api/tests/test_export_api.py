import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from tumor_api.app import create_app
from tumor_dynamics.demo import setup_demo
from tumor_dynamics.storage import Store
from tumor_dynamics.worker import process_next


@pytest.mark.parametrize('method', ['last_observed', 'damped_trend'])
def test_api_downloads_exact_recorded_evidence_for_either_method(tmp_path, method):
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    client = TestClient(create_app(tmp_path))
    configuration = dict(snapshot_id=snapshot.id, culture_id='culture-01', scope='whole culture', cutoff=7, targets=[14,21], method=method)
    run = client.post('/runs', json=configuration).json()
    pending = client.get(f'/runs/{run["id"]}/export')
    assert pending.status_code == 409
    assert 'successful completed' in pending.json()['detail']
    process_next(store)
    saved = client.get(f'/runs/{run["id"]}').json()
    response = client.get(f'/runs/{run["id"]}/export')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/zip'
    assert f'evidence-{run["id"]}.zip' in response.headers['content-disposition']
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert json.loads(archive.read('predictions.json')) == saved['result']['predictions']
        assert json.loads(archive.read('evaluations.json')) == saved['result']['evaluations']
        assert json.loads(archive.read('manifest.json'))['method'] == method
    assert TestClient(create_app(tmp_path)).get(f'/runs/{run["id"]}/export').content == response.content
    assert client.get(f'/runs/{run["id"]}').json() == saved


def test_api_explains_unavailable_exports_and_validates_run_identity(tmp_path):
    store = Store(tmp_path)
    snapshot = setup_demo(store)
    client = TestClient(create_app(tmp_path))
    run = client.post('/runs', json=dict(snapshot_id=snapshot.id, culture_id='culture-01', scope='whole culture', cutoff=7, targets=[14])).json()
    client.post(f'/runs/{run["id"]}/cancel')
    assert client.get(f'/runs/{run["id"]}/export').status_code == 409
    assert client.get('/runs/not-a-run/export').status_code == 422
    assert client.get(f'/runs/{"a"*32}/export').status_code == 404
