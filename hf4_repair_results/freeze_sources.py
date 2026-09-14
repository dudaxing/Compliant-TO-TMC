"""Save each pre-execution implementation snapshot without changing old evidence."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json

p = argparse.ArgumentParser()
p.add_argument('--label', required=True)
a = p.parse_args()
if not a.label.replace('_', '').isalnum():
    raise ValueError('label must be alphanumeric/underscore')
root = Path(__file__).resolve().parents[1]
repo = root/'hf_repo'
output = root/'hf4_repair_results'/('source_'+a.label)
output.mkdir(exist_ok=False)
files = {}
for directory in ('src/hf_eval', 'scripts', 'tests'):
    for source in sorted((repo/directory).glob('*.py')):
        relative = source.relative_to(repo).as_posix()
        data = source.read_bytes()
        dest = output/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        files[relative] = hashlib.sha256(data).hexdigest()
record = dict(schema_version='hf4-split-source-freeze-1.0', version='0.5.0',
              created_utc=datetime.now(timezone.utc).isoformat(), files=files,
              scope='actual runtime, development scripts, and tests before the named execution')
(output/'source_freeze.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
print(output/'source_freeze.json')
