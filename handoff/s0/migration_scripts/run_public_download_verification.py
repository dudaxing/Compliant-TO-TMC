"""Read public S0 assets without GitHub authorization, then verify a fresh clone."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import traceback
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OPS = Path(__file__).resolve().parent
CLONE = ROOT / 'c2_s0_public_clone'
NETWORK_CACHE = ROOT / 'c2_s0_public_download_cache'
OLD_CACHE = ROOT / 'c2_s0_public_old_cache'
OLD_SOURCE = ROOT / 'fresh_restore_cache'
COMMIT = 'd70d5a63e3f52bda687cb73b0058a339bf16811f'


def write_new(name, value):
    with (OPS / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


class Tee:
    def __init__(self, terminal, log):
        self.terminal, self.log = terminal, log
    def write(self, text):
        self.terminal.write(text)
        self.log.write(text)
        self.log.flush()
    def flush(self):
        self.terminal.flush()
        self.log.flush()


def main():
    # Exclusive output creation ensures no previous attempt or cache is reused.
    for path in (NETWORK_CACHE, OLD_CACHE):
        if path.exists():
            raise FileExistsError(path)
    if subprocess.check_output(['git', '-C', str(CLONE), 'rev-parse', 'HEAD'], text=True).strip() != COMMIT:
        raise ValueError('Unexpected public clone commit')
    h = runpy.run_path(str(CLONE / 'tools/handoff.py'), run_name='s0_public_remote_verification')
    index = json.loads((CLONE / 'handoff/evidence_assets.json').read_text(encoding='utf-8'))
    old_assets = index['assets'][:5]
    new_assets = index['assets'][5:]
    if len(old_assets) != 5 or len(new_assets) != 6:
        raise ValueError('Expected five old and six new assets')
    network_records = []
    original_urlopen = urllib.request.urlopen
    def public_urlopen(request, *args, **kwargs):
        if not isinstance(request, urllib.request.Request):
            raise ValueError('Expected explicit public Request')
        if request.has_header('Authorization'):
            raise ValueError('Authorization is forbidden in public download verification')
        if request.full_url not in {a['url'] for a in new_assets}:
            raise ValueError('Unexpected initial public URL')
        network_records.append({'url': request.full_url,
                                'authorization_header_present': False,
                                'started_utc': datetime.now(timezone.utc).isoformat()})
        return original_urlopen(request, *args, **kwargs)
    urllib.request.urlopen = public_urlopen
    try:
        restored_new = h['fetch']([a['name'] for a in new_assets], NETWORK_CACHE, None, root=CLONE)
    finally:
        urllib.request.urlopen = original_urlopen
        write_new('public_network_requests.json', network_records)
    if len(network_records) != 6 or {r['url'] for r in network_records} != {a['url'] for a in new_assets}:
        raise ValueError('Not all six archives came from distinct public requests')
    new_verified = []
    for asset in new_assets:
        archive = NETWORK_CACHE / asset['name']
        h['check_file'](archive, asset)
        new_verified.append({'name': asset['name'], 'url': asset['url'],
                             'bytes': archive.stat().st_size, 'sha256': h['digest'](archive),
                             'source': 'unauthenticated_public_network_to_new_empty_cache',
                             'restored_member_count': len(asset['files'])})
    write_new('public_network_restore.json', {
        'schema': 'hf4-c2-s0-public-network-restore-1.0', 'status': 'pass',
        'clone_commit': COMMIT, 'cache_was_absent': True, 'cache': str(NETWORK_CACHE),
        'authorization_header_used': False, 'local_archive_source_used_for_new_assets': False,
        'requests': network_records, 'assets': new_verified, 'restoration': restored_new})
    # Historical assets are expressly reused; they are not counted as new public downloads.
    for asset in old_assets:
        h['check_file'](OLD_SOURCE / asset['name'], asset)
    restored_old = h['fetch']([a['name'] for a in old_assets], OLD_CACHE, OLD_SOURCE, root=CLONE)
    write_new('public_old_assets_reuse.json', {
        'schema': 'hf4-c2-s0-historical-reuse-1.0', 'status': 'pass',
        'source': str(OLD_SOURCE), 'cache': str(OLD_CACHE), 'network_used': False,
        'all_source_archive_hashes_checked': True, 'restoration': restored_old})
    command = [sys.executable, '-B', str(CLONE / 'tools/handoff.py'), 'verify', '--full',
               '--output', str(OPS / 'public_full_verification.json')]
    with (OPS / 'public_full_verify.stdout.log').open('x', encoding='utf-8') as stdout, \
         (OPS / 'public_full_verify.stderr.log').open('x', encoding='utf-8') as stderr:
        completed = subprocess.run(command, cwd=CLONE, stdout=stdout, stderr=stderr, check=False)
    if completed.returncode:
        raise RuntimeError('Public full verification failed; see preserved logs')
    verified = json.loads((OPS / 'public_full_verification.json').read_text(encoding='utf-8'))
    clean = not subprocess.check_output(['git', '-C', str(CLONE), 'status', '--porcelain'], text=True).strip()
    if verified['status'] != 'pass' or not clean:
        raise ValueError('Full verification or clean tracked clone requirement failed')
    receipt = {
        'schema': 'hf4-c2-s0-independent-public-clone-roundtrip-1.0', 'status': 'pass',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'actual_commit': COMMIT,
        'public_clone_root': str(CLONE), 'git_tracked_worktree_clean_after_restoration': clean,
        'new_assets_public_downloads': 6, 'new_asset_archive_bytes': sum(a['bytes'] for a in new_assets),
        'new_assets_restored_files': sum(len(a['files']) for a in new_assets),
        'old_assets_reused_from_verified_local_cache': 5,
        'old_assets_downloaded_from_network_this_run': 0,
        'full_verification_command': command, 'full_verification_returncode': completed.returncode,
        'full_verification': verified, 'script_sha256': h['digest'](Path(__file__)),
        'mechanics_run': False, 'new_high_precision_evaluation': False,
        'source_delivery_tree_changed': False, 'scientific_evidence_payload_changed': False,
        'scope': 'Fresh remote clone, six unauthenticated public asset downloads, full byte restoration; no mechanics admission.'}
    write_new('public_clone_remote_receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    with (OPS / 'public_network_restore.log').open('x', encoding='utf-8', newline='\n') as log:
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            try:
                main()
            except Exception as error:
                write_new('public_clone_remote_failure.json', {
                    'schema': 'hf4-c2-s0-public-roundtrip-failure-1.0', 'status': 'failed',
                    'error_type': type(error).__name__, 'error': str(error),
                    'created_utc': datetime.now(timezone.utc).isoformat(),
                    'partial_outputs_preserved': True, 'mechanics_run': False,
                    'new_high_precision_evaluation': False})
                traceback.print_exc()
                raise
