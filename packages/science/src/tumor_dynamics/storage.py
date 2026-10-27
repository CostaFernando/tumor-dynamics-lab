"""SQLite metadata and content-addressed, immutable local input snapshots."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from .composition import composition
from .models import Experiment, Snapshot


def storage_root() -> Path:
    return Path(os.environ.get('TDL_DATA_DIR', 'data')).resolve()


class Store:
    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root is not None else storage_root()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / 'snapshots').mkdir(exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, name TEXT NOT NULL, synthetic INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.root / 'research.sqlite3', timeout=30)
        db.row_factory = sqlite3.Row
        return db

    def save_snapshot(self, experiment: Experiment) -> Snapshot:
        content = json.dumps(experiment.model_dump(mode='json'), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        identity = hashlib.sha256(content).hexdigest()
        path = self.root / 'snapshots' / f'{identity}.json'
        # Exclusive creation keeps repeated setup from overwriting an existing snapshot.
        try:
            with path.open('xb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            path.chmod(0o444)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError('Snapshot content identity mismatch')
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO snapshots(id, experiment_id, name, synthetic) VALUES (?, ?, ?, ?)',
                       (identity, experiment.id, experiment.name, experiment.synthetic))
        return self.get_snapshot(identity)

    def get_snapshot(self, identity: str) -> Snapshot:
        with self.connect() as db:
            row = db.execute('SELECT id FROM snapshots WHERE id = ?', (identity,)).fetchone()
        if row is None:
            raise KeyError(f'Snapshot {identity} not found')
        content = (self.root / 'snapshots' / f'{row["id"]}.json').read_bytes()
        if hashlib.sha256(content).hexdigest() != identity:
            raise ValueError('Stored snapshot failed content identity verification')
        experiment = Experiment.model_validate_json(content)
        return Snapshot(id=identity, experiment=experiment,
                        observations=[composition(s) for s in experiment.samples])

    def list_snapshots(self) -> list[Snapshot]:
        with self.connect() as db:
            ids = [r['id'] for r in db.execute('SELECT id FROM snapshots ORDER BY created_at, id')]
        return [self.get_snapshot(identity) for identity in ids]
