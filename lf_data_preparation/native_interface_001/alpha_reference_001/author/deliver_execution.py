"""Incremental closed M-AREF1 publication; raw output hashes, never science."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = 'e687bdf1ca60edbd0fd044f4f8c990b3b9ccc182'
REL = 'lf_data_preparation/native_interface_001/alpha_reference_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
read = lambda path: json.loads(path.read_bytes())
digest = lambda raw: sha256(raw).hexdigest()
git = lambda root,*args: subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}


def sha(path):
    value = sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024*1024),b''):
            value.update(block)
    return value.hexdigest()


def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as output:
        output.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def identity(root,name):
    path = (root/name).resolve()
    path.relative_to(root)
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path))


def partial_json(path):
    if not path.exists():
        return dict(record_missing=True)
    try:
        value = read(path)
        return value if isinstance(value,dict) else dict(record_read_error='Expected JSON object; raw record retained')
    except (OSError,ValueError) as error:
        return dict(record_read_error=type(error).__name__+': '+str(error))


def check_execution(root,config,entries,previous):
    stage = root/REL
    protocol,outer = read(stage/'protocol.json'),read(stage/'reference_launch.json')
    status = config['execution_status']
    assert config['source_commit'] == BASE and config['executed_card'] == 'M-AREF1'
    assert config['authorized'] is config['executed'] is config['execution_closed'] is True
    assert status in ('pass','not_pass') and outer['status'] == status and outer['completed_utc']
    assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert sha(stage/'protocol.json') == config['protocol_sha256'] == outer['protocol_sha256']
    assert len(protocol['bindings']) == 48
    # Ten old input NPZs are inherited and were checked by the scientific runner.
    npz_inputs = {name for name in protocol['bindings'] if name.lower().endswith('.npz')}
    assert len(npz_inputs) == 10
    for name,pin in protocol['bindings'].items():
        assert previous[name]['sha256'] == entries[name]['sha256'] == pin
        if name not in npz_inputs:
            assert sha(root/name) == pin
    reference = root/protocol['reference_output']
    helper,summary = (partial_json(reference/name) for name in ('lifecycle.json','summary.json'))
    if status == 'pass':
        assert outer['invocations'] == 1 and outer['exit_code'] == 0 and outer['stop_reason'] is None
        assert outer['all_bindings_unchanged'] is True and outer['helper_status'] == 'pass'
        assert not (stage/'stop_requested.txt').exists()
        assert helper.get('status') == summary.get('status') == 'pass'
        assert outer['elapsed_seconds'] <= protocol['phases']['reference']['outer_seconds'] == 960
        assert outer['child_terminal_wall_seconds'] <= protocol['phases']['reference']['helper_seconds'] == 900
        assert helper['elapsed_seconds'] <= 900 and helper['sampled_peak_RSS_bytes'] <= protocol['sampled_RSS_bytes']
        assert outer['peak_sampled_tree_RSS_bytes'] <= protocol['sampled_RSS_bytes'] == 8*1024**3
        assert helper['HP_calls_started'] == helper['HP_calls_completed'] == summary['HP_calls_started'] == summary['HP_calls_completed'] == 4
        assert helper['accepted_mechanical_states_completed'] == helper['workpiece_states_completed'] == summary['accepted_states'] == 2
        assert summary['audited_targets_mm'] == protocol['targets_mm'] == [1.2,1.15]
        assert [row['index'] for row in summary['states']] == [0,1]
        assert [row['reference_execution_index'] for row in summary['states']] == [13,14]
        assert [row['original_target_index'] for row in summary['states']] == [13,14]
        assert all(row['status'] == 'pass' and row['HP_calls'] == 2 for row in summary['states'])
        child_file = root/protocol['production_stage']/protocol['production_result_dir']/'result.json'
        child = read(child_file)
        assert summary['result_sha256'] == entries[child_file.relative_to(root).as_posix()]['sha256']
        assert summary['gates'] == protocol['gates'] and summary['continuation'] == child['continuation']
        assert [(row['state_sha256'],row['target_mm']) for row in summary['states']] == [(row['state_sha256'],row['d']) for row in child['states']]
        assert summary['full_original_path_reference_pass'] is summary['full_original_path_completed'] is False
        assert all(summary[key] is False for key in ('contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified'))
    else:
        assert (outer.get('stop_reason') is not None or outer.get('failure') is not None or outer.get('exit_code') != 0
            or outer.get('helper_status') != 'pass' or outer.get('all_bindings_unchanged') is not True or summary.get('status') != 'pass')
        # Missing/running/corrupt helper files remain honest failed snapshots.
        assert outer.get('invocations') in (0,1)
    auth,reply = (read(stage/'author'/name) for name in ('authorization.json','direct_human_reply.json'))
    proof_file = root/config['previous_publication_receipt']['path']
    proof = read(proof_file)
    assert sha(proof_file) == config['previous_publication_receipt']['sha256']
    assert auth['authorized'] is True and auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['card'] == reply['card'] == proof['prepared_card'] == 'M-AREF1'
    assert auth['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit'] == BASE
    assert auth['protocol_sha256'] == proof['protocol_sha256'] == config['protocol_sha256']
    assert auth['human_evidence_sha256'] == sha(stage/'author/direct_human_reply.json')
    assert auth['source_publication_receipt_sha256'] == sha(proof_file)
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip() and reply['reply_context']
    assert {row['path'] for row in config['front_history']} == FRONTS
    for row in config['front_history']:
        prior,current = git(root,'show',BASE+':'+row['path']),(root/row['path']).read_bytes()
        assert digest(prior) == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert entries[row['path']]['sha256'] == row['new_sha256']
    closed = config['closed_output_SHA256']
    run_files = {path.relative_to(root).as_posix() for path in (stage/'run_001').rglob('*') if path.is_file()}
    assert run_files == {name for name in closed if name.startswith(REL+'/run_001/')}
    for name,pin in closed.items():
        assert entries[name]['sha256'] == pin
    actual_stage = {path.relative_to(root).as_posix() for path in stage.rglob('*') if path.is_file()}
    assert actual_stage == {name for name in entries if name.startswith(REL+'/')}
    assert config['terminal_review_paths']
    for name in config['terminal_review_paths']:
        review = read(root/name)
        assert review['status'].startswith('pass') and review['execution_status'] == status
    final = config.get('final_review_path')
    if final:
        review = read(root/final)
        assert review['status'].startswith('pass') and review['execution_status'] == status
        assert review['config_sha256'] == sha(stage/'author/execution_delivery_config.json')
        assert set(config['allowed_delta_paths'])-{final} <= review['reviewed_repository_SHA256'].keys()
        for name,pin in review['reviewed_repository_SHA256'].items():
            assert entries[name]['sha256'] == pin
    return protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('finalize','verify'))
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--restore',type=Path,default=Path('D:/hf-restore-20260930'))
    parser.add_argument('--external-base',type=Path,default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root,restore,external = args.repo.resolve(),args.restore.resolve(),args.external_base.resolve()
    config = read(root/REL/'author/execution_delivery_config.json')
    proof_file = root/config['previous_publication_receipt']['path']
    proof = read(proof_file)
    oldraw = git(root,'show',BASE+':'+MANIFEST)
    old = json.loads(oldraw)
    previous = {row['path']:row for row in old['files']}
    assert sha(proof_file) == config['previous_publication_receipt']['sha256']
    assert proof['published_commit'] == BASE and proof['status'] == 'published_and_incrementally_restored_pass'
    assert proof['prepared_card'] == 'M-AREF1' and proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    assert digest(oldraw) == proof['manifest_sha256'] and len(previous) == proof['ordinary_manifest_files']
    assert sum(row['bytes'] for row in previous.values()) == proof['ordinary_manifest_bytes']
    allowed = set(config['allowed_delta_paths'])
    assert len(allowed) == len(config['allowed_delta_paths']) and FRONTS <= allowed
    assert all(name in FRONTS or name.startswith(REL+'/') for name in allowed)
    assert sha(root/REL/'author/deliver_execution.py') == sha(external/'deliver_execution.py')
    delta_file = external/'execution_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root,restore):
        assert git(tree,'branch','--show-current').decode().strip() == 'main'
        assert git(tree,'remote','get-url','origin').decode().strip() == ORIGIN
        assert git(tree,'remote','get-url','--push','origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root,'rev-parse','HEAD').decode().strip() == BASE and not delta_file.exists()
        assert (root/MANIFEST).read_bytes() == oldraw
        assert not git(root,'diff','--name-only') and not git(root,'ls-files','--others','--exclude-standard','-z')
        paths = names(git(root,'ls-files','-z'))-{MANIFEST}
        new = paths-previous.keys()
        assert not previous.keys()-paths
        assert names(git(root,'diff','--cached','--name-only','-z',BASE)) == allowed == new|FRONTS
        delta = [identity(root,name) for name in sorted(allowed)]
        entries = dict(previous,**{row['path']:row for row in delta})
        check_execution(root,config,entries,previous)
        manifest = dict(old,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage='saved_alpha_reference_closed_001',files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(raw)
        value = dict(status='incremental_closed_execution_delivery_pass',previous_delivery_commit=BASE,
            manifest_sha256=digest(raw),ordinary_manifest_files=len(entries),ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta,delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(previous)-2,
            protocol_sha256=config['protocol_sha256'],executed_card='M-AREF1',execution_status=config['execution_status'],
            authorized=True,executed=True,execution_closed=True,inherited_input_NPZ_bindings_not_raw_reread=10,
            new_full_source_scan=False,new_NPZ_decodes_or_HF_or_HP_or_tests_or_plots=0)
        write_new(delta_file,value)
    else:
        source = read(delta_file)
        commit = git(root,'rev-parse','HEAD').decode().strip()
        assert git(root,'rev-parse','HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root,'ls-remote','--heads','origin','main').decode().split() == [commit,'refs/heads/main']
        for tree in (root,restore):
            assert git(tree,'rev-parse','HEAD').decode().strip() == commit and not git(tree,'status','--porcelain')
        assert (root/MANIFEST).read_bytes() == (restore/MANIFEST).read_bytes() and sha(restore/MANIFEST) == source['manifest_sha256']
        manifest = read(restore/MANIFEST)
        entries = {row['path']:row for row in manifest['files']}
        assert len(entries) == source['ordinary_manifest_files'] and sum(row['bytes'] for row in entries.values()) == source['ordinary_manifest_bytes']
        assert names(git(root,'diff','--name-only','-z',BASE,commit)) == allowed|{MANIFEST}
        assert {row['path'] for row in source['delta_files']} == allowed and source['execution_status'] == config['execution_status']
        for tree in (root,restore):
            assert names(git(tree,'ls-files','-z')) == entries.keys()|{MANIFEST}
            assert all(identity(tree,row['path']) == row == entries[row['path']] for row in source['delta_files'])
            check_execution(tree,config,entries,previous)
        assert all(entries[name] == previous[name] for name in previous.keys()-allowed)
        assert manifest['science_version'] == old['science_version'] == '0.5.0'
        assert manifest['science_baseline_commit'] == old['science_baseline_commit']
        value = dict(status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit,previous_delivery_commit=BASE,branch='main',origin=ORIGIN,
            source_and_restore_clean=True,remote_main_confirmed_equal=True,restore_root=str(restore),
            manifest_sha256=source['manifest_sha256'],ordinary_manifest_files=len(entries),ordinary_manifest_bytes=source['ordinary_manifest_bytes'],
            delta_files_restored_and_hashed=len(allowed),delta_bytes=source['delta_bytes'],
            unchanged_manifest_entries_inherited=source['unchanged_manifest_entries_inherited'],protocol_sha256=config['protocol_sha256'],
            executed_card='M-AREF1',authorized=True,executed=True,execution_status=config['execution_status'],execution_closed=True,
            inherited_input_NPZ_bindings_not_raw_reread=10,new_full_source_or_restore_scan=False,
            new_NPZ_decodes_or_HF_or_HP_or_tests_or_plots=0,whole_HF5_complete=False)
        write_new(external/'execution_publication_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key!='delta_files'},ensure_ascii=False))


if __name__ == '__main__':
    main()
