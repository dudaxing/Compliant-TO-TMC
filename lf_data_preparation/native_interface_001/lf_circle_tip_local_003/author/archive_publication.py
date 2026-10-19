"""Archive the completed L-CTIPLOCAL3 ordinary publication receipt in a second commit."""
from datetime import datetime, timezone
import json
from publish_local import (AUTHOR, CARD, MANIFEST, ROOT, RESTORE, STAGE,
    command, git, origins_unchanged, ordinary_row, check_added_text, push_and_restore, save)


def main():
    result_file = AUTHOR / 'publication_archive_receipt.json'
    assert not result_file.exists(), 'Preserve the existing archive attempt receipt'
    result = dict(card=CARD, status='publication_archive_started',
                  created_utc=datetime.now(timezone.utc).isoformat())
    phase = 'publication_receipt_and_baseline'
    try:
        record = json.loads((AUTHOR / 'publication_receipt.json').read_bytes())
        assert record['card'] == CARD and record['status'] == 'published_and_incrementally_restored_pass'
        base = record['commit']
        origins_unchanged()
        assert git(ROOT, 'rev-parse', 'HEAD') == git(RESTORE, 'rev-parse', 'HEAD') == base
        assert not git(ROOT, 'status', '--porcelain') and not git(RESTORE, 'status', '--porcelain')
        manifest = json.loads((ROOT / MANIFEST).read_bytes())
        assert len(manifest['files']) == record['manifest_files']
        entries = {row['path']: row for row in manifest['files']}
        rows = []
        for item in ('publication_receipt.json', 'archive_publication.py'):
            name = STAGE + '/author/' + item
            assert name not in entries and not (ROOT / name).exists()
            raw = (AUTHOR / item).read_bytes()
            check_added_text(name, raw)
            with (ROOT / name).open('xb') as stream:
                stream.write(raw)
            row = ordinary_row(name)
            entries[name] = row
            rows.append(row)
        manifest.update(previous_delivery_commit=base,
            storage_stage='l_ctiplocal3_publication_receipt_archived_001',
            created_utc=datetime.now(timezone.utc).isoformat(),
            files=sorted(entries.values(), key=lambda row: row['path']))
        save(ROOT / MANIFEST, manifest)
        rows.append(ordinary_row(MANIFEST))
        assert not git(ROOT, 'diff', '--name-only', '--', 'hf_repo/src')
        phase = 'archive_commit_push_restore'
        names = [row['path'] for row in rows]
        command(ROOT, 'add', '-f', '--', *names)
        assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == set(names)
        command(ROOT, 'diff', '--cached', '--check')
        command(ROOT, 'commit', '-m', 'Archive circle 1.05 and 1.06 mm localization publication and local Git restore receipt')
        head = git(ROOT, 'rev-parse', 'HEAD')
        result.update(status='archive_committed', commit=head, execution_delivery_commit=base)
        save(result_file, result)
        push_and_restore(head, rows)
        result.update(status='ordinary_publication_receipt_archived_and_restored',
            execution_outcome=record['execution_outcome'], remote_main=head, restore_head=head,
            restore_transport=record['restore_transport'], manifest_files=len(entries),
            source_clean=True, restore_clean=True, completed_utc=datetime.now(timezone.utc).isoformat())
        save(result_file, result)
        print(json.dumps(result), flush=True)
    except BaseException as error:
        result.update(status='publication_archive_stopped', failure_phase=phase,
            error=dict(exception_class=type(error).__name__, reason=str(error)),
            no_automatic_retry_rollback_or_force_push=True,
            stopped_utc=datetime.now(timezone.utc).isoformat())
        save(result_file, result)
        raise


if __name__ == '__main__':
    main()
