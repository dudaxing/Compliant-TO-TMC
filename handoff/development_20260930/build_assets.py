"""Losslessly package the 18 already-frozen development roots; no scientific execution.

Run once with a fresh archive directory. Never edits the frozen roots. Files in
the Git tree may also be in an archive; restoration accepts identical bytes.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

TAG = 'hf4-c2-development-evidence-20260930-v1'
GROUPS = {
    'arithmetic': ['near_rotation_segments_001', 'invariants_hu_campaign_001', 's0_ready_001', 'jit_ad_ready_001'],
    'supervision': ['force_observe_001', 'force_cpu_001', 'cpu_supervision_001', 'cpu_pid_diagnostic_001', 'cpu_cleanup_contract_001', 'force_cpu_observe_001'],
    'reuse': ['force_reuse_001', 'force_reuse_002'],
    'cost-trace': ['force_cost_001', 'micro_trace_001'],
    'native': ['native_path_001', 'micro_trace_002'],
    'readers': ['native_volume_001', 'native_stream_001'],
}

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    # Extended Windows paths preserve actual long-path members in the archives.
    scan = Path('\\\\?\\' + str(root)) if __import__('os').name == 'nt' else root
    args.archives.mkdir(parents=True, exist_ok=False)
    index_path = root / 'handoff/evidence_assets.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    assert not any(a.get('release_tag') == TAG for a in index['assets'])
    new_assets = []
    keep, archive_only = [], []
    for group, names in GROUPS.items():
        records = []
        for name in names:
            base = scan / 'hf4_c2_stable_f_validation' / name
            assert base.is_dir()
            for path in sorted(base.rglob('*')):
                if path.is_dir():
                    continue
                assert path.is_file() and not path.is_symlink()
                rel = path.relative_to(scan).as_posix()
                assert path.suffix.lower() not in ('.pdf', '.m'), rel
                records.append({'path': rel, 'bytes': path.stat().st_size, 'sha256': digest(path)})
                # Top-level receipts, maps and SVGs remain navigable in a clone.
                (keep if path.parent == base else archive_only).append(rel)
        asset_name = f'hf4-c2-development-{group}-20260930-v1.zip'
        target = args.archives / asset_name
        with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
            for record in records:
                path = scan / record['path']
                assert path.stat().st_size == record['bytes'] and digest(path) == record['sha256']
                archive.write(path, arcname=record['path'])
        # Verify ZIP members byte-for-byte (does not decode any native gzip).
        with zipfile.ZipFile(target) as archive:
            assert archive.namelist() == [f['path'] for f in records]
            for record in records:
                with archive.open(record['path']) as f:
                    assert hashlib.file_digest(f, 'sha256').hexdigest() == record['sha256']
                assert digest(scan / record['path']) == record['sha256']
        new_assets.append({'name': asset_name, 'url': f'https://github.com/dudaxing/Compliant-TO-TMC/releases/download/{TAG}/{asset_name}',
            'bytes': target.stat().st_size, 'sha256': digest(target), 'mode': 'restore_relative_files',
            'release_tag': TAG, 'requires': [], 'files': records})
        print(json.dumps({'group': group, 'files': len(records), 'bytes': sum(f['bytes'] for f in records), 'archive_bytes': target.stat().st_size}), flush=True)
    # All groups form a complete chain. Restore prior groups when requesting a
    # later stage; the first group also restores the existing saved C1/C2 inputs.
    prior = ['hf4-c2-stable-f-saved-production-arrays-v1.zip']
    for asset in new_assets:
        asset['requires'] = list(prior)
        prior = [asset['name']]
    index['assets'].extend(new_assets)
    write_json(index_path, index)
    ignore = root / '.gitignore'
    with ignore.open('a', encoding='utf-8', newline='\n') as f:
        f.write('\n# Lossless development evidence in versioned Release assets, 2026-09-30.\n')
        for name in sorted(archive_only):
            # Gitignore metacharacters must remain literal file identities.
            escaped = name.replace('[', '[[]').replace('*', '[*]').replace('?', '[?]')
            f.write('/' + escaped + '\n')
    report = {'schema': 'development-lossless-packaging-v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'release_tag': TAG, 'frozen_roots': [n for names in GROUPS.values() for n in names],
        'files': sum(len(a['files']) for a in new_assets), 'original_bytes': sum(f['bytes'] for a in new_assets for f in a['files']),
        'archives': [{k: a[k] for k in ('name', 'bytes', 'sha256', 'requires')} for a in new_assets],
        'git_navigation_files': sorted(keep), 'release_only_files': sorted(archive_only),
        'all_member_hashes_verified': True, 'frozen_files_unchanged': True, 'native_gzip_decoded': False,
        'mechanics_executed': False, 'scientific_admission_changed': False}
    write_json(root / 'handoff/development_20260930/packaging_receipt.json', report)

if __name__ == '__main__':
    main()
