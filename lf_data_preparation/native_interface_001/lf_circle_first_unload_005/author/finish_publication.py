"""Finish ordinary delivery after a precommit EOF rejection; no scientific execution."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE = Path('D:/hf-restore-20260930')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_005'
BASE = '8a78fbf54fcd45640879ad357c880d12ee38aca9'
MANIFEST = 'handoff/repository_manifest.json'
SEALED = {'.npz', '.png', '.gif', '.gz', '.csv', '.zip'}


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args], cwd=root).decode('utf-8').strip()


def command(root, *args):
    subprocess.run(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args], cwd=root, check=True)


def pin(raw):
    return sha256(raw).hexdigest()


def row(name):
    raw = (ROOT/name).read_bytes()
    return dict(path=name, bytes=len(raw), sha256=pin(raw))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def main():
    raw = (AUTHOR/'publication_receipt.json').read_bytes()
    record = json.loads(raw)
    assert record['status'] == 'publication_stopped' and record['failure_phase'] == 'stage_and_commit'
    assert 'diff' in record['error']['reason'] and '--check' in record['error']['reason']
    assert record['execution_outcome'] == 'pass'
    assert git(ROOT, 'rev-parse', 'HEAD') == git(RESTORE, 'rev-parse', 'HEAD') == BASE
    assert not git(RESTORE, 'status', '--porcelain')
    assert git(ROOT, 'branch', '--show-current') == 'main'
    assert git(ROOT, 'remote', 'get-url', '--push', 'origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    rows = {item['path']:item for item in record['delta_files']}
    assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == set(rows)
    failure_name = STAGE+'/author/publication_precommit_failure.json'
    with (ROOT/failure_name).open('xb') as stream:
        stream.write(raw)
    normalized = []
    for suffix in ('.json', '.md'):
        name = STAGE+'/author/PHYSICAL_INTERPRETATION'+suffix
        path = ROOT/name
        before = path.read_bytes()
        assert row(name) == rows[name]
        after = before.rstrip(b'\r\n')+b'\n'
        assert before == after+b'\n', 'Only the one surplus EOF LF reported by Git may change'
        assert (AUTHOR/path.name).read_bytes() == before
        if suffix == '.json':
            assert json.loads(before) == json.loads(after)
        path.write_bytes(after)
        normalized.append(dict(path=name, before_bytes=len(before), after_bytes=len(after), before_sha256=pin(before), after_sha256=pin(after), removed_EOF_LF=1, content_unchanged=True))
        rows[name] = row(name)
    note_name = STAGE+'/author/publication_format_note.json'
    note = dict(scope='Ordinary documentation/Git completion only; unique scientific window and closure remain closed PASS', original_publication_terminal='df066e exit1 before commit', failure_record=dict(path=failure_name, sha256=pin(raw)), normalization=normalized, scientific_executions_added=0, helper_relaunches=0, close_relaunches=0, original_publish_main_relaunches=0, original_scientific_output_seal_files=78, source_qualification_unchanged=True, recorded_utc=datetime.now(timezone.utc).isoformat())
    with (ROOT/note_name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(note, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    script_name = STAGE+'/author/finish_publication.py'
    assert not (ROOT/script_name).exists()
    shutil.copyfile(Path(__file__), ROOT/script_name)
    results_name = STAGE+'/RESULTS.md'
    text = (ROOT/results_name).read_text(encoding='utf-8')
    text += '\nOrdinary publication note: the first Git precommit whitespace check stopped on surplus EOF lines in two explanatory annexes, before any commit/push. Only these EOF lines were normalized; the scientific PASS, original78-output seal and source bytes remain unchanged. See [failure record](author/publication_precommit_failure.json) and [format note](author/publication_format_note.json). The original helper, close and publication main were not relaunched.\n'
    (ROOT/results_name).write_text(text, encoding='utf-8', newline='\n')
    for name in (failure_name, note_name, script_name, results_name):
        rows[name] = row(name)
    assert not git(ROOT, 'diff', BASE, '--name-only', '--', 'hf_repo/src')
    for item in rows.values():
        if item['path'] == MANIFEST:
            continue
        path = ROOT/item['path']
        assert path.stat().st_size == item['bytes']
        if path.suffix.lower() not in SEALED:
            assert row(item['path']) == item
    history = json.loads((ROOT/STAGE/'author/front_history.json').read_bytes())
    for item in history['files']:
        old = subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', 'show', BASE+':'+item['path']], cwd=ROOT)
        current = (ROOT/item['path']).read_bytes()
        assert current.endswith(old) and current.count(old) == 1
    manifest = json.loads((ROOT/MANIFEST).read_bytes())
    entries = {item['path']:item for item in manifest['files']}
    for name, item in rows.items():
        if name != MANIFEST:
            entries[name] = item
    manifest.update(created_utc=datetime.now(timezone.utc).isoformat(), storage_stage='l_cunload5_closed_ordinary_EOF_delivery_completion', files=sorted(entries.values(), key=lambda item:item['path']))
    write(ROOT/MANIFEST, manifest)
    rows[MANIFEST] = row(MANIFEST)
    actual_stage = {p.relative_to(ROOT).as_posix() for p in (ROOT/STAGE).rglob('*') if p.is_file()}
    assert actual_stage == {n for n in rows if n.startswith(STAGE+'/')}
    record.update(status='ordinary_format_repair_ready_to_commit', delta_files=list(rows.values()), manifest_files=len(entries), manifest_total_bytes=sum(item['bytes'] for item in entries.values()), precommit_failure_record=dict(path=failure_name, sha256=pin(raw)), ordinary_format_completion_note=note_name)
    for key in ('failure_phase', 'error', 'stopped_utc', 'no_automatic_retry_rollback_or_force'):
        record.pop(key, None)
    command(ROOT, 'add', '-f', '--', *rows)
    assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == set(rows)
    command(ROOT, 'diff', '--cached', '--check')
    command(ROOT, 'commit', '-m', 'Record circle unloading to zero and documented precommit EOF correction')
    head = git(ROOT, 'rev-parse', 'HEAD')
    record.update(status='committed', commit=head)
    write(AUTHOR/'publication_receipt.json', record)
    command(ROOT, 'push', 'origin', 'main')
    remote = git(ROOT, 'ls-remote', 'origin', 'refs/heads/main').split()[0]
    assert remote == head and not git(ROOT, 'status', '--porcelain')
    command(RESTORE, 'fetch', 'origin')
    command(RESTORE, 'merge', '--ff-only', 'origin/main')
    assert git(RESTORE, 'rev-parse', 'HEAD') == head
    for item in rows.values():
        path = RESTORE/item['path']
        assert path.stat().st_size == item['bytes']
        if path.suffix.lower() not in SEALED:
            assert pin(path.read_bytes()) == item['sha256']
    assert not git(RESTORE, 'status', '--porcelain')
    record.update(status='published_and_incrementally_restored_pass', remote_main=remote, restore_head=head, source_clean=True, restore_clean=True, completed_utc=datetime.now(timezone.utc).isoformat(), ordinary_completion_scope='Precommit EOF correction and normal Git delivery only; no helper/controller/viewer/close/original publication-main rerun, no scientific payload read/hash/decode. Initial failed publication receipt retained.')
    write(AUTHOR/'publication_receipt.json', record)
    print(json.dumps({key:record[key] for key in ('status', 'execution_outcome', 'commit', 'remote_main', 'restore_head', 'manifest_files')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
