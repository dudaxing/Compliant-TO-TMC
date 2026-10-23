"""Bound the complete original window and seal new full/partial evidence once."""
import time
START=time.monotonic()

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

BASE=Path(__file__).resolve().parent
def read(path): return json.loads(Path(path).read_bytes())
def write(path,row):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(row,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')
def identity(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def passed(row):
    proof=row.get('cleanup_proof',{})
    return (row.get('reason')=='normal_exit' and row.get('returncode')==0
        and row.get('cleanup_verified') is True and proof.get('pass') is True
        and proof.get('job_handle_closed') is True)

def main():
    if len(sys.argv)!=1 or any((BASE/name).exists() for name in
            ('top_start.json','run_001','helper_start.json','root_qa.json','execution_evidence.zip')):
        raise FileExistsError('Unique original authorized launch only; no retry or reopening')
    write(BASE/'top_start.json',dict(stage='L-CTIPFREAL1',start_monotonic=START,
        started_utc=datetime.now(timezone.utc).isoformat(),outer_seconds=2760,
        helper_seconds=2700,execution_attempt=1,external_retries=0))
    p=read(BASE/'protocol.json')
    for row in p['bindings']:
        if identity(row['path'])!={k:row[k] for k in ('bytes','sha256')}:
            raise ValueError('Frozen source mismatch: '+row['path'])
    if time.monotonic()>=START+20:
        raise TimeoutError('Original top bootstrap reserve exceeded')
    from windows_owned_process_sup2 import run_owned
    env=os.environ.copy(); env.update(p['thread_environment']); env['PYTHONDONTWRITEBYTECODE']='1'
    supervised=run_owned([p['python_executable'],'-X','utf8','-B',str(BASE/'helper_freal1.py')],
        cwd=str(BASE),env=env,log=BASE/'helper.log',deadline=START+2630,seconds=2630,
        rss_limit=p['memory_limit_bytes'],instance_log_path=BASE/'helper.instances.ndjson',
        instance_identity=dict(stage='L-CTIPFREAL1',phase='entire_original_helper_tree'))
    write(BASE/'top_supervision.json',supervised)
    proof=supervised.get('cleanup_proof',{})
    clean=(supervised.get('cleanup_verified') is True and proof.get('pass') is True
           and proof.get('job_handle_closed') is True)
    ok=passed(supervised)
    if ok:
        ok=(read(BASE/'helper_receipt.json')['status']=='pass'
            and all(passed(read(BASE/'run_001'/name)) for name in
                    ('science_supervision.json','comparison_supervision.json','viewer_supervision.json')))
    origin=read(BASE/'helper_start.json')['start_monotonic'] if (BASE/'helper_start.json').exists() else None
    seal=dict(stage='L-CTIPFREAL1',status='not_started',attempts=0,execution_pass=ok,
        original_helper_seconds=2700,original_outer_seconds=2760,numerical_retries=0,
        archive_scope='Only new runtime files; original LOW1 scientific packages are neither copied nor sealed again',
        scientific_payloads_read_as_original_bytes_only=True,production_modifications=0)
    # The complete helper Job is gone before reading any evidence file for sealing.
    # The new NPZ are transported as bytes; the original three/four input read sets
    # belong only to science/comparison and are never revisited here.
    if clean and origin is not None and time.monotonic()<origin+2645:
        seal['attempts']=1; members=[]
        try:
            excluded={'execution_evidence.zip','EVIDENCE_MANIFEST.json','seal_receipt.json'}
            paths=sorted(path for path in BASE.rglob('*') if path.is_file()
                         and path.relative_to(BASE).as_posix() not in excluded)
            with zipfile.ZipFile(BASE/'execution_evidence.zip','x',zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
                for path in paths:
                    if time.monotonic()>=origin+2680:
                        raise TimeoutError('Original evidence-member sealing margin closed')
                    raw=path.read_bytes(); name=path.relative_to(BASE).as_posix()
                    archive.writestr(name,raw)
                    members.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
            if time.monotonic()>=origin+2690:
                raise TimeoutError('Original archive-identity margin closed')
            archived=identity(BASE/'execution_evidence.zip')
            write(BASE/'EVIDENCE_MANIFEST.json',dict(stage='L-CTIPFREAL1',
                archive=dict(path='execution_evidence.zip',**archived),members=members,
                scope='Stable original new full/partial bytes after complete same-instance helper-tree cleanup; no scientific decode'))
            seal.update(status='pass',archive=archived,members=len(members))
        except BaseException as error:
            seal.update(status='failed_once_no_retry',error=dict(type=type(error).__name__,message=str(error)),
                members_written_before_error=len(members))
    else:
        seal['status']='skipped_cleanup_unproven_or_original_window_closed'
    seal.update(elapsed_outer_seconds=time.monotonic()-START,
        elapsed_helper_seconds=None if origin is None else time.monotonic()-origin)
    if seal['status']=='pass' and (seal['elapsed_outer_seconds']>=2760 or seal['elapsed_helper_seconds']>=2700):
        seal['status']='failed_original_window_exceeded'
    write(BASE/'seal_receipt.json',seal)
    print(json.dumps(dict(execution_pass=ok,outer_reason=supervised['reason'],
        outer_returncode=supervised['returncode'],seal_status=seal['status'],
        elapsed_outer_seconds=seal['elapsed_outer_seconds'])),flush=True)
    return 0 if ok and seal['status']=='pass' else 1

if __name__=='__main__':
    raise SystemExit(main())
