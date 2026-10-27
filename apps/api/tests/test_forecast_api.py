from fastapi.testclient import TestClient
from tumor_api.app import create_app
from tumor_dynamics.demo import setup_demo
from tumor_dynamics.storage import Store
from tumor_dynamics.worker import process_next


def test_api_creates_queued_attempt_and_reopens_original_saved_configuration(tmp_path):
    snapshot = setup_demo(Store(tmp_path))
    client = TestClient(create_app(tmp_path))
    request = dict(snapshot_id=snapshot.id,culture_id='culture-01',scope='whole culture',cutoff=7,targets=[14],method='last_observed')
    assert client.post('/forecast/eligibility',json=request).json()['available'] is True
    response = client.post('/runs',json=request)
    assert response.status_code == 201
    run = response.json()
    assert run['status'] == 'queued'
    process_next(Store(tmp_path))
    saved = client.get('/runs/'+run['id']).json()
    assert saved['status'] == 'succeeded'
    assert saved['configuration'] == request
    assert saved['result']['predictions'][0]['proportions']['C'] == 0
    assert client.get('/runs').json()[0] == saved
    assert client.get('/runs/no-such-run').status_code == 404
    request['scope'] = 'incompatible fraction'
    eligibility = client.post('/forecast/eligibility',json=request).json()
    assert eligibility['available'] is False
    assert 'scope' in eligibility['reason']
    assert client.post('/runs',json=request).status_code == 422
    request['cutoff'] = '7'
    assert client.post('/runs',json=request).status_code == 422


def test_api_trend_eligibility_and_saved_prediction_are_explicit(tmp_path):
    snapshot = setup_demo(Store(tmp_path))
    client = TestClient(create_app(tmp_path))
    request = dict(snapshot_id=snapshot.id,culture_id='culture-01',scope='whole culture',cutoff=0,targets=[14],method='damped_trend')
    outcome = client.post('/forecast/eligibility',json=request)
    assert outcome.status_code == 200
    assert outcome.json()['available'] is False
    assert 'two distinct' in outcome.json()['reason']
    assert client.post('/runs',json=request).status_code == 422
    request['cutoff'] = 7
    created = client.post('/runs',json=request)
    assert created.status_code == 201
    process_next(Store(tmp_path))
    saved = client.get('/runs/'+created.json()['id']).json()
    assert saved['status'] == 'succeeded'
    assert saved['method_version'] == 'damped-trend-v1'
    assert saved['settings']['alpha'] == .5
    assert saved['result']['predictions'][0]['proportions']['C'] > 0
