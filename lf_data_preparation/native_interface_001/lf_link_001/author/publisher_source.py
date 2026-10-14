"""Publish L-LINK1 ordinary source preparation; inherit existing media identities."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

BASE = '909f8acee95279e449e09961fd4fe68fed9d688f'
REL = 'lf_data_preparation/native_interface_001/lf_link_001'
PRODUCTION = 'lf_data_preparation/native_interface_001/lf_forward_001/run_001'
REFERENCE = 'lf_data_preparation/native_interface_001/lf_reference_001/run_001/reference'
DEFAULT = 'hf_repo/src/hf_eval/native_response.py'
DEFAULT_PIN = '53bee087509f780ec5a62dae5b39a067e5f0df38f6fd7cc47311766ab3e2f14b'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
RUNTIME = {'execute_lf_link.py', 'launch_link.py', 'test_partial_native_reference.py', 'candidate.native_response.py'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
OLD_MANIFEST_SHA = 'aaa13ff53e966d3b18296a0199a4e5fc889bfd238af48f551b85964a8cf1f6b3'
ORDINARY = {'.json', '.py', '.md', '.toml'}


def path_in(root, name):
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = (root/relative).resolve()
    path.relative_to(root)
    return path


def raw(path):
    assert path.suffix.lower() in ORDINARY, 'Ordinary files only; science/media bytes remain inherited'
    return path.read_bytes()


def sha(path):
    return sha256(raw(path)).hexdigest()


def read(path):
    assert path.suffix.lower() == '.json'
    return json.loads(raw(path))


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)


def names(value):
    return {part.decode('utf-8') for part in value.split(b'\0') if part}


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def old_manifest(root, proof):
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']:row for row in previous['files']}
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['executed_card'] == 'L-REF1' and proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    assert proof['authorized'] is proof['executed'] is True
    assert proof['manifest_sha256'] == sha256(oldraw).hexdigest() == OLD_MANIFEST_SHA
    assert len(old) == len(previous['files']) == proof['ordinary_manifest_files'] == 20536
    assert sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes'] == 11309928280
    assert previous['science_version'] == '0.5.0'
    assert previous['science_baseline_commit'] == 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
    return oldraw, previous, old


def check_protocol(root, protocol, old):
    """Inspect ordinary bindings; five media identities use closed producer seals and stat."""
    assert protocol['schema_version'] == 'lf-selected-reference-linked-delivery-card-1.0' and protocol['card'] == 'L-LINK1'
    assert protocol['source_baseline_commit'] == BASE and protocol['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is protocol['installed'] is False
    assert protocol.get('protocol_seed_only',False) is False
    phase = protocol['phases']['link']
    assert (phase['helper_seconds'],phase['outer_seconds'],phase['tests_seconds'],protocol['sampled_RSS_bytes']) == (180,240,60,8*1024**3)
    assert phase['argv'] == [REL+'/execute_lf_link.py','--repo','.', '--protocol',REL+'/protocol.json','--time-limit','180']
    assert protocol['source_before_installation'] == {'path':DEFAULT,'sha256':DEFAULT_PIN}
    assert sha(root/DEFAULT) == old[DEFAULT]['sha256'] == DEFAULT_PIN
    assert protocol['candidate_source'] == REL+'/candidate.native_response.py'
    assert protocol['result_file'] == PRODUCTION+'/lf_fine_forward/result.json'
    assert protocol['reference_file'] == REFERENCE+'/summary.json'
    assert protocol['selected_accepted_indices'] == protocol['original_target_indices'] == [13,16]
    assert protocol['targets_mm'] == [1.2,1.05]
    assert (protocol['production_accepted_states'],protocol['expected_reference_states']) == (25,2)
    assert protocol['expected_new_mechanics_calls'] == 0 and protocol['planned_default_metadata_file_changes'] == 1
    assert all(protocol[key] is False for key in ('full_production_path_reference_pass','full_original_path_reference_pass',
        'HF5_qualified','HP_matrix_columns_exhaustively_checked','contact_qualified','clamp_qualified','pressure_qualified'))
    inherited = protocol['inherited_media_bindings']
    assert len(inherited) == 5 and set(protocol['media_files']) == inherited.keys()
    assert {name for name in protocol['bindings'] if Path(name).suffix.lower() not in ORDINARY} == inherited.keys()
    sealed_outputs = {}
    receipt_names = {'production_receipt_file':PRODUCTION+'/execution_receipt.json',
        'reference_execution_receipt_file':REFERENCE+'/execution_receipt.json'}
    for key,name in receipt_names.items():
        assert protocol[key] == name
        assert sha(path_in(root,name)) == old[name]['sha256']
        producer = read(path_in(root,name))
        assert producer['status'] == 'pass' and producer['output_identity_seal'] == 'complete_inside_original_helper_window'
        sealed_outputs.update(producer['outputs'])
    for name,pin in protocol['bindings'].items():
        path = path_in(root,name)
        if name in inherited:
            entry = inherited[name]
            sealed = sealed_outputs[name]
            assert entry['sha256'] == sealed['sha256'] == old[name]['sha256'] == pin
            assert path.is_file() and path.stat().st_size == entry['bytes'] == sealed['bytes'] == old[name]['bytes']
        else:
            assert sha(path) == pin
            if name in old: assert old[name]['sha256'] == pin
    result = read(root/protocol['result_file'])
    reference = read(root/protocol['reference_file'])
    assert result['status'] == 'success' and result['accepted_states'] == len(result['states']) == 25
    assert result['path_completed'] is result['task_target_executed'] is True
    assert reference['status'] == 'pass' and reference['accepted_states'] == len(reference['states']) == 2
    assert [row['index'] for row in reference['states']] == [13,16]
    selected = [result['states'][i] for i in (13,16)]
    assert [row['state_sha256'] for row in selected] == [row['state_sha256'] for row in reference['states']]
    assert [row['d'] for row in selected] == [row['target_mm'] for row in reference['states']] == [1.2,1.05]


def identity(root, name):
    path = path_in(root,name)
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path))


def check_preparation(root, entries, old):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    check_protocol(root,protocol,old)
    assert not any((stage/name).exists() for name in ('run_001','link_launch.json','link_stdout.log','stop_requested.txt'))
    assert not any((stage/'author'/name).exists() for name in ('authorization.json','direct_human_reply.json','source_publication_receipt.json'))
    receipt = read(stage/'author/source_preparation_receipt.json')
    assert receipt['card'] == 'L-LINK1' and receipt['source_baseline_commit'] == BASE
    assert receipt['prepared'] is True and receipt['authorized'] is receipt['executed'] is receipt['installed'] is False
    for name,pin in receipt['artifact_SHA256'].items():
        assert name.startswith(REL+'/') and entries[name]['sha256'] == pin == sha(path_in(root,name))
    assert REL+'/author/final_preparation_review.json' not in receipt['artifact_SHA256']
    assert {row['path'] for row in receipt['front_history']} == FRONTS and len(receipt['front_history']) == 2
    for row in receipt['front_history']:
        prior = git(root,'show',BASE+':'+row['path'])
        current = raw(root/row['path'])
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha256(current).hexdigest() == row['new_sha256'] == entries[row['path']]['sha256']
    review = read(stage/'author/final_preparation_review.json')
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    assert review['authorized'] is review['executed'] is review['installed'] is False
    assert review['protocol_SHA256'] == sha(stage/'protocol.json')
    files = {path.relative_to(stage).as_posix() for path in stage.rglob('*') if path.is_file()}
    assert set(review['current_source_SHA256']) == files-{'author/final_preparation_review.json'}
    assert RUNTIME | {'protocol.json','L-LINK1_CARD.md','PREPARATION_RESULTS.md','author/final_preparation_review.md'} <= files
    assert all(sha(path_in(stage,name)) == pin for name,pin in review['current_source_SHA256'].items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('finalize','verify'))
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--restore',type=Path,default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root,restore,here = args.repo.resolve(),args.restore.resolve(),Path(__file__).resolve().parent
    assert not here.is_relative_to(root), 'Run the external publisher; the formal copy is recovery evidence only'
    proof = read(root/REL/'author/previous_publication_receipt.json')
    oldraw,previous,old = old_manifest(root,proof)
    delta_file = here/'source_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root,restore):
        assert git(tree,'branch','--show-current').decode().strip() == 'main'
        assert git(tree,'remote','get-url','origin').decode().strip() == git(tree,'remote','get-url','--push','origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root,'rev-parse','HEAD').decode().strip() == BASE and not delta_file.exists()
        assert raw(root/MANIFEST) == oldraw and not git(root,'diff','--name-only')
        assert not git(root,'ls-files','--others','--exclude-standard','-z')
        stage = {path.relative_to(root).as_posix() for path in (root/REL).rglob('*') if path.is_file()}
        assert stage and not stage & old.keys()
        allowed = stage | FRONTS
        paths = names(git(root,'ls-files','-z'))-{MANIFEST}
        assert not old.keys()-paths
        assert names(git(root,'diff','--cached','--name-only','-z',BASE)) == allowed == (paths-old.keys()) | FRONTS
        delta = [identity(root,name) for name in sorted(allowed)]
        entries = dict(old, **{row['path']:row for row in delta})
        assert paths == entries.keys()
        check_preparation(root,entries,old)
        manifest = dict(previous,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage='native_lf_selected_reference_link_source_prepared_001',files=[entries[name] for name in sorted(paths)])
        output = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(output)
        value = dict(status='incremental_preparation_delivery_pass',previous_delivery_commit=BASE,
            manifest_sha256=sha256(output).hexdigest(),ordinary_manifest_files=len(entries),ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta,delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=sha(root/REL/'protocol.json'),prepared_card='L-LINK1',prepared=True,authorized=False,executed=False,installed=False,
            planned_metadata_tests_maximum=16,planned_saved_summary_invocations=1,planned_response_writes=1,planned_index_writes=1,
            planned_future_default_installations_after_all_pass=1,planned_HP_calls=0,planned_plots=0,inherited_stat_only_media=5,default_changes=0,
            new_full_source_scan=False,scientific_or_media_byte_reads_hashes_headers_decode=0,new_HF_API_HP_solver_tests_pixels_or_plots=0,
            full25_LF_path_reference_qualified=False,whole_HF5_complete=False)
        write_new(delta_file,value)
    else:
        source = read(delta_file)
        assert source['status'] == 'incremental_preparation_delivery_pass' and source['previous_delivery_commit'] == BASE
        commit = git(root,'rev-parse','HEAD').decode().strip()
        assert git(root,'rev-parse','HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root,'ls-remote','--heads','origin','main').decode().split() == [commit,'refs/heads/main']
        for tree in (root,restore):
            assert git(tree,'rev-parse','HEAD').decode().strip() == commit and not git(tree,'status','--porcelain')
        assert raw(root/MANIFEST) == raw(restore/MANIFEST) and sha(restore/MANIFEST) == source['manifest_sha256']
        current = read(restore/MANIFEST)
        entries = {row['path']:row for row in current['files']}
        allowed = {row['path'] for row in source['delta_files']}
        assert len(entries) == len(current['files']) == source['ordinary_manifest_files']
        assert sum(row['bytes'] for row in entries.values()) == source['ordinary_manifest_bytes']
        assert names(git(root,'diff','--name-only','-z',BASE,commit)) == allowed | {MANIFEST}
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        for tree in (root,restore):
            assert names(git(tree,'ls-files','-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree,row['path']) == row == entries[row['path']] for row in source['delta_files'])
            assert {path.relative_to(tree).as_posix() for path in (tree/REL).rglob('*') if path.is_file()} | FRONTS == allowed
            check_preparation(tree,entries,old)
        assert current['science_version'] == previous['science_version'] == '0.5.0' and current['science_baseline_commit'] == previous['science_baseline_commit']
        value = dict(source,status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),published_commit=commit,
            branch='main',origin=ORIGIN,source_and_restore_clean=True,remote_main_confirmed_equal=True,restore_root=str(restore),
            delta_files_restored_and_hashed=len(allowed),new_full_source_or_restore_scan=False)
        value.pop('delta_files')
        write_new(here/'source_publication_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key != 'delta_files'},ensure_ascii=False))


if __name__ == '__main__':
    main()
