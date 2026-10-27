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


def test_prepared_snapshots_and_descriptive_states_are_retrievable_independently(tmp_path):
    from pathlib import Path
    from tumor_dynamics.prepared import import_prepared
    store = Store(tmp_path)
    demo = setup_demo(store)
    prepared = import_prepared(Path(__file__).resolve().parents[3] / 'fixtures' / 'prepared-example', store)
    with TestClient(create_app(tmp_path)) as client:
        assert {s['id'] for s in client.get('/snapshots').json()} == {demo.id, prepared.id}
        detail = client.get(f'/snapshots/{prepared.id}').json()
        assert detail['experiment']['id'] == 'prepared-format-example'
        assert detail['observations'][0]['proportions']['__unknown__'] == 0.2
        assert detail['observations'][0]['sample']['cell_state_summary'].startswith('Fictional descriptive')
        assert client.get(f'/snapshots/{demo.id}').json()['observations'][0]['total'] == 100
