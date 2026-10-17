"""Archive the completed L-CREF1 publication receipt, ordinary metadata only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE = Path('D:/hf-restore-20260930')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_reference_001'


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def main():
    record = json.loads((AUTHOR / 'publication_receipt.json').read_bytes())
    assert record['status'] == 'published_and_incrementally_restored_pass'
    base = record['commit']
    assert git(ROOT, 'rev-parse', 'HEAD') == git(RESTORE, 'rev-parse', 'HEAD') == base
    assert not git(ROOT, 'status', '--porcelain') and not git(RESTORE, 'status', '--porcelain')
    assert git(ROOT, 'remote', 'get-url', '--push', 'origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    name = STAGE + '/author/publication_receipt.json'
    archive = ROOT / name
    with archive.open('xb') as stream:
        stream.write((AUTHOR / 'publication_receipt.json').read_bytes())
    manifest_name = 'handoff/repository_manifest.json'
    manifest = json.loads((ROOT / manifest_name).read_bytes())
    assert len(manifest['files']) == record['manifest_files']
    assert name not in {row['path'] for row in manifest['files']}
    raw = archive.read_bytes()
    manifest['files'].append(dict(path=name, bytes=len(raw), sha256=sha256(raw).hexdigest()))
    manifest['files'].sort(key=lambda row: row['path'])
    manifest.update(previous_delivery_commit=base, storage_stage='l_cref1_publication_receipt_archived_001',
        created_utc=datetime.now(timezone.utc).isoformat())
    (ROOT / manifest_name).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8', newline='\n')
    names = [name, manifest_name]
    pins = {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in names}
    subprocess.run(['git', 'add', '-f', '--', *names], cwd=ROOT, check=True)
    assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == set(names)
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    subprocess.run(['git', 'commit', '-m', 'Archive L-CREF1 publication and restore receipt'], cwd=ROOT, check=True)
    head = git(ROOT, 'rev-parse', 'HEAD')
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT, check=True)
    assert git(ROOT, 'ls-remote', 'origin', 'refs/heads/main').split()[0] == head
    subprocess.run(['git', 'fetch', 'origin'], cwd=RESTORE, check=True)
    subprocess.run(['git', 'merge', '--ff-only', 'origin/main'], cwd=RESTORE, check=True)
    assert git(RESTORE, 'rev-parse', 'HEAD') == head
    assert all(sha256((RESTORE / path).read_bytes()).hexdigest() == pin for path, pin in pins.items())
    assert not git(ROOT, 'status', '--porcelain') and not git(RESTORE, 'status', '--porcelain')
    answer = dict(status='ordinary_publication_receipt_archived_and_restored', commit=head,
        execution_delivery_commit=base, execution_outcome=record['execution_outcome'],
        manifest_files=len(manifest['files']), source_clean=True, restore_clean=True)
    (AUTHOR / 'publication_archive_receipt.json').write_text(json.dumps(answer, indent=2) + '\n',
        encoding='utf-8', newline='\n')
    print(json.dumps(answer), flush=True)


if __name__ == '__main__':
    main()
