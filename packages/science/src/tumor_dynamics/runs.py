"""Persistent local run queue and immutable recorded outcomes."""
from datetime import datetime, timezone
import json
from typing import Annotated, Literal
from pydantic import Field
from uuid import uuid4
from .models import Model
from .storage import Store
from .forecasting import RunConfiguration, ForecastResult, prepare_forecast

SOFTWARE_VERSION = '0.1.0'
RunId = Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]


class RunRecord(Model):
    id: str
    configuration: RunConfiguration
    status: Literal['queued','running','succeeded','failed','cancelled']
    created_at: str
    method_version: str
    software_version: str
    settings: dict[str, bool | float | str]
    deterministic: bool = True
    crosses_withdrawal: bool
    error: str | None = None
    result: ForecastResult | None = None


def method_metadata(method: str) -> tuple[str,dict]:
    if method == 'last_observed':
        return 'last-observed-v1', {'smoothing':False}
    raise ValueError('Unsupported forecast method')


class RunRepository:
    def __init__(self, store: Store):
        self.store = store
        (store.root / 'runs').mkdir(exist_ok=True)
        with store.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS forecast_runs (
                id TEXT PRIMARY KEY, configuration TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL, method_version TEXT NOT NULL, software_version TEXT NOT NULL,
                settings TEXT NOT NULL, crosses_withdrawal INTEGER NOT NULL,
                error TEXT, result_path TEXT)''')

    def enqueue(self, configuration: RunConfiguration) -> RunRecord:
        snapshot = self.store.get_snapshot(configuration.snapshot_id)
        prepare_forecast(snapshot.experiment, configuration)
        version, settings = method_metadata(configuration.method)
        culture = next(c for c in snapshot.experiment.cultures if c.id == configuration.culture_id)
        crosses = any(configuration.cutoff < treatment.end <= max(configuration.targets) for treatment in culture.treatments)
        identity = uuid4().hex
        with self.store.connect() as db:
            db.execute('''INSERT INTO forecast_runs(id,configuration,status,created_at,method_version,software_version,settings,crosses_withdrawal)
                VALUES (?,?,?,?,?,?,?,?)''', (identity,configuration.model_dump_json(),'queued',datetime.now(timezone.utc).isoformat(),version,SOFTWARE_VERSION,json.dumps(settings),int(crosses)))
        return self.get(identity)

    def get(self, identity: str) -> RunRecord:
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM forecast_runs WHERE id=?',(identity,)).fetchone()
        if row is None:
            raise KeyError(f'Run {identity} not found')
        result = None
        if row['status'] == 'succeeded' and row['result_path']:
            result = ForecastResult.model_validate_json((self.store.root / row['result_path']).read_bytes())
        return RunRecord(id=row['id'],configuration=RunConfiguration.model_validate_json(row['configuration']),
            status=row['status'],created_at=row['created_at'],method_version=row['method_version'],software_version=row['software_version'],
            settings=json.loads(row['settings']),crosses_withdrawal=bool(row['crosses_withdrawal']),error=row['error'],result=result)

    def list(self) -> list[RunRecord]:
        with self.store.connect() as db:
            identities = [r['id'] for r in db.execute('SELECT id FROM forecast_runs ORDER BY created_at DESC,id')]
        return [self.get(identity) for identity in identities]

    def claim(self) -> RunRecord | None:
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT id FROM forecast_runs WHERE status='queued' ORDER BY created_at,id LIMIT 1").fetchone()
            if row is None:
                return None
            db.execute("UPDATE forecast_runs SET status='running' WHERE id=? AND status='queued'",(row['id'],))
        return self.get(row['id'])

    def complete(self, identity: str, result: ForecastResult) -> RunRecord:
        relative = f'runs/{identity}.json'
        path = self.store.root / relative
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT status FROM forecast_runs WHERE id=?',(identity,)).fetchone()
            if row is None:
                raise KeyError(f'Run {identity} not found')
            if row['status'] != 'running':
                return self.get(identity)
            with path.open('x') as stream:
                stream.write(result.model_dump_json())
            path.chmod(0o444)
            db.execute("UPDATE forecast_runs SET status='succeeded',result_path=? WHERE id=? AND status='running'",(relative,identity))
        return self.get(identity)

    def fail(self, identity: str, explanation: str) -> RunRecord:
        with self.store.connect() as db:
            db.execute("UPDATE forecast_runs SET status='failed',error=? WHERE id=? AND status='running'",(explanation,identity))
        return self.get(identity)

    def cancel(self, identity: str) -> RunRecord:
        with self.store.connect() as db:
            db.execute("UPDATE forecast_runs SET status='cancelled',error='Cancelled by researcher',result_path=NULL WHERE id=? AND status IN ('queued','running')", (identity,))
        return self.get(identity)

    def retry(self, identity: str) -> RunRecord:
        previous = self.get(identity)
        if previous.status not in ('failed', 'cancelled'):
            raise ValueError('Only failed or cancelled attempts can be retried')
        return self.enqueue(previous.configuration)

    def recover_interrupted(self) -> None:
        """Call only while holding the exclusive worker ownership lock."""
        with self.store.connect() as db:
            db.execute("UPDATE forecast_runs SET status='failed',error='Worker interrupted before finalization; retry creates a new attempt',result_path=NULL WHERE status='running'")
