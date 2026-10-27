"""Deterministic evidence bundles made only from recorded successful outcomes."""
import csv
import hashlib
import io
import json
import zipfile

from .models import Model
from .runs import RunId, RunRepository
from .storage import Store


class ExportRequest(Model):
    run_id: RunId


LIMITATIONS = [
    'Observed proportions do not establish absolute abundance or growth.',
    'Non-detection does not establish extinction.',
    'The baselines do not model biological effects of treatment changes, including withdrawal.',
    'Previously unseen identified lineages and unknown ancestry are separate categories.',
    'Synthetic results exercise software behavior and do not establish biological validity.',
]


def _json(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def _csv(fields: list[str], rows: list[dict]) -> bytes:
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode('utf-8')


def export_evidence(store: Store, request: ExportRequest) -> bytes:
    run = RunRepository(store).get(request.run_id)
    if run.status != 'succeeded' or run.result is None:
        raise ValueError('Export requires a successful completed run; wait for completion or retry a failed/cancelled attempt.')
    if not run.result.evaluations or len(run.result.evaluations) != len(run.configuration.targets):
        raise ValueError('This saved run has no complete recorded evaluation. Create a new forecast to export complete evidence.')
    snapshot = store.get_snapshot(run.configuration.snapshot_id)
    evaluations = [value.model_dump(mode='json') for value in run.result.evaluations]
    comparisons = [dict(time=target.time, sample_id=target.sample_id, observed_total=target.observed_total, **category.model_dump(mode='json'))
                   for target in run.result.evaluations for category in target.categories]
    scores = [dict(time=target.time, sample_id=target.sample_id, observed_total=target.observed_total,
                   total_variation_distance=target.total_variation_distance, previously_unseen_share=target.previously_unseen_share)
              for target in run.result.evaluations]
    files = {
        'configuration.json': _json(run.configuration.model_dump(mode='json')),
        'predictions.json': _json([prediction.model_dump(mode='json') for prediction in run.result.predictions]),
        'evaluations.json': _json(evaluations),
        'comparisons.csv': _csv(['time', 'sample_id', 'observed_total', 'category', 'predicted_proportion', 'observed_proportion', 'observed_count', 'difference_percentage_points', 'previously_unseen'], comparisons),
        'scores.csv': _csv(['time', 'sample_id', 'observed_total', 'total_variation_distance', 'previously_unseen_share'], scores),
        'README.txt': ('Tumor Dynamics Lab evidence bundle, format 1\n\n'
            'This bundle contains saved predictions and observed comparisons, without recomputation.\n'
            'Reproducing the calculation requires access to the identified managed input snapshot.\n'
            'Resolve input_snapshot.managed_relative_path under the installation TDL_DATA_DIR and verify its SHA-256 identity.\n'
            'The source dataset and input observation tables are not included.\n'
            'Signed differences are forecast minus observed, in percentage points.\n'
            'Total variation distance is half the sum of absolute proportion differences over exhaustive aligned categories.\n'
            'Previously unseen share includes identified target-only lineages; unknown ancestry is separate and remains in totals.\n'
            'Scores are separate for each target; no cell counts are pooled across times/cultures.\n'
            'Both initial methods are deterministic; random seeds do not apply.\n\n'
            + '\n'.join(LIMITATIONS) + '\n').encode('utf-8'),
    }
    manifest = {
        'format_version': '1', 'run_id': run.id, 'created_at': run.created_at,
        'input_snapshot': {'id': snapshot.id, 'hash_algorithm': 'sha256', 'managed_relative_path': f'snapshots/{snapshot.id}.json'},
        'experiment_id': snapshot.experiment.id, 'experiment_name': snapshot.experiment.name,
        'culture_id': run.configuration.culture_id, 'scope': run.configuration.scope,
        'cutoff': run.configuration.cutoff, 'targets': run.configuration.targets, 'time_unit': snapshot.experiment.time_unit,
        'method': run.configuration.method, 'method_version': run.method_version,
        'software_version': run.software_version, 'settings': run.settings,
        'deterministic': run.deterministic, 'random_seeds': None,
        'synthetic': snapshot.experiment.synthetic, 'crosses_withdrawal': run.crosses_withdrawal,
        'source_dataset_included': False, 'limitations': LIMITATIONS,
        'files': {name: {'sha256': hashlib.sha256(content).hexdigest()} for name, content in sorted(files.items())},
    }
    files['manifest.json'] = _json(manifest)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(files.items()):
            # Fixed ZIP metadata makes repeat downloads byte-identical.
            archive.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), content)
    return output.getvalue()
