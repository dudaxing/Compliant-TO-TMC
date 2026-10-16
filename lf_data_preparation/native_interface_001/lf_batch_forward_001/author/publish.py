"""Publish the closed L-BFWD1 delta, preserving its actual pass or partial failure."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE = Path('D:/hf-restore-20260930')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_batch_forward_001'
BASE = 'ff448447a135d31314f7a0bd88e6ddd8ed449bfb'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
          'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md', 'docs/L_USE1_NEXT_STEP_PLAN.md']
NEW = []  # This stage installs or modifies no default HF files.
REVIEW_JSON = STAGE + '/author/ACTUAL_REVIEW.json'
LAUNCH_JSON = STAGE + '/batch_launch.json'
SEALED_ONLY_SUFFIXES = {'.npz', '.png', '.gif', '.gz', '.csv', '.zip'}


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root).decode('utf-8').strip()


def read(name):
    return json.loads((ROOT/name).read_bytes())


def digest(raw):
    return sha256(raw).hexdigest()


def save(record):
    (AUTHOR/'publication_receipt.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


def main():
    record = dict(status='publication_started', previous_delivery_commit=BASE,
                  created_utc=datetime.now(timezone.utc).isoformat())
    phase = 'closed_records_and_baseline'
    try:
        assert git(ROOT, 'rev-parse', 'HEAD') == git(RESTORE, 'rev-parse', 'HEAD') == BASE
        assert not git(RESTORE, 'status', '--porcelain')
        assert git(ROOT, 'remote', 'get-url', '--push', 'origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
        assert not git(ROOT, 'diff', '--cached', '--name-only')
        review = read(REVIEW_JSON)
        assert review['status'].startswith('pass') and not review.get('blocking_findings', [])
        receipt = read(STAGE+'/run_001/execution_receipt.json')
        launch = read(LAUNCH_JSON)
        closure = read(STAGE+'/author/closure.json')
        assert receipt['card'] == launch['card'] == closure['card'] == 'L-BFWD1'
        assert receipt['status'] in ('pass', 'not_pass')
        assert launch['status'] in ('pass', 'not_pass') and launch['invocations'] == 1
        assert launch.get('cleanup_verified') is True
        assert closure['status'] not in ('running', 'preparing')
        outcome = 'pass' if receipt['status'] == launch['status'] == 'pass' else 'not_pass'
        assert review.get('execution_status', outcome) == outcome
        assert closure.get('execution_status', outcome) == outcome
        assert receipt['output_identity_seal'] in (
            'complete_inside_original_helper_window', 'actual_partial_inside_original_helper_window',
            'not_complete_before_resource_close', 'not_complete')
        record.update(execution_outcome=outcome, helper_status=receipt['status'],
                      outer_status=launch['status'], output_identity_seal=receipt['output_identity_seal'])
        assert set(git(ROOT, 'diff', '--name-only').splitlines()) == set(FRONTS)
        history = read(STAGE+'/author/front_history.json')
        assert history['source_baseline_commit'] == BASE
        assert {row['path'] for row in history['files']} == set(FRONTS)
        for row in history['files']:
            old = subprocess.check_output(['git', 'show', BASE+':'+row['path']], cwd=ROOT)
            current = (ROOT/row['path']).read_bytes()
            assert len(old) == row['old_bytes'] and digest(old) == row['old_sha256']
            assert current.endswith(old) and current.count(old) == 1

        phase = 'incremental_identity_manifest'
        old_raw = (ROOT/MANIFEST).read_bytes()
        assert old_raw == subprocess.check_output(['git', 'show', BASE+':'+MANIFEST], cwd=ROOT)
        manifest = json.loads(old_raw)
        entries = {row['path']:row for row in manifest['files']}
        assert len(entries) == len(manifest['files']) == 21236
        assert manifest['schema_version'] == 'github-handoff-repository-1.0'
        assert manifest['science_version'] == '0.5.0'
        assert manifest['science_baseline_commit'] == 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
        stage_files = sorted(path.relative_to(ROOT).as_posix()
                             for path in (ROOT/STAGE).rglob('*') if path.is_file())
        assert stage_files
        names = sorted(FRONTS+NEW+stage_files)
        assert len(names) == len(set(names))
        rows, sealed_payloads = [], []
        for name in names:
            path = ROOT/name
            if path.suffix.lower() in SEALED_ONLY_SUFFIXES:
                # Absence of a producer seal blocks publication; never invent/recompute a closed-window identity.
                assert name in receipt['outputs'], 'No original-window seal for scientific/media file: '+name
                seal = receipt['outputs'][name]
                assert path.stat().st_size == seal['bytes'], name
                row = dict(path=name, sha256=seal['sha256'], bytes=seal['bytes'])
                sealed_payloads.append(dict(path=name,
                    identity_basis='Original L-BFWD1 helper-window seal plus publication stat only; no payload hash/decode'))
            else:
                raw = path.read_bytes()
                row = dict(path=name, bytes=len(raw), sha256=digest(raw))
                if name in receipt['outputs']:
                    assert {key:row[key] for key in ('bytes', 'sha256')} == receipt['outputs'][name], name
            rows.append(row)
            entries[name] = row
        assert MANIFEST not in entries
        manifest.update(created_utc=datetime.now(timezone.utc).isoformat(),
            storage_stage='l_bfwd1_actual_batch_forward_closed_001', previous_delivery_commit=BASE,
            files=sorted(entries.values(), key=lambda row:row['path']))
        (ROOT/MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n',
                                  encoding='utf-8', newline='\n')
        raw = (ROOT/MANIFEST).read_bytes()
        rows.append(dict(path=MANIFEST, bytes=len(raw), sha256=digest(raw)))
        record.update(status='ready_to_stage', delta_files=rows, sealed_payload_identity_policy=sealed_payloads,
            old_manifest_sha256=digest(old_raw), inherited_baseline_entries=21236,
            manifest_files=len(entries), manifest_total_bytes=sum(row['bytes'] for row in entries.values()),
            new_default_HF_files=NEW,
            inheritance_basis='Historical entries inherited; only six fronts and the new stage updated. Actual pass/not_pass and partial output facts preserved; no old/default HF source or original result changed, no historical scientific payload reread.')
        save(record)

        phase = 'stage_and_commit'
        subprocess.run(['git', 'add', '-f', '--', *[row['path'] for row in rows]], cwd=ROOT, check=True)
        assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == {row['path'] for row in rows}
        subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
        subprocess.run(['git', 'commit', '-m', 'Record actual short-load batch consumption and saved views'], cwd=ROOT, check=True)
        head = git(ROOT, 'rev-parse', 'HEAD')
        record.update(status='committed', commit=head)
        save(record)
        phase = 'push_main'
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT, check=True)
        remote = git(ROOT, 'ls-remote', 'origin', 'refs/heads/main').split()[0]
        assert remote == head and not git(ROOT, 'status', '--porcelain')
        record.update(status='pushed', remote_main=remote)
        save(record)

        phase = 'incremental_restore'
        assert git(RESTORE, 'rev-parse', 'HEAD') == BASE and not git(RESTORE, 'status', '--porcelain')
        subprocess.run(['git', 'fetch', 'origin'], cwd=RESTORE, check=True)
        subprocess.run(['git', 'merge', '--ff-only', 'origin/main'], cwd=RESTORE, check=True)
        assert git(RESTORE, 'rev-parse', 'HEAD') == head
        for row in rows:
            path = RESTORE/row['path']
            assert path.stat().st_size == row['bytes'], row['path']
            if path.suffix.lower() not in SEALED_ONLY_SUFFIXES:
                assert digest(path.read_bytes()) == row['sha256'], row['path']
        assert not git(RESTORE, 'status', '--porcelain')
        record.update(status='published_and_incrementally_restored_pass', restore_head=head,
            source_clean=True, restore_clean=True,
            restore_verification='Delta ordinary source/JSON/MD/log SHA; scientific/media stat plus original helper-window seal. No science execution, payload rehash/decode or pixel reinspection.',
            completed_utc=datetime.now(timezone.utc).isoformat())
        save(record)
        print(json.dumps({key:record[key] for key in ('status', 'execution_outcome', 'commit',
            'remote_main', 'restore_head', 'manifest_files', 'manifest_total_bytes')}), flush=True)
    except BaseException as error:
        record.update(status='publication_stopped', failure_phase=phase,
                      error=dict(exception_class=type(error).__name__, reason=str(error)),
                      no_automatic_retry_rollback_or_force=True,
                      stopped_utc=datetime.now(timezone.utc).isoformat())
        save(record)
        raise


if __name__ == '__main__':
    main()
