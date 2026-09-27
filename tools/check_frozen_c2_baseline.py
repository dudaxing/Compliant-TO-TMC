"""Verify preserved historical code, protocols, geometry and archive identities."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

BASELINE = '7fea2e44b67d0eff421219ebbcac68c506fb9d2f'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('choose a new receipt path')
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(subprocess.check_output(
        ['git', 'show', BASELINE+':handoff/repository_manifest.json'], cwd=root))
    records = [f for f in manifest['files'] if f['path'].startswith(('hf_repo/', 'geometry_dataset/'))
               or f['path'] == 'handoff/evidence_assets.json']
    errors = []
    for row in records:
        path = root/row['path']
        if not path.is_file():
            errors.append({'path':row['path'], 'reason':'missing'})
            continue
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != row['sha256'] or path.stat().st_size != row['bytes']:
            errors.append({'path':row['path'], 'reason':'modified'})
    receipt = dict(schema='c2-frozen-baseline-preservation-v1', baseline_commit=BASELINE,
        status='pass' if not errors else 'not_pass', errors=errors,
        hf_repo_original_files=sum(f['path'].startswith('hf_repo/') for f in records),
        geometry_original_files=sum(f['path'].startswith('geometry_dataset/') for f in records),
        archive_index_checked=True, byte_count=sum(f['bytes'] for f in records),
        checked_utc=datetime.now(timezone.utc).isoformat(),
        scope='Existing files only; candidate and guard additions have separate identities.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    print(json.dumps(receipt))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
