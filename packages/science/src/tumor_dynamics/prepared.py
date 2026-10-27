"""Versioned prepared-folder import through the shared scientific input models."""
import json
from pathlib import Path

from .models import Experiment, Snapshot
from .storage import Store


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key {key!r}; count records and metadata keys must be unique')
        result[key] = value
    return result


def import_prepared(folder: Path | str, store: Store) -> Snapshot:
    path = Path(folder) / 'experiment.json'
    data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_object)
    if not isinstance(data, dict) or 'format_version' not in data:
        raise ValueError('experiment.json requires explicit format_version: "1"')
    experiment = Experiment.model_validate(data)
    return store.save_snapshot(experiment)
