from fastapi.testclient import TestClient
from tumor_api.app import create_app
from tumor_dynamics.demo import setup_demo
from tumor_dynamics.storage import Store


def test_persisted_demo_is_visible_after_api_restart(tmp_path):
    snapshot = setup_demo(Store(tmp_path))
    for _ in range(2):
        with TestClient(create_app(tmp_path)) as client:
            listing = client.get('/snapshots')
            assert listing.status_code == 200
            assert listing.json()[0]['id'] == snapshot.id
            detail = client.get(f'/snapshots/{snapshot.id}').json()
            assert detail['observations'][2]['proportions']['A'] == 0.65
            assert detail['observations'][2]['total'] == 100
            assert client.get('/snapshots/missing').status_code == 404
