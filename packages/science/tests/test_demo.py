from tumor_dynamics.demo import setup_demo
from tumor_dynamics.storage import Store


def test_demo_survives_restart_and_repeated_setup_preserves_snapshot(tmp_path):
    first = setup_demo(Store(tmp_path))
    reopened = Store(tmp_path).get_snapshot(first.id)
    repeated = setup_demo(Store(tmp_path))
    assert repeated.id == first.id
    assert reopened == first
    assert len(Store(tmp_path).list_snapshots()) == 1
    assert reopened.experiment.synthetic is True
    samples = reopened.experiment.samples
    assert [s.time for s in samples] == [0, 3, 7, 14, 21]
    assert samples[2].counts['C'] == 0
    assert 'D' not in samples[2].counts
    assert samples[3].counts['D'] == 10
