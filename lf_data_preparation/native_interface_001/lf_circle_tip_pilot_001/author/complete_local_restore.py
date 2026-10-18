"""Complete different-path restore from committed local Git objects after remote fetch EOF."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE=Path('D:/hf-restore-20260930')
AUTHOR=Path(__file__).resolve().parent
BASE='036fd5d9298525894b5f90a37dab8f258d6cc9b1'
SEALED={'.npz','.png','.gif','.gz','.csv','.zip'}


def git(root,*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=root,text=True).strip()


def run(root,*args):
    subprocess.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=root,check=True)


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    raw=(AUTHOR/'publication_receipt.json').read_bytes();record=json.loads(raw)
    assert record['status']=='ordinary_publication_continuation_stopped' and record['failure_phase']=='incremental_restore'
    head=record['commit']
    assert git(ROOT,'rev-parse','HEAD')==head and git(RESTORE,'rev-parse','HEAD')==BASE
    assert not git(ROOT,'status','--porcelain') and not git(RESTORE,'status','--porcelain')
    url='https://github.com/dudaxing/Compliant-TO-TMC.git'
    assert git(ROOT,'remote','get-url','--push','origin')==git(RESTORE,'remote','get-url','origin')==url
    remote=git(ROOT,'ls-remote','origin','refs/heads/main').split()[0]
    assert remote==head
    with (AUTHOR/'publication_restore_attempt_001.json').open('xb') as output:output.write(raw)
    run(RESTORE,'fetch','--no-tags',str(ROOT),'refs/heads/main:refs/remotes/origin/main')
    run(RESTORE,'merge','--ff-only','origin/main')
    assert git(RESTORE,'rev-parse','HEAD')==head
    for row in record['delta_files']:
        path=RESTORE/row['path'];assert path.stat().st_size==row['bytes'],row['path']
        if path.suffix.lower() not in SEALED:assert sha256(path.read_bytes()).hexdigest()==row['sha256'],row['path']
    assert not git(ROOT,'status','--porcelain') and not git(RESTORE,'status','--porcelain')
    recovery=dict(card='L-CTIPPILOT1',status='local_git_restore_verified',commit=head,remote_main_verified=remote,
        remote_fetch_terminal='7fd74c',remote_fetch_error='curl56 schannel server closed abruptly; early EOF; invalid index-pack output',
        cancellation_observer_terminal='5a4c87',cancellation_observer='No matching live fetch found; assertion stopped before opening a process handle or terminating anything',
        processes_terminated=0,scientific_reexecutions=0,scientific_or_media_payload_wrapper_reads=0,
        failed_restore_receipt_sha256=sha256(raw).hexdigest(),
        restore_transport='Local committed Git source path; origin URL unchanged; remote main independently verified with ls-remote',
        restore_verification='Delta ordinary SHA; scientific/media/CSV stat plus original helper seal. Git object I/O outside wrapper read statement.',
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'RESTORE_TRANSPORT_RECOVERY.json',recovery)
    record.update(status='published_and_incrementally_restored_pass',remote_main=head,restore_head=head,
        source_clean=True,restore_clean=True,restore_transport_recovery=recovery,completed_utc=recovery['completed_utc'])
    write(AUTHOR/'publication_receipt.json',record)
    print(json.dumps(dict(status=record['status'],commit=head,restore_transport='local Git',source_clean=True,restore_clean=True)),flush=True)


if __name__=='__main__':main()
