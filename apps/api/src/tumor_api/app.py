from pathlib import Path
from fastapi import FastAPI, HTTPException
from tumor_dynamics.models import Snapshot
from tumor_dynamics.storage import Store
from tumor_dynamics.forecasting import RunConfiguration, Eligibility, eligibility
from tumor_dynamics.runs import RunRepository, RunRecord


def create_app(root: Path | str | None = None) -> FastAPI:
    app = FastAPI(title='Tumor Dynamics Lab', version='0.1.0')
    # Initialize storage on request, so contract generation has no side effects.
    def store():
        return Store(root)

    @app.get('/snapshots', response_model=list[Snapshot], operation_id='list_snapshots')
    def list_snapshots():
        return store().list_snapshots()

    @app.get('/snapshots/{snapshot_id}', response_model=Snapshot, operation_id='get_snapshot')
    def get_snapshot(snapshot_id: str):
        try:
            return store().get_snapshot(snapshot_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post('/forecast/eligibility', response_model=Eligibility, operation_id='forecast_eligibility')
    def forecast_eligibility(configuration: RunConfiguration):
        try:
            return eligibility(store().get_snapshot(configuration.snapshot_id).experiment, configuration)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post('/runs', response_model=RunRecord, status_code=201, operation_id='create_run')
    def create_run(configuration: RunConfiguration):
        try:
            return RunRepository(store()).enqueue(configuration)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.get('/runs', response_model=list[RunRecord], operation_id='list_runs')
    def list_runs():
        return RunRepository(store()).list()

    @app.get('/runs/{run_id}', response_model=RunRecord, operation_id='get_run')
    def get_run(run_id: str):
        try:
            return RunRepository(store()).get(run_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    return app


app = create_app()
