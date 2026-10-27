import argparse
import json
import sys
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
    args = parser.parse_args()
    try:
        store = Store()
        if args.command == 'demo':
            snapshot = setup_demo(store)
            print(json.dumps({'snapshot_id': snapshot.id, 'synthetic': True}))
        elif args.command == 'import':
            snapshot = import_prepared(args.folder, store)
            print(json.dumps({'snapshot_id': snapshot.id, 'synthetic': snapshot.experiment.synthetic}))
        else:
            print(store.get_snapshot(args.snapshot_id).model_dump_json(indent=2))
    except (ValueError, KeyError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
