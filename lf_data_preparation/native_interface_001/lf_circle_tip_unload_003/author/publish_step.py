"""Publish the closed L-CTIPUNLOAD3 delta and restore it through local Git objects."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE = Path('D:/hf-restore-20260930')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_unload_003'
BASE = '2fe7a5f942454ca75acc4ddd54b5926732afcb46'
CARD = 'L-CTIPUNLOAD3'
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
          'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
          'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md']
ORDINARY = {'.py', '.json', '.jsonl', '.ndjson', '.md', '.log', '.txt'}
GIT = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']


def git(root, *args):
    return subprocess.check_output(GIT + list(args), cwd=root).decode('utf-8').strip()


def command(root, *args):
    subprocess.run(GIT + list(args), cwd=root, check=True)


def read(name):
    return json.loads((ROOT / name).read_bytes())


def digest(raw):
    return sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8', newline='\n')


def ordinary_row(name, root=ROOT):
    assert Path(name).suffix.lower() in ORDINARY, name
    raw = (root / name).read_bytes()
    return dict(path=name, bytes=len(raw), sha256=digest(raw))


def check_added_text(name, raw):
    lines = raw.decode('utf-8').splitlines()
    assert all(line == line.rstrip(' \t') for line in lines), 'Trailing whitespace: ' + name


def origins_unchanged():
    for root in (ROOT, RESTORE):
        assert git(root, 'branch', '--show-current') == 'main'
        assert git(root, 'remote', 'get-url', 'origin') == ORIGIN
        assert git(root, 'remote', 'get-url', '--push', 'origin') == ORIGIN


def push_and_restore(head, rows):
    """Remote identity and separate-path local object recovery are distinct checks."""
    command(ROOT, 'push', 'origin', 'main')
    assert git(ROOT, 'ls-remote', 'origin', 'refs/heads/main').split()[0] == head
    command(RESTORE, 'fetch', '--no-tags', str(ROOT),
            'refs/heads/main:refs/remotes/origin/main')
    command(RESTORE, 'merge', '--ff-only', 'origin/main')
    assert git(RESTORE, 'rev-parse', 'HEAD') == head
    for row in rows:
        assert (RESTORE / row['path']).stat().st_size == row['bytes'], row['path']
        if Path(row['path']).suffix.lower() in ORDINARY:
            assert ordinary_row(row['path'], RESTORE) == row, row['path']
    origins_unchanged()
    assert not git(ROOT, 'status', '--porcelain')
    assert not git(RESTORE, 'status', '--porcelain')


def main():
    receipt_file = AUTHOR / 'publication_receipt.json'
    assert not receipt_file.exists(), 'Preserve the existing publication attempt receipt'
    record = dict(card=CARD, status='publication_started', previous_delivery_commit=BASE,
                  created_utc=datetime.now(timezone.utc).isoformat())
    phase = 'closed_records_and_baseline'
    try:
        origins_unchanged()
        assert git(ROOT, 'rev-parse', 'HEAD') == git(RESTORE, 'rev-parse', 'HEAD') == BASE
        assert not git(RESTORE, 'status', '--porcelain')
        assert not git(ROOT, 'diff', '--cached', '--name-only')
        untracked = git(ROOT, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')
        assert all(not name or name.startswith(STAGE + '/') for name in untracked)
        assert set(git(ROOT, 'diff', '--name-only').splitlines()) == set(FRONTS)
        assert not git(ROOT, 'diff', BASE, '--name-only', '--', 'hf_repo/src')
        review = read(STAGE + '/author/ACTUAL_REVIEW.json')
        assert review['status'].startswith('pass')
        assert not review.get('blockers', review.get('blocking_findings', []))
        launch, closure = read(STAGE + '/step_launch.json'), read(STAGE + '/author/closure.json')
        helper_path = ROOT / STAGE / 'run_001/execution_receipt.json'
        helper = json.loads(helper_path.read_bytes()) if helper_path.is_file() else {}
        assert launch['card'] == closure['card'] == CARD
        assert launch['status'] in ('pass', 'not_pass') and launch['invocations'] == 1
        assert launch['cleanup_verified'] is True and closure['execution_closed'] is True
        assert not helper or (helper['card'] == CARD and helper['status'] in ('pass', 'not_pass'))
        assert not helper or helper['default_installations'] == helper['new_tests'] == helper['HP_calls_by_wrapper'] == 0
        outcome = 'pass' if helper.get('status') == launch['status'] == 'pass' else 'not_pass'
        assert closure['execution_status'] == review['execution_status'] == outcome
        seals = helper.get('outputs') or {}
        history = read(STAGE + '/author/front_history.json')
        assert history['source_baseline_commit'] == BASE
        assert {row['path'] for row in history['files']} == set(FRONTS)
        for row in history['files']:
            old = subprocess.check_output(GIT + ['show', BASE + ':' + row['path']], cwd=ROOT)
            current = (ROOT / row['path']).read_bytes()
            assert len(old) == row['old_bytes'] and digest(old) == row['old_sha256']
            assert current.endswith(old) and current.count(old) == 1
            check_added_text(row['path'], current[:-len(old)])

        phase = 'incremental_manifest'
        old_raw = (ROOT / MANIFEST).read_bytes()
        assert old_raw == subprocess.check_output(GIT + ['show', BASE + ':' + MANIFEST], cwd=ROOT)
        manifest = json.loads(old_raw)
        entries = {row['path']: row for row in manifest['files']}
        assert len(entries) == len(manifest['files']) == 23873
        assert manifest['schema_version'] == 'github-handoff-repository-1.0'
        assert manifest['science_version'] == '0.5.0'
        assert manifest['science_baseline_commit'] == 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
        assert not any(name.startswith(STAGE + '/') for name in entries)
        stage_files = sorted(path.relative_to(ROOT).as_posix()
                             for path in (ROOT / STAGE).rglob('*') if path.is_file())
        assert stage_files and STAGE + '/author/archive_publication.py' not in stage_files
        rows, sealed = [], []
        for name in sorted(FRONTS + stage_files):
            path = ROOT / name
            if path.suffix.lower() in ORDINARY:
                row = ordinary_row(name)
                if name.startswith(STAGE + '/'):
                    check_added_text(name, path.read_bytes())
                if name in seals:
                    assert {key: row[key] for key in ('bytes', 'sha256')} == seals[name], name
            else:
                assert name in seals, 'No original helper-window payload seal: ' + name
                pin = seals[name]
                assert path.stat().st_size == pin['bytes'], name
                row = dict(path=name, bytes=pin['bytes'], sha256=pin['sha256'])
                sealed.append(name)
            entries[name] = row
            rows.append(row)
        assert MANIFEST not in entries
        manifest.update(created_utc=datetime.now(timezone.utc).isoformat(),
            storage_stage='l_ctipunload3_saved_circle_suffix_closed_001', previous_delivery_commit=BASE,
            files=sorted(entries.values(), key=lambda row: row['path']))
        save(ROOT / MANIFEST, manifest)
        rows.append(ordinary_row(MANIFEST))
        record.update(status='ready_to_stage', execution_outcome=outcome, helper_status=helper.get('status'),
            outer_status=launch['status'], output_identity_seal=helper.get('output_identity_seal'),
            inherited_baseline_entries=23873, old_manifest_sha256=digest(old_raw), delta_files=rows,
            manifest_files=len(entries), manifest_total_bytes=sum(row['bytes'] for row in entries.values()),
            sealed_payload_paths=sealed, new_default_HF_files=[],
            payload_identity_policy='Original helper producer seals plus stat only; no scientific/media/CSV payload hashing or decoding after its window.',
            restore_transport='Local Git object fetch from source checkout, then ff-only; remote main verified independently. This is a different-path recovery check, not an independent-machine or remote-object-download test.',
            git_object_IO_scope='Git object and transport reads are outside the wrapper payload-read statement; auto-maintenance is disabled per command.')
        save(receipt_file, record)
        phase = 'stage_commit_push_restore'
        names = [row['path'] for row in rows]
        command(ROOT, 'add', '-f', '--', *names)
        assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == set(names)
        command(ROOT, 'diff', '--cached', '--check')
        command(ROOT, 'commit', '-m', 'Unload tip-facing circle from saved 1.00 to zero through five targets and visualize response')
        head = git(ROOT, 'rev-parse', 'HEAD')
        record.update(status='committed', commit=head)
        save(receipt_file, record)
        push_and_restore(head, rows)
        record.update(status='published_and_incrementally_restored_pass', remote_main=head,
            restore_head=head, source_clean=True, restore_clean=True,
            completed_utc=datetime.now(timezone.utc).isoformat())
        save(receipt_file, record)
        print(json.dumps({key: record[key] for key in ('status', 'execution_outcome', 'commit',
            'remote_main', 'restore_head', 'manifest_files', 'manifest_total_bytes')}), flush=True)
    except BaseException as error:
        record.update(status='publication_stopped', failure_phase=phase,
            error=dict(exception_class=type(error).__name__, reason=str(error)),
            no_automatic_retry_rollback_or_force_push=True,
            stopped_utc=datetime.now(timezone.utc).isoformat())
        save(receipt_file, record)
        raise


if __name__ == '__main__':
    main()
