"""Finish the interrupted metadata publication without restarting any science."""
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import shutil
import subprocess

AUTHOR = Path(__file__).resolve().parent
old = runpy.run_path(str(AUTHOR / 'publish.py'))
ROOT, RESTORE, STAGE = old['ROOT'], old['RESTORE'], old['STAGE']
git, digest, save = old['git'], old['digest'], old['save']


def main():
    initial_raw = (AUTHOR / 'publication_receipt.json').read_bytes()
    record = json.loads(initial_raw)
    assert record['status'] == 'publication_stopped'
    assert record['failure_phase'] == 'stage_and_commit'
    assert git(ROOT, 'rev-parse', 'HEAD') == git(RESTORE, 'rev-parse', 'HEAD') == old['BASE']
    assert not git(RESTORE, 'status', '--porcelain')
    assert git(ROOT, 'branch', '--show-current') == 'main'
    assert git(ROOT, 'remote', 'get-url', '--push', 'origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    assert not git(ROOT, 'diff', old['BASE'], '--name-only', '--', 'hf_repo/src')
    artifact = STAGE + '/CANDIDATE_DIFF.md'
    raw = (ROOT / artifact).read_bytes()
    assert digest(raw) == 'fdc6ede4dd19f62ff1b9168ecdd66d6d25d1b7f92761637c6c7d58a513ad4322'
    lines = raw.decode('utf-8').splitlines()
    trailing = [(i, line) for i, line in enumerate(lines, 1) if line.rstrip() != line]
    assert trailing == [(i, ' ') for i in (29, 30, 32, 38, 42, 64)]
    assert raw.count(b'```diff') == 1
    assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == {r['path'] for r in record['delta_files']}
    git(ROOT, 'diff', '--cached', '--check', '--', '.', ':(exclude)' + artifact)

    note = (
        '# L-CUNLOAD2 publication interruption and explicit metadata continuation\n\n'
        'The first publication stopped before commit at git diff --cached --check. '
        'Exactly six reported lines (29,30,32,38,42,64) in CANDIDATE_DIFF.md are '
        'the single-space context marker for empty lines inside its literal unified diff. '
        'The frozen artifact SHA remains fdc6ede4dd19f62ff1b9168ecdd66d6d25d1b7f92761637c6c7d58a513ad4322.\n\n'
        'The root inspected these six literal lines, verified all other staged files with '
        'the unchanged whitespace check, and explicitly continued only commit/push/restore. '
        'The literal diff artifact is excluded from that formatting-only check; its frozen '
        'bytes are preserved. No global Git setting, source, scientific gate, calculation, '
        'test, viewer, seal or pixel inspection is changed or repeated. '
        'The original publication interruption receipt is preserved verbatim beside this note. '
        'This is ordinary metadata completion, not a resumed scientific resource window.\n'
    )
    new_files = {
        STAGE + '/author/publication_initial_stop.json': initial_raw,
        STAGE + '/author/publication_whitespace_note.md': note.encode('utf-8'),
        STAGE + '/author/resume_publication_metadata.py': Path(__file__).read_bytes(),
    }
    manifest_name = old['MANIFEST']
    manifest = json.loads((ROOT / manifest_name).read_bytes())
    assert len(manifest['files']) == record['manifest_files']
    entries = {r['path']: r for r in manifest['files']}
    rows = {r['path']: r for r in record['delta_files']}
    for name, content in new_files.items():
        assert name not in entries and not (ROOT / name).exists()
        (ROOT / name).write_bytes(content)
        row = dict(path=name, bytes=len(content), sha256=digest(content))
        entries[name] = rows[name] = row
    manifest.update(files=sorted(entries.values(), key=lambda r: r['path']),
                    created_utc=datetime.now(timezone.utc).isoformat())
    (ROOT / manifest_name).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    raw = (ROOT / manifest_name).read_bytes()
    rows[manifest_name] = dict(path=manifest_name, bytes=len(raw), sha256=digest(raw))
    record.update(status='explicit_metadata_continuation', delta_files=list(rows.values()),
        manifest_files=len(entries), manifest_total_bytes=sum(r['bytes'] for r in entries.values()),
        initial_publication_interruption=dict(failure_phase=record['failure_phase'], error=record['error'],
            receipt_path=STAGE + '/author/publication_initial_stop.json'),
        continuation_scope='Formatting-only exception for six exact literal diff context lines; no scientific or frozen-byte changes, no science retry')
    save(record)
    def run(root, *args):
        subprocess.run(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args], cwd=root, check=True)
    run(ROOT, 'add', '-f', '--', *new_files, manifest_name)
    assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == set(rows)
    git(ROOT, 'diff', '--cached', '--check', '--', '.', ':(exclude)' + artifact)
    run(ROOT, 'commit', '-m', 'Validate installed first-unload reader with corrected tiny caller')
    head = git(ROOT, 'rev-parse', 'HEAD')
    record.update(status='committed', commit=head)
    save(record)
    run(ROOT, 'push', 'origin', 'main')
    assert git(ROOT, 'ls-remote', 'origin', 'refs/heads/main').split()[0] == head
    assert not git(ROOT, 'status', '--porcelain')
    record.update(status='pushed', remote_main=head)
    save(record)
    run(RESTORE, 'fetch', 'origin')
    run(RESTORE, 'merge', '--ff-only', 'origin/main')
    assert git(RESTORE, 'rev-parse', 'HEAD') == head
    for row in rows.values():
        path = RESTORE / row['path']
        assert path.stat().st_size == row['bytes']
        if path.suffix.lower() not in old['SEALED_ONLY_SUFFIXES']:
            assert digest(path.read_bytes()) == row['sha256']
    assert not git(ROOT, 'status', '--porcelain') and not git(RESTORE, 'status', '--porcelain')
    record.update(status='published_and_incrementally_restored_pass', restore_head=head,
        source_clean=True, restore_clean=True, completed_utc=datetime.now(timezone.utc).isoformat(),
        restore_verification='Delta ordinary bytes only; scientific/media original producer seal plus stat, no payload rehash/decode or science')
    save(record)
    print(json.dumps({k: record[k] for k in ('status', 'execution_outcome', 'commit', 'remote_main', 'restore_head', 'manifest_files')}), flush=True)


if __name__ == '__main__':
    main()
