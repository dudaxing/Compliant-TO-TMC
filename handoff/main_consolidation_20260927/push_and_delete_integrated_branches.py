"""Publish main normally, then delete only unchanged tips already in main.

Deletion uses atomic compare-and-swap leases; no main history is force-pushed.
Run only after the main consolidation regression and recovery checks pass.
"""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--worktree', type=Path, required=True)
parser.add_argument('--receipt', type=Path, required=True)
args = parser.parse_args()
ROOT = args.worktree.resolve()
EXPECTED_ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
BEFORE = json.loads((ROOT/'handoff/main_consolidation_20260927/remote_before_mutation.json').read_text(encoding='utf-8'))
RECEIPT = args.receipt.resolve()
assert not RECEIPT.exists(), 'Preserve every prior attempt; inspect instead of overwriting'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def refs(kind):
    return {line.split()[1]: line.split()[0] for line in git('ls-remote', kind, 'origin').splitlines()}


def save():
    RECEIPT.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')


assert git('remote', 'get-url', 'origin') == EXPECTED_ORIGIN
assert git('remote', 'get-url', '--push', 'origin') == EXPECTED_ORIGIN
assert git('branch', '--show-current') == 'main'
assert not git('status', '--porcelain=v1'), 'Main worktree must be clean'
head = git('rev-parse', 'HEAD')
targets = {ref: sha for ref, sha in BEFORE['heads'].items() if ref != 'refs/heads/main'}
assert len(targets) == 6
assert refs('--heads') == BEFORE['heads'], 'A remote tip changed; inspect new work before deleting'
for ref, sha in targets.items():
    subprocess.run(['git', 'merge-base', '--is-ancestor', sha, head], cwd=ROOT, check=True)
assert refs('--tags') == BEFORE['tags'], 'Tags changed; inspect before mutation'
receipt = dict(schema='main-integrated-branch-cleanup-v1', status='preflight_pass',
               started_utc=datetime.now(timezone.utc).isoformat(), origin=EXPECTED_ORIGIN,
               main_payload_commit=head, ancestor_checked_tips=targets,
               deletion_policy='atomic leased deletion of exact tips; normal main push; preserve all tags and local worktrees')
save()
try:
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT, check=True)
    expected = {**BEFORE['heads'], 'refs/heads/main': head}
    assert refs('--heads') == expected, 'Unexpected remote movement after main push'
    receipt['status'] = 'main_pushed_all_tips_saved'; save()
    command = ['git', 'push', '--atomic', *[
        '--force-with-lease='+ref+':'+sha for ref, sha in targets.items()],
        'origin', *[':'+ref for ref in targets]]
    receipt['deletion_command'] = command; save()
    subprocess.run(command, cwd=ROOT, check=True)
    after = refs('--heads')
    assert after == {'refs/heads/main': head}
    assert refs('--tags') == BEFORE['tags'], 'Historical tags unexpectedly changed'
    receipt.update(status='pass', deleted_branches=list(targets), remote_heads_after=after,
                   tags_unchanged=True, local_worktrees_removed=False,
                   finished_utc=datetime.now(timezone.utc).isoformat())
    save()
    print(json.dumps(receipt, indent=2), flush=True)
except Exception as error:
    receipt.update(status='failed_preserved', error_type=type(error).__name__)
    save()
    raise
