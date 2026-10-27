from pathlib import Path
from fastapi import FastAPI, HTTPException
from tumor_dynamics.models import Snapshot
from tumor_dynamics.storage import Store


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

    return app


app = create_app()
