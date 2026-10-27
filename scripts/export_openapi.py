"""Generate the committed client contract from Python response/request models."""
import json
from pathlib import Path
from tumor_api.app import create_app

root = Path(__file__).resolve().parents[1]
(root / 'packages/api-client/openapi.json').write_text(json.dumps(create_app().openapi(), indent=2) + '\n')
