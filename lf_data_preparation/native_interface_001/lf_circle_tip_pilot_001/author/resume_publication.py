"""Continue ordinary publication after a documented, one-space Git-format correction."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE=Path('D:/hf-restore-20260930')
AUTHOR=Path(__file__).resolve().parent
STAGE='lf_data_preparation/native_interface_001/lf_circle_tip_pilot_001'
BASE='036fd5d9298525894b5f90a37dab8f258d6cc9b1'
MANIFEST='handoff/repository_manifest.json'
FRONTS=['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/PHYSICAL_FUNCTION_PROGRESS.md',
    'docs/RESUME_DEVELOPMENT.md','docs/L_USE1_NEXT_STEP_PLAN.md','docs/L_BFWD1_NEXT_STEP_PLAN.md']
SEALED={'.npz','.png','.gif','.gz','.csv','.zip'}
read=lambda path:json.loads(path.read_bytes())
pin=lambda raw:sha256(raw).hexdigest()


def git(root,*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=root,text=True).strip()


def run(root,*args):
    subprocess.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=root,check=True)


def save(record):
    (AUTHOR/'publication_receipt.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    record=dict(status='ordinary_publication_continuation_started',previous_delivery_commit=BASE,
        created_utc=datetime.now(timezone.utc).isoformat(),execution_outcome='pass',
        scientific_reexecution=False,failed_attempt_file=STAGE+'/author/publication_attempt_001.json',
        correction_file=STAGE+'/author/PUBLICATION_CORRECTION.json',
        correction_review_file=STAGE+'/author/PUBLICATION_CORRECTION_REVIEW.json')
    phase='validate_existing_staged_attempt'
    try:
        assert git(ROOT,'rev-parse','HEAD')==git(RESTORE,'rev-parse','HEAD')==BASE
        assert not git(RESTORE,'status','--porcelain')
        assert git(ROOT,'branch','--show-current')=='main'
        assert git(ROOT,'remote','get-url','--push','origin')=='https://github.com/dudaxing/Compliant-TO-TMC.git'
        failed=read(AUTHOR/'publication_attempt_001.json')
        assert failed['status']=='publication_stopped' and failed['failure_phase']=='stage_and_commit'
        assert (ROOT/STAGE/'author/publication_attempt_001.json').read_bytes()==(AUTHOR/'publication_attempt_001.json').read_bytes()
        assert set(git(ROOT,'diff','--cached','--name-only').splitlines())=={row['path'] for row in failed['delta_files']}
        correction=read(AUTHOR/'PUBLICATION_CORRECTION.json')
        assert pin((AUTHOR/'publication_attempt_001.json').read_bytes())==correction['publication_attempt_001_sha256']
        corrected=(AUTHOR/'prepare_document_sources.py').read_bytes()
        assert corrected==(ROOT/STAGE/'author/prepare_document_sources.py').read_bytes()
        assert len(corrected)==correction['new_bytes'] and pin(corrected)==correction['new_sha256']
        review=read(AUTHOR/'PUBLICATION_CORRECTION_REVIEW.json')
        assert review['status'].startswith('pass') and not review['blocking_findings']
        for name,expected in review['reviewed_author_sha256'].items():assert pin((AUTHOR/name).read_bytes())==expected,name
        for name in ('PUBLICATION_CORRECTION_REVIEW.json','PUBLICATION_CORRECTION_REVIEW.md','resume_publication.py'):
            (ROOT/STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
        protocol=read(ROOT/STAGE/'protocol.json')
        for name,expected in protocol['source_bindings'].items():assert pin((ROOT/name).read_bytes())==expected,name
        launch=read(ROOT/STAGE/'pilot_launch.json')
        receipt=read(ROOT/STAGE/'run_001/execution_receipt.json')
        assert launch['status']==receipt['status']=='pass' and launch['cleanup_verified'] and launch['invocations']==1
        assert receipt['cached_production_gates']['passed'] and receipt['new_tests']==receipt['default_installations']==receipt['HP_calls_by_wrapper']==0
        final_review=read(ROOT/STAGE/'author/FINAL_DOC_REVIEW.json')
        assert final_review['status'].startswith('pass') and not final_review['blocking_findings']
        assert not git(ROOT,'diff',BASE,'--name-only','--','hf_repo/src','hf_repo/scripts','hf_repo/tests','hf_repo/pyproject.toml')
        for row in read(ROOT/STAGE/'author/front_history.json')['files']:
            old=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',BASE+':'+row['path']],cwd=ROOT)
            current=(ROOT/row['path']).read_bytes()
            assert pin(old)==row['old_sha256'] and current.endswith(old) and current.count(old)==1
        changed=git(ROOT,'diff','HEAD','--name-only').splitlines()
        assert all(name in FRONTS+[MANIFEST] or name.startswith(STAGE+'/') for name in changed)
        others=git(ROOT,'ls-files','--others','--exclude-standard').splitlines()
        assert all(name.startswith(STAGE+'/') for name in others)
        phase='corrected_incremental_manifest'
        old_raw=(ROOT/MANIFEST).read_bytes()
        manifest_row=next(row for row in failed['delta_files'] if row['path']==MANIFEST)
        assert len(old_raw)==manifest_row['bytes'] and pin(old_raw)==manifest_row['sha256']
        manifest=json.loads(old_raw);entries={row['path']:row for row in manifest['files']}
        baseline=json.loads(subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',BASE+':'+MANIFEST],cwd=ROOT))
        assert len(entries)==failed['manifest_files'] and manifest['science_version']=='0.5.0'
        for row in baseline['files']:
            if row['path'] not in FRONTS:assert entries[row['path']]==row,row['path']
        seals=receipt['outputs']
        names=sorted(FRONTS+[path.relative_to(ROOT).as_posix() for path in (ROOT/STAGE).rglob('*') if path.is_file()])
        rows=[]
        for name in names:
            path=ROOT/name
            if path.suffix.lower() in SEALED:
                sealed=seals[name]
                assert path.stat().st_size==sealed['bytes'],name
                row=dict(path=name,**sealed)
            else:
                raw=path.read_bytes();row=dict(path=name,bytes=len(raw),sha256=pin(raw))
                if name in seals:assert {key:row[key] for key in ('bytes','sha256')}==seals[name],name
            entries[name]=row;rows.append(row)
        manifest.update(created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage='l_ctippilot1_publication_format_correction_closed_001',files=sorted(entries.values(),key=lambda row:row['path']))
        (ROOT/MANIFEST).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        raw=(ROOT/MANIFEST).read_bytes();rows.append(dict(path=MANIFEST,bytes=len(raw),sha256=pin(raw)))
        record.update(delta_files=rows,manifest_files=len(entries),manifest_total_bytes=sum(row['bytes'] for row in entries.values()),
            inherited_baseline_entries=len(baseline['files']),output_identity_seal=receipt['output_identity_seal'],
            new_default_HF_files=[],identity_policy='Original closed-helper producer seal plus stat for all scientific/media/CSV; ordinary files SHA. Git object/transport I/O is outside this wrapper-read statement.')
        save(record)
        phase='commit_corrected_stage'
        run(ROOT,'add','-f','--',*[row['path'] for row in rows])
        assert set(git(ROOT,'diff','--cached','--name-only').splitlines())=={row['path'] for row in rows}
        run(ROOT,'diff','--cached','--check')
        run(ROOT,'commit','-m','Run tip-facing circle short pilot and record publication format correction')
        head=git(ROOT,'rev-parse','HEAD');record.update(status='committed',commit=head);save(record)
        phase='push_main'
        run(ROOT,'push','origin','main')
        assert git(ROOT,'ls-remote','origin','refs/heads/main').split()[0]==head and not git(ROOT,'status','--porcelain')
        phase='incremental_restore'
        run(RESTORE,'fetch','origin');run(RESTORE,'merge','--ff-only','origin/main')
        assert git(RESTORE,'rev-parse','HEAD')==head
        for row in rows:
            path=RESTORE/row['path'];assert path.stat().st_size==row['bytes'],row['path']
            if path.suffix.lower() not in SEALED:assert pin(path.read_bytes())==row['sha256'],row['path']
        assert not git(ROOT,'status','--porcelain') and not git(RESTORE,'status','--porcelain')
        record.update(status='published_and_incrementally_restored_pass',remote_main=head,restore_head=head,
            source_clean=True,restore_clean=True,completed_utc=datetime.now(timezone.utc).isoformat())
        save(record)
        print(json.dumps({key:record[key] for key in ('status','commit','remote_main','restore_head','manifest_files')}),flush=True)
    except BaseException as error:
        record.update(status='ordinary_publication_continuation_stopped',failure_phase=phase,
            error=dict(exception_class=type(error).__name__,reason=str(error)),no_automatic_retry_or_rollback=True)
        save(record)
        raise


if __name__=='__main__':main()
