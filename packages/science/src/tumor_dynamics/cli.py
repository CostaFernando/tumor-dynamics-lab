import argparse
import json
import sys
import time
from .forecasting import RunConfiguration
from .runs import RunRepository
from .worker import process_next
from .demo import setup_demo
from .prepared import import_prepared
from .storage import Store


def main():
    parser = argparse.ArgumentParser(description='Local lineage-composition research tools')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo', help='Initialize the fixed fictional experiment idempotently')
    prepared = commands.add_parser('import', help='Import a versioned prepared local folder')
    prepared.add_argument('folder')
    inspect = commands.add_parser('inspect', help='Inspect a managed immutable snapshot')
    inspect.add_argument('snapshot_id')
    forecast = commands.add_parser('forecast', help='Queue a forecast using one culture and comparable sampling scope')
    forecast.add_argument('--snapshot', required=True)
    forecast.add_argument('--culture', required=True)
    forecast.add_argument('--scope', required=True)
    forecast.add_argument('--cutoff', type=float, required=True)
    forecast.add_argument('--target', type=float, action='append', required=True)
    forecast.add_argument('--method', choices=['last_observed'], default='last_observed')
    run = commands.add_parser('run', help='Reopen a recorded run without recomputing')
    run.add_argument('run_id')
    worker = commands.add_parser('worker', help='Process the persistent local run queue independently of the browser')
    worker.add_argument('--once', action='store_true', help='Process at most one queued attempt and exit')
    args = parser.parse_args()
    try:
        store = Store()
        if args.command == 'demo':
            snapshot = setup_demo(store)
            print(json.dumps({'snapshot_id': snapshot.id, 'synthetic': True}))
        elif args.command == 'import':
            snapshot = import_prepared(args.folder, store)
            print(json.dumps({'snapshot_id': snapshot.id, 'synthetic': snapshot.experiment.synthetic}))
        elif args.command == 'forecast':
            configuration = RunConfiguration(snapshot_id=args.snapshot,culture_id=args.culture,scope=args.scope,cutoff=args.cutoff,targets=args.target,method=args.method)
            print(RunRepository(store).enqueue(configuration).model_dump_json(indent=2))
        elif args.command == 'run':
            print(RunRepository(store).get(args.run_id).model_dump_json(indent=2))
        elif args.command == 'worker':
            while True:
                identity = process_next(store)
                if args.once:
                    print(json.dumps({'processed_run':identity}))
                    break
                if identity is None:
                    time.sleep(0.25)
        else:
            print(store.get_snapshot(args.snapshot_id).model_dump_json(indent=2))
    except KeyboardInterrupt:
        return 0
    except (ValueError, KeyError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
