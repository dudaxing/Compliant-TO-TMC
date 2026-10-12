"""Publish only reviewed ordinary M-EXTEND1 source preparation; inherit previous evidence."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import argparse
import json
import subprocess

BASE='c4d81620fe7d1a9260cf0f7d27ab35970d463e46'
REL='lf_data_preparation/native_interface_001/saved_extension_001'
MANIFEST='handoff/repository_manifest.json'
FRONTS={'docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'}
ORIGIN='https://github.com/dudaxing/Compliant-TO-TMC.git'
read=lambda path:json.loads(path.read_bytes())
git=lambda root,*args:subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=root)
names=lambda raw:{part.decode('utf-8') for part in raw.split(b'\0') if part}
sha=lambda path:sha256(path.read_bytes()).hexdigest()


def identity(root,name):
    path=(root/name).resolve();path.relative_to(root)
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path))


def new_json(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as output:
        output.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def check_preparation(root,entries,old):
    stage=root/REL;protocol=read(stage/'protocol.json')
    assert protocol['card']=='M-EXTEND1' and protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert protocol['phases']['production']['helper_seconds']==3000 and protocol['phases']['production']['outer_seconds']==3060
    assert (protocol['focused_tests_seconds'],protocol['view_seconds'],protocol['settings']['time_limit_seconds'])==(180,600,1800.)
    assert protocol['targets_mm']==[1.15,1.1] and protocol['original_target_indices']==[14,15]
    assert len(protocol['source_package']['files'])==90 and len(protocol['focused_test_selectors'])==36 and len(protocol['installation'])==6
    assert not (stage/'run_001').exists() and not (stage/'production_launch.json').exists()
    assert not any((stage/'author'/name).exists() for name in ('authorization.json','direct_human_reply.json','M_EXTEND1_source_publication_receipt.json'))
    inherited=protocol['inherited_byte_input_identities'];assert len(inherited)==7
    assert sum(Path(name).suffix.lower() in ('.png','.gif') for name in inherited)==5
    assert sum(Path(name).suffix.lower()=='.npz' for name in inherited)==2
    for name,pin in protocol['bindings'].items():
        assert entries[name]['sha256']==pin
        if name in inherited:
            assert old[name]==entries[name]==inherited[name] and (root/name).stat().st_size==old[name]['bytes']
        else:assert sha(root/name)==pin
    for row in protocol['installation']:
        assert row['target'] not in protocol['bindings']
        assert entries[row['target']]==old[row['target']] and sha(root/row['target'])==row['old_sha256']
        assert sha(root/row['candidate_source'])==row['new_sha256']
    receipt=read(stage/'author/preparation_receipt.json')
    assert receipt['status']=='prepared_static_review_only' and receipt['authorized'] is receipt['executed'] is receipt['installed'] is False
    assert all(entries[name]['sha256']==pin==sha(root/name) for name,pin in receipt['artifact_SHA256'].items())
    for row in receipt['front_history']:
        previous=git(root,'show',BASE+':'+row['path']);current=(root/row['path']).read_bytes()
        assert sha256(previous).hexdigest()==row['old_sha256'] and current.count(previous)==1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']]==previous
        assert entries[row['path']]['sha256']==row['new_sha256']
    assert {row['path'] for row in receipt['front_history']}==FRONTS
    for name in ('wrapper_static_review.json','final_protocol_scope_review.json'):
        review=read(stage/'author'/name)
        assert review['authorized'] is review['executed'] is False and review['blocking_findings']==[]
        assert review['protocol_SHA256']==sha(stage/'protocol.json')
        assert all(sha(stage/path)==pin for path,pin in review['current_source_SHA256'].items())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('finalize','verify'));parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--restore',type=Path,default=Path('D:/hf-restore-20260930'))
    args=parser.parse_args();root,restore,external=args.repo.resolve(),args.restore.resolve(),Path(__file__).resolve().parent
    oldraw=git(root,'show',BASE+':'+MANIFEST);previous=json.loads(oldraw);old={row['path']:row for row in previous['files']}
    prior=read(root/REL/'author/previous_publication_receipt.json')
    assert prior['status']=='published_and_incrementally_restored_pass' and prior['published_commit']==BASE
    assert prior['executed_card']=='M-ALINK1' and prior['execution_status']=='pass' and prior['execution_closed'] is True
    assert prior['manifest_sha256']==sha256(oldraw).hexdigest() and len(old)==prior['ordinary_manifest_files']
    assert sum(row['bytes'] for row in old.values())==prior['ordinary_manifest_bytes']
    delta_file=external/'preparation_delivery_delta_verify.json'
    for tree in (root,) if args.mode=='finalize' else (root,restore):
        assert git(tree,'branch','--show-current').decode().strip()=='main'
        assert git(tree,'remote','get-url','origin').decode().strip()==git(tree,'remote','get-url','--push','origin').decode().strip()==ORIGIN
    if args.mode=='finalize':
        assert git(root,'rev-parse','HEAD').decode().strip()==BASE and not delta_file.exists()
        assert (root/MANIFEST).read_bytes()==oldraw and not git(root,'diff','--name-only')
        assert not git(root,'ls-files','--others','--exclude-standard','-z')
        stage={path.relative_to(root).as_posix() for path in (root/REL).rglob('*') if path.is_file()}
        allowed=stage|FRONTS;assert all(Path(name).suffix.lower() in ('.json','.py','.md') for name in allowed)
        assert not stage&old.keys()
        paths=names(git(root,'ls-files','-z'))-{MANIFEST}
        assert not old.keys()-paths
        assert names(git(root,'diff','--cached','--name-only','-z',BASE))==allowed==(paths-old.keys())|FRONTS
        delta=[identity(root,name) for name in sorted(allowed)];entries=dict(old,**{row['path']:row for row in delta})
        check_preparation(root,entries,old)
        manifest=dict(previous,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage='saved_explicit_path_extension_prepared_001',files=[entries[name] for name in sorted(paths)])
        raw=(json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8');(root/MANIFEST).write_bytes(raw)
        value=dict(status='incremental_preparation_delivery_pass',previous_delivery_commit=BASE,manifest_sha256=sha256(raw).hexdigest(),
            ordinary_manifest_files=len(entries),ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta,delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=sha(root/REL/'protocol.json'),prepared_card='M-EXTEND1',prepared=True,authorized=False,executed=False,
            inherited_stat_only_media=5,inherited_stat_only_NPZ=2,default_changes=0,new_full_source_scan=False,
            HF_collect_tests_science_arrays_media_byte_reads_plots=0)
        new_json(delta_file,value)
    else:
        source=read(delta_file);commit=git(root,'rev-parse','HEAD').decode().strip()
        assert git(root,'rev-parse','HEAD^').decode().strip()==BASE and commit!=BASE
        assert git(root,'ls-remote','--heads','origin','main').decode().split()==[commit,'refs/heads/main']
        for tree in (root,restore):assert git(tree,'rev-parse','HEAD').decode().strip()==commit and not git(tree,'status','--porcelain')
        assert (root/MANIFEST).read_bytes()==(restore/MANIFEST).read_bytes() and sha(restore/MANIFEST)==source['manifest_sha256']
        entries={row['path']:row for row in read(restore/MANIFEST)['files']};allowed={row['path'] for row in source['delta_files']}
        assert names(git(root,'diff','--name-only','-z',BASE,commit))==allowed|{MANIFEST}
        for tree in (root,restore):
            assert names(git(tree,'ls-files','-z'))==entries.keys()|{MANIFEST}
            assert all(identity(tree,row['path'])==row==entries[row['path']] for row in source['delta_files'])
            check_preparation(tree,entries,old)
        assert all(entries[name]==old[name] for name in old.keys()-allowed)
        current=read(restore/MANIFEST)
        assert current['science_version']==previous['science_version']=='0.5.0' and current['science_baseline_commit']==previous['science_baseline_commit']
        value=dict(status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),published_commit=commit,
            previous_delivery_commit=BASE,branch='main',origin=ORIGIN,source_and_restore_clean=True,remote_main_confirmed_equal=True,restore_root=str(restore),
            manifest_sha256=source['manifest_sha256'],ordinary_manifest_files=len(entries),ordinary_manifest_bytes=source['ordinary_manifest_bytes'],
            delta_files_restored_and_hashed=len(allowed),delta_bytes=source['delta_bytes'],unchanged_manifest_entries_inherited=source['unchanged_manifest_entries_inherited'],
            protocol_sha256=source['protocol_sha256'],prepared_card='M-EXTEND1',prepared=True,authorized=False,executed=False,
            inherited_stat_only_media=5,inherited_stat_only_NPZ=2,default_changes=0,new_full_source_or_restore_scan=False,
            HF_collect_tests_science_arrays_media_byte_reads_plots=0,whole_HF5_complete=False)
        new_json(external/'source_publication_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key!='delta_files'},ensure_ascii=False))


if __name__=='__main__':main()
