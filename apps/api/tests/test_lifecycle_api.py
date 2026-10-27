from fastapi.testclient import TestClient
from tumor_api.app import create_app
from tumor_dynamics.demo import setup_demo
from tumor_dynamics.storage import Store


def test_cancel_retry_api_records_distinct_attempts_and_validates_action_identifiers(tmp_path):
    snapshot = setup_demo(Store(tmp_path))
    client = TestClient(create_app(tmp_path))
    config = dict(snapshot_id=snapshot.id,culture_id='culture-01',scope='whole culture',cutoff=7,targets=[14],method='last_observed')
    created = client.post('/runs',json=config).json()
    cancelled = client.post(f'/runs/{created["id"]}/cancel')
    assert cancelled.status_code == 200
    assert cancelled.json()['status'] == 'cancelled'
    retried = client.post(f'/runs/{created["id"]}/retry')
    assert retried.status_code == 201
    assert retried.json()['id'] != created['id']
    assert retried.json()['configuration'] == created['configuration']
    assert client.get(f'/runs/{created["id"]}').json()['status'] == 'cancelled'
    assert client.post(f'/runs/{retried.json()["id"]}/retry').status_code == 409
    assert client.post('/runs/invalid/cancel').status_code == 422
    assert client.post(f'/runs/{"a"*32}/cancel').status_code == 404
