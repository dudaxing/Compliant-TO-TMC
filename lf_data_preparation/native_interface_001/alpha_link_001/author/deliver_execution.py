"""Publish the closed M-ALINK1 ordinary delta; inherit old science/media identities."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = '1e639641625b4d0f92eb84aff4b4c6fdb05d0171'
REL = 'lf_data_preparation/native_interface_001/alpha_link_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
SCIENCE_BASE = 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
SUFFIXES = {'.json', '.py', '.md', '.log'}
read = lambda path: json.loads(path.read_bytes())
git = lambda root, *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}


def sha(path):
    assert path.suffix.lower() in SUFFIXES, 'Only ordinary execution metadata may be byte-read: '+str(path)
    return sha256(path.read_bytes()).hexdigest()


def identity(root, name):
    path = (root/name).resolve()
    path.relative_to(root)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def check_execution(root, entries, old, config):
    stage = root/REL
    protocol_file, proof_file = stage/'protocol.json', stage/'author/source_publication_receipt.json'
    protocol, proof = read(protocol_file), read(proof_file)
    auth_file, reply_file = stage/'author/authorization.json', stage/'author/direct_human_reply.json'
    auth, reply = read(auth_file), read(reply_file)
    assert protocol['card'] == auth['card'] == reply['card'] == proof['prepared_card'] == 'M-ALINK1'
    assert protocol['prepared'] is proof['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is proof['authorized'] is proof['executed'] is False
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert config['source_commit'] == auth['approved_source_commit'] == reply['approved_source_commit'] == BASE
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip()
    assert reply['reply_context'] == 'Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction'
    assert auth['human_evidence_sha256'] == sha(reply_file) and auth['source_publication_receipt_sha256'] == sha(proof_file)
    assert config['protocol_sha256'] == proof['protocol_sha256'] == auth['protocol_sha256'] == sha(protocol_file)
    assert auth['helper_seconds'] == protocol['phases']['link']['helper_seconds'] == 180
    assert auth['outer_seconds'] == protocol['phases']['link']['outer_seconds'] == 240
    assert auth['sampled_RSS_bytes'] == protocol['sampled_RSS_bytes'] == 8*1024**3
    assert auth['invocations_authorized'] == 1 and auth['retries'] == 0 and auth['force'] is False
    assert protocol['expected_accepted_states'] == 2 and protocol['targets_mm'] == [1.2,1.15]
    assert protocol['original_target_indices'] == [13,14] and len(protocol['bindings']) == 30
    # The approved sole run checked these raw bytes. Publication inherits their
    # manifest identities instead of rereading old arrays, media or sources.
    assert all(entries[name] == old[name] and entries[name]['sha256'] == pin for name,pin in protocol['bindings'].items())
    launch, helper = read(stage/'link_launch.json'), read(stage/'run_001/execution_receipt.json')
    assert launch['status'] == helper['status'] == launch['helper_status'] == 'pass'
    assert launch['card'] == 'M-ALINK1' and launch['invocations'] == 1 and launch['exit_code'] == 0
    assert launch['approved_source_commit'] == BASE and launch['completed_utc'] and launch['stop_reason'] is None
    assert launch['all_bindings_unchanged'] is helper['all_bindings_unchanged'] is True
    assert launch['protocol_sha256'] == helper['protocol_sha256'] == config['protocol_sha256']
    assert 0 <= launch['elapsed_seconds'] <= launch['outer_seconds'] == 240
    assert 0 <= launch['child_terminal_wall_seconds'] <= 180
    assert 0 <= helper['elapsed_seconds'] <= helper['helper_seconds'] == 180
    assert launch['peak_sampled_tree_RSS_bytes'] <= launch['sampled_RSS_limit_bytes'] == protocol['sampled_RSS_bytes']
    assert helper['sampled_peak_RSS_bytes'] <= helper['sampled_RSS_limit_bytes'] == protocol['sampled_RSS_bytes']
    assert helper['calls'] == protocol['expected_calls'] == dict(saved_summary_started=1,saved_summary_completed=1,response_writes=1,index_writes=1)
    assert helper['mechanical_hooks_monitored'] is False
    assert all(helper[key] == 0 for key in ('new_NPZ_decodes','new_gzip_reads','new_force_calls','new_tangent_calls','new_HP_calls','new_solver_calls','new_model_constructions','new_plots'))
    run_names = {path.relative_to(root).as_posix() for path in (stage/'run_001').rglob('*') if path.is_file()}
    assert run_names == {REL+'/run_001/'+name for name in ('linked_response.json','light_index.json','execution_receipt.json')}
    assert run_names <= config['closed_output_SHA256'].keys()
    assert all(entries[name]['sha256'] == pin for name,pin in config['closed_output_SHA256'].items())
    assert set(helper['outputs']) == {'linked_response.json','light_index.json'}
    assert all(entries[REL+'/run_001/'+name]['sha256'] == pin for name,pin in helper['outputs'].items())
    linked, index = read(stage/'run_001/linked_response.json'), read(stage/'run_001/light_index.json')
    path, reference, continuation = linked['path'], linked['independent_reference'], linked['continuation']
    assert linked['status'] == 'success' and path['completed'] is True and path['accepted_states'] == 2
    assert path['requested_targets_mm'] == [1.2,1.15] and path['task_target_executed'] is path['full_original_path_completed'] is False
    assert linked['target_response'] is None and continuation['parent_status'] == 'failed'
    assert continuation['parent_failure']['code'] == 'time_limit' and continuation['parent_path_completed'] is False
    assert continuation['full_original_path_executed_by_child'] is False and continuation['original_target_indices'] == [13,14]
    assert reference['status'] == 'matched' and reference['accepted_reference_pass'] is reference['full_path_reference_pass'] is True
    assert reference['reference_scope'] == 'Child accepted suffix only' and reference['full_original_path_reference_pass'] is False
    assert reference['HP_calls_completed'] == 4 and linked['views']['status'] == 'matched' and len(linked['views']['links']) == 4
    assert all(value is False for value in linked['producer_flags'].values())
    assert all(reference[key] is False for key in ('HP_all_columns_qualified','contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified'))
    assert index['status'] == 'pass' and index['continuation'] == continuation and index['source_flags'] == linked['producer_flags']
    assert index['linked_response']['sha256'] == entries[REL+'/run_001/linked_response.json']['sha256']
    assert {row['path'] for row in config['front_history']} == FRONTS
    for row in config['front_history']:
        prior = git(root,'show',BASE+':'+row['path'])
        current = (root/row['path']).read_bytes()
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert entries[row['path']]['sha256'] == row['new_sha256']
    for name,pin in config.get('review_pins',{}).items():
        assert entries[name]['sha256'] == pin == sha(root/name)
    final_name = config.get('final_review_path')
    if final_name:
        review = read(root/final_name)
        assert review['status'].startswith('pass') and review['config_sha256'] == sha(stage/'author/execution_delivery_config.json')
        covered = set(config['allowed_delta_paths'])-{final_name}
        assert covered <= review['reviewed_repository_SHA256'].keys() and final_name not in review['reviewed_repository_SHA256']
        assert all(entries[name]['sha256'] == pin for name,pin in review['reviewed_repository_SHA256'].items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('finalize','verify'))
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--restore',type=Path,default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), Path(__file__).resolve().parent
    config = read(root/REL/'author/execution_delivery_config.json')
    assert config['source_commit'] == BASE
    allowed = set(config['allowed_delta_paths'])
    assert FRONTS <= allowed and all(name in FRONTS or name.startswith(REL+'/') for name in allowed)
    assert all(Path(name).suffix.lower() in SUFFIXES for name in allowed)
    oldraw = git(root,'show',BASE+':'+MANIFEST)
    old_manifest = json.loads(oldraw)
    old = {row['path']:row for row in old_manifest['files']}
    proof = read(root/REL/'author/source_publication_receipt.json')
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['prepared_card'] == 'M-ALINK1' and proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    assert proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert len(old) == proof['ordinary_manifest_files'] and sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes']
    assert old_manifest['science_version'] == '0.5.0' and old_manifest['science_baseline_commit'] == SCIENCE_BASE
    assert len({name for name in old if name.startswith(REL+'/')}) == 21
    assert allowed & old.keys() == FRONTS
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
        assert not old.keys()-paths
        assert names(git(root,'diff','--cached','--name-only','-z',BASE)) == allowed == (paths-old.keys())|FRONTS
        delta = [identity(root,name) for name in sorted(allowed)]
        entries = dict(old,**{row['path']:row for row in delta})
        assert set(entries) == paths
        check_execution(root,entries,old,config)
        manifest = dict(old_manifest,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage='saved_alpha_linked_response_closed_001',files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(raw)
        value = dict(status='incremental_execution_delivery_pass',previous_delivery_commit=BASE,
            manifest_sha256=sha256(raw).hexdigest(),ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),delta_files=delta,
            delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=sha(root/REL/'protocol.json'),executed_card='M-ALINK1',authorized=True,executed=True,
            execution_status='pass',execution_closed=True,bindings_inherited_from_closed_sole_run=30,
            old_science_media_byte_reads=0,new_full_source_scan=False,new_HF_API_NPZ_HP_tests_plots=0)
        write_new(delta_file,value)
    else:
        source = read(delta_file)
        commit = git(root,'rev-parse','HEAD').decode().strip()
        assert git(root,'rev-parse','HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root,'ls-remote','--heads','origin','main').decode().split() == [commit,'refs/heads/main']
        for tree in (root,restore):
            assert git(tree,'rev-parse','HEAD').decode().strip() == commit and not git(tree,'status','--porcelain')
        assert (root/MANIFEST).read_bytes() == (restore/MANIFEST).read_bytes() and sha(restore/MANIFEST) == source['manifest_sha256']
        current_manifest = read(restore/MANIFEST)
        entries = {row['path']:row for row in current_manifest['files']}
        assert {row['path'] for row in source['delta_files']} == allowed
        assert names(git(root,'diff','--name-only','-z',BASE,commit)) == allowed|{MANIFEST}
        for tree in (root,restore):
            assert names(git(tree,'ls-files','-z')) == entries.keys()|{MANIFEST}
            assert all(identity(tree,row['path']) == row == entries[row['path']] for row in source['delta_files'])
            check_execution(tree,entries,old,config)
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        assert current_manifest['science_version'] == '0.5.0' and current_manifest['science_baseline_commit'] == SCIENCE_BASE
        value = dict(status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit,previous_delivery_commit=BASE,branch='main',origin=ORIGIN,
            source_and_restore_clean=True,remote_main_confirmed_equal=True,restore_root=str(restore),
            manifest_sha256=source['manifest_sha256'],ordinary_manifest_files=len(entries),ordinary_manifest_bytes=source['ordinary_manifest_bytes'],
            delta_files_restored_and_hashed=len(allowed),delta_bytes=source['delta_bytes'],
            unchanged_manifest_entries_inherited=source['unchanged_manifest_entries_inherited'],protocol_sha256=source['protocol_sha256'],
            executed_card='M-ALINK1',authorized=True,executed=True,execution_status='pass',execution_closed=True,
            bindings_inherited_from_closed_sole_run=30,old_science_media_byte_reads=0,new_full_source_or_restore_scan=False,
            new_HF_API_NPZ_HP_tests_plots=0,whole_HF5_complete=False)
        write_new(external/'execution_publication_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key != 'delta_files'},ensure_ascii=False))


if __name__ == '__main__':
    main()
