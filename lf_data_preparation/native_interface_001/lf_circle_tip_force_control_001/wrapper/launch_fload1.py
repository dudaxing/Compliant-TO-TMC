"""Bound the entire FLOAD1 tree, then seal once in the original helper clock."""
import time
START=time.monotonic()

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

BASE=Path(__file__).resolve().parent

def read(path):
    return json.loads(Path(path).read_bytes())

def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')

def identity(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def main():
    if len(sys.argv)!=1 or any((BASE/name).exists() for name in
            ('top_start.json','run_001','outer_start.json','execution_evidence.zip','root_qa.json')):
        raise ValueError('Unique original launch only; no alternate arguments or reopened output')
    write(BASE/'top_start.json',dict(stage='L-CTIPFLOAD1',start_monotonic=START,
        start_utc=datetime.now(timezone.utc).isoformat(),outer_seconds=540,helper_seconds=480,
        helper_clock_origin='outer_fload1 first executable line before its imports',execution_attempt=1))
    p=read(BASE/'protocol.json')
    for item in p['bindings']:
        if identity(item['path'])!={k:item[k] for k in ('bytes','sha256')}:
            raise ValueError('Frozen source changed: '+item['path'])
    from windows_owned_process_sup2 import run_owned
    env=os.environ.copy()
    env.update(p['thread_environment'])
    env['PYTHONDONTWRITEBYTECODE']='1'
    outer=run_owned([p['python_executable'],'-X','utf8','-B',str(BASE/'outer_fload1.py')],
        cwd=str(BASE),env=env,log=BASE/'outer.log',deadline=START+460.,seconds=460.,
        rss_limit=p['memory_limit_bytes'],instance_log_path=BASE/'outer.instances.ndjson',
        instance_identity=dict(stage='L-CTIPFLOAD1',phase='outer540_including_shared480'))
    write(BASE/'top_supervision.json',outer)
    proof=outer.get('cleanup_proof',{})
    clean=outer.get('cleanup_verified') is True and proof.get('pass') is True and proof.get('job_handle_closed') is True
    ok=clean and outer.get('reason')=='normal_exit' and outer.get('returncode')==0
    origin=read(BASE/'outer_start.json')['start_monotonic'] if (BASE/'outer_start.json').exists() else None
    installation=dict(stage='L-CTIPFLOAD1',status='not_started',installed=[],
        all_four_cleanup_proofs_required=True,automatic_rollback=False)
    if ok:
        try:
            def install_clock():
                if origin is None or time.monotonic()>=origin+455.:
                    raise TimeoutError('Original installation margin closed')
            install_clock()
            # The numerical tree is gone and all four handles are proved
            # closed before any formal production target is created.
            from run_fload1 import passed
            for receipt in (BASE/'outer_supervision.json',BASE/'run_001/tests_supervision.json',
                            BASE/'run_001/viewer_supervision.json'):
                if not passed(read(receipt)):
                    raise ValueError('An inner supervision proof did not pass')
            root=Path(p['root_repository'])
            head=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',
                'rev-parse','HEAD'],cwd=root).decode().strip()
            if head!=p['baseline']:
                raise ValueError('Formal baseline changed; do not install')
            for old in p['original_production']:
                if identity(old['path'])!={k:old[k] for k in ('bytes','sha256')}:
                    raise ValueError('Old production bytes changed; do not install')
            for item in p['install_files']:
                if Path(item['target']).exists() or identity(item['source'])!={k:item[k] for k in ('bytes','sha256')}:
                    raise ValueError('Target exists or new candidate differs; do not install')
            for item in p['install_files']:
                install_clock()
                with Path(item['target']).open('xb') as stream:
                    stream.write(Path(item['source']).read_bytes())
                actual=identity(item['target'])
                installation['installed'].append(dict(path=item['target'],**actual))
                if actual!={k:item[k] for k in ('bytes','sha256')}:
                    raise ValueError('Installed bytes differ; retain actual partial installation')
            installation.update(status='pass',original_source_files_unchanged=55,default_entry_changed=False)
        except BaseException as error:
            ok=False
            installation.update(status='failed_no_rollback',error=dict(type=type(error).__name__,message=str(error)))
    installation['elapsed_helper_seconds']=None if origin is None else time.monotonic()-origin
    write(BASE/'installation_receipt.json',installation)
    seal=dict(stage='L-CTIPFLOAD1',status='not_started',attempts=0,outer_pass=ok,
        scientific_payloads_read_as_bytes_only=True,numerical_retries=0)
    if clean and origin is not None and time.monotonic()<origin+465.:
        members=[]
        seal['attempts']=1
        try:
            excluded={'execution_evidence.zip','EVIDENCE_MANIFEST.json','seal_receipt.json'}
            paths=sorted(x for x in BASE.rglob('*') if x.is_file()
                         and x.relative_to(BASE).as_posix() not in excluded)
            with zipfile.ZipFile(BASE/'execution_evidence.zip','x',zipfile.ZIP_DEFLATED) as archive:
                for path in paths:
                    if time.monotonic()>=origin+475.:
                        raise TimeoutError('Original shared helper seal deadline reached')
                    raw=path.read_bytes(); name=path.relative_to(BASE).as_posix()
                    archive.writestr(name,raw)
                    members.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
            if time.monotonic()>=origin+478.:
                raise TimeoutError('No original margin for archive identity and receipt')
            archived=identity(BASE/'execution_evidence.zip')
            write(BASE/'EVIDENCE_MANIFEST.json',dict(stage='L-CTIPFLOAD1',
                archive=dict(path='execution_evidence.zip',**archived),members=members,
                scope='Stable original full/partial bytes after complete outer tree same-instance cleanup; no NPZ decode'))
            seal.update(status='pass',archive=archived,members=len(members))
        except BaseException as error:
            seal.update(status='failed_once_no_retry',error=dict(type=type(error).__name__,message=str(error)),
                members_written_before_error=len(members))
    else:
        seal['status']='skipped_cleanup_unproven_or_original_helper_window_closed'
    seal.update(elapsed_outer_seconds=time.monotonic()-START,
        elapsed_helper_seconds=None if origin is None else time.monotonic()-origin)
    if seal['status']=='pass' and (seal['elapsed_helper_seconds']>=480 or seal['elapsed_outer_seconds']>=540):
        seal['status']='failed_original_window_exceeded'
    write(BASE/'seal_receipt.json',seal)
    print(json.dumps(dict(outer_pass=ok,reason=outer['reason'],returncode=outer['returncode'],
        seal_status=seal['status'],elapsed=seal['elapsed_outer_seconds'])),flush=True)
    return 0 if ok and seal['status']=='pass' else 1

if __name__=='__main__':
    raise SystemExit(main())
