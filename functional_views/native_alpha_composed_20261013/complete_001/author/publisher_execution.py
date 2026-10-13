"""Incrementally publish closed M-PATH1 observations; never open old media or new PNG bytes."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

REL = 'functional_views/native_alpha_composed_20261013/complete_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
FINAL_JSON = REL+'/author/final_execution_review.json'
FINAL_MD = REL+'/author/final_execution_review.md'
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
ORDINARY = {'.json', '.py', '.md', '.toml', '.log', '.txt'}
OUTPUTS = {'composed_path.json', 'path_index.json', 'OBSERVATIONS.md', 'path_ports.png', 'path_workpiece.png'}


def path_in(root, name):
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = (root/relative).resolve()
    path.relative_to(root)
    return path


def raw(path):
    assert path.suffix.lower() in ORDINARY, 'Ordinary bytes only; PNG/GIF identities use producer records and stat'
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


def declared_pngs(root, helper):
    expected = {REL+'/run_001/'+name for name in OUTPUTS}
    assert set(helper['outputs']) == expected, 'A missing output seal blocks publication; do not hash PNGs after closure'
    declared = {}
    for name, record in helper['outputs'].items():
        path = path_in(root, name)
        assert set(record) == {'sha256', 'bytes'} and len(record['sha256']) == 64
        assert path.is_file() and path.stat().st_size == record['bytes']
        if path.suffix.lower() == '.png':
            declared[name] = dict(path=name, **record)
        else:
            assert sha(path) == record['sha256']
    assert len(declared) == 2
    return declared


def identity(root, name, declared):
    path = path_in(root, name)
    if path.suffix.lower() == '.png':
        record = declared[name]
        assert record['path'] == name and path.stat().st_size == record['bytes']
        return dict(record)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def check_closed(root, entries, old, base, allowed, declared):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    assert protocol['schema_version'] == 'composed-saved-path-card-1.0' and protocol['card'] == 'M-PATH1'
    assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert (protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (180,240,8*1024**3)
    proof_path, reply_path = stage/'author/source_publication_receipt.json', stage/'author/direct_human_reply.json'
    proof, reply, auth = read(proof_path), read(reply_path), read(stage/'author/authorization.json')
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared_card'] == auth['card'] == reply['card'] == 'M-PATH1'
    assert proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    assert proof['published_commit'] == base and proof['previous_delivery_commit'] == protocol['source_baseline_commit']
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['authorized_execution_source_commit'] == reply['authorized_execution_source_commit'] == base
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip() and reply['reply_context']
    assert auth['new_HP_authorized'] is reply['new_HP_authorized_by_this_record'] is False
    assert auth['human_evidence_sha256'] == sha(reply_path) and auth['source_publication_receipt_sha256'] == sha(proof_path)
    assert sha(stage/'protocol.json') == auth['protocol_sha256'] == proof['protocol_sha256']
    assert len(protocol['bindings']) == 27
    for name, pin in protocol['bindings'].items():
        assert entries[name] == old[name] and old[name]['sha256'] == pin == sha(path_in(root, name))
    media = protocol['existing_GIF_identities_stat_only']
    assert len(media) == 5 and not media.keys() & protocol['bindings'].keys()
    for name, record in media.items():
        path = path_in(root, name)
        assert path.suffix.lower() == '.gif' and record == {key:old[name][key] for key in ('sha256','bytes')}
        assert entries[name] == old[name] and path.is_file() and path.stat().st_size == record['bytes']
    outer = read(stage/'path_launch.json')
    helper = read(stage/'run_001/execution_receipt.json')
    assert outer['card'] == helper['card'] == 'M-PATH1' and outer['completed_utc'] and helper['completed_utc']
    assert outer['status'] == helper['status'] == 'pass' and outer['invocations'] == 1 and outer['exit_code'] == 0
    assert outer['stop_reason'] is None and outer['all_bindings_unchanged'] is True and not (stage/'stop_requested.txt').exists()
    assert 0 <= outer['elapsed_seconds'] <= 240 and 0 <= outer['helper_wall_seconds'] <= 180
    assert 0 <= helper['elapsed_seconds'] <= 180 and outer['peak_sampled_tree_RSS_bytes'] <= 8*1024**3
    assert helper['peak_sampled_RSS_bytes'] <= 8*1024**3
    assert outer['protocol_sha256'] == helper['protocol_sha256'] == sha(stage/'protocol.json')
    assert helper['authorized_execution_source_commit'] == base
    assert all(helper[key] == 1 for key in ('compose_started','compose_completed','render_started','render_completed'))
    assert (helper['source_rows'],helper['unique_states'],helper['shared_anchors']) == (29,25,4)
    assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
    assert all(helper[key] == 0 for key in ('HF_imports','F_T_HP_solver_tests','old_scientific_or_media_byte_reads','new_GIF_decode_or_generation','default_changes'))
    assert helper['pressure_clamp_stability_HF5_qualification'] is False
    assert declared_pngs(root, helper) == declared
    data = read(stage/'run_001/composed_path.json')
    assert data['schema_version'] == 'mpath1-composed-observations-1.0' and data['status'] == 'composed_saved_observations'
    assert data['counts'] == dict(source_segments=5,raw_rows=29,unique_rows=25,shared_anchors=4)
    assert len(data['raw_rows']) == 29 and len(data['unique_rows']) == 25 and len(data['anchor_join_ledger']) == 4
    assert all(value is False for value in data['composition_claims'].values())
    assert data['scientific_calls'] == data['scientific_or_media_bytes_read_or_hashed'] == 0
    assert data['sources'][0]['status']['status'] == 'failed'
    closure = read(stage/'author/execution_documentation_receipt.json')
    assert closure['source_baseline_commit'] == base and closure['actual_execution_closed'] is True
    assert closure['actual_execution_status'] == 'pass' and {row['path'] for row in closure['front_history']} == FRONTS
    for row in closure['front_history']:
        prior = git(root,'show',base+':'+row['path'])
        current = raw(root/row['path'])
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert entries[row['path']]['sha256'] == row['new_sha256'] == sha256(current).hexdigest()
    review = read(root/FINAL_JSON)
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    assert review['authorized'] is review['executed'] is review['execution_closed'] is True and review['execution_status'] == 'pass'
    assert review['protocol_SHA256'] == sha(stage/'protocol.json') and review['declared_binary_identities'] == declared
    ordinary = {name for name in allowed if Path(name).suffix.lower() in ORDINARY}-{FINAL_JSON}
    assert FINAL_MD in ordinary and ordinary <= review['reviewed_repository_SHA256'].keys()
    assert FINAL_JSON not in review['reviewed_repository_SHA256']
    assert all(entries[name]['sha256'] == pin == sha(path_in(root,name)) for name,pin in review['reviewed_repository_SHA256'].items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('finalize','verify'))
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--restore',type=Path,default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root,restore,here = args.repo.resolve(),args.restore.resolve(),Path(__file__).resolve().parent
    assert not here.is_relative_to(root), 'Run the external publisher; the formal copy is recovery evidence only'
    proof = read(root/REL/'author/source_publication_receipt.json')
    base = proof['published_commit']
    oldraw = git(root,'show',base+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']:row for row in previous['files']}
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared_card'] == 'M-PATH1'
    assert proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    assert proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert len(old) == len(previous['files']) == proof['ordinary_manifest_files']
    assert sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes']
    assert previous['science_version'] == '0.5.0'
    actual = {path.relative_to(root).as_posix() for path in (root/REL).rglob('*') if path.is_file()}
    allowed = (actual-old.keys()) | FRONTS
    assert allowed & old.keys() == FRONTS and {FINAL_JSON,FINAL_MD} <= allowed
    assert all(Path(name).suffix.lower() in ORDINARY | {'.png'} for name in allowed)
    helper = read(root/REL/'run_001/execution_receipt.json')
    declared = declared_pngs(root,helper)
    assert declared.keys() == {name for name in allowed if Path(name).suffix.lower() == '.png'}
    delta_file = here/'execution_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root,restore):
        assert git(tree,'branch','--show-current').decode().strip() == 'main'
        assert git(tree,'remote','get-url','origin').decode().strip() == ORIGIN
        assert git(tree,'remote','get-url','--push','origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root,'rev-parse','HEAD').decode().strip() == base and not delta_file.exists()
        assert raw(root/MANIFEST) == oldraw and not git(root,'diff','--name-only')
        assert not git(root,'ls-files','--others','--exclude-standard','-z')
        paths = names(git(root,'ls-files','-z'))-{MANIFEST}
        assert not old.keys()-paths
        assert names(git(root,'diff','--cached','--name-only','-z',base)) == allowed == (paths-old.keys()) | FRONTS
        delta = [identity(root,name,declared) for name in sorted(allowed)]
        entries = dict(old, **{row['path']:row for row in delta})
        assert paths == entries.keys()
        check_closed(root,entries,old,base,allowed,declared)
        manifest = dict(previous,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=base,
            storage_stage='composed_saved_alpha_path_closed_pass_001',files=[entries[name] for name in sorted(paths)])
        output = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(output)
        value = dict(status='incremental_execution_delivery_pass',previous_delivery_commit=base,
            manifest_sha256=sha256(output).hexdigest(),ordinary_manifest_files=len(entries),ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta,delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(old)-len(FRONTS),
            protocol_sha256=sha(root/REL/'protocol.json'),executed_card='M-PATH1',authorized=True,executed=True,execution_closed=True,execution_status='pass',
            ordinary_input_bindings_checked=27,existing_GIF_identities_inherited_and_stat_only=5,new_PNG_identities_from_closed_producer_stat_only=2,
            old_scientific_or_media_byte_reads=0,new_PNG_byte_reads_or_hashes=0,new_HF_API_HP_solver_tests_pixels_or_plots=0,
            default_changes=0,new_full_source_scan=False,single_full_path_producer_run=False,full_path_reference_qualified=False,whole_HF5_complete=False)
        write_new(delta_file,value)
    else:
        source = read(delta_file)
        assert source['status'] == 'incremental_execution_delivery_pass' and source['previous_delivery_commit'] == base
        assert {row['path'] for row in source['delta_files']} == allowed
        commit = git(root,'rev-parse','HEAD').decode().strip()
        assert git(root,'rev-parse','HEAD^').decode().strip() == base and commit != base
        assert git(root,'ls-remote','--heads','origin','main').decode().split() == [commit,'refs/heads/main']
        for tree in (root,restore):
            assert git(tree,'rev-parse','HEAD').decode().strip() == commit and not git(tree,'status','--porcelain')
        assert raw(root/MANIFEST) == raw(restore/MANIFEST) and sha(restore/MANIFEST) == source['manifest_sha256']
        current = read(restore/MANIFEST)
        entries = {row['path']:row for row in current['files']}
        assert len(entries) == len(current['files']) == source['ordinary_manifest_files']
        assert sum(row['bytes'] for row in entries.values()) == source['ordinary_manifest_bytes']
        assert names(git(root,'diff','--name-only','-z',base,commit)) == allowed | {MANIFEST}
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        for tree in (root,restore):
            assert names(git(tree,'ls-files','-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree,row['path'],declared) == row == entries[row['path']] for row in source['delta_files'])
            assert ({path.relative_to(tree).as_posix() for path in (tree/REL).rglob('*') if path.is_file()}-old.keys()) | FRONTS == allowed
            check_closed(tree,entries,old,base,allowed,declared)
        assert current['previous_delivery_commit'] == base and current['science_version'] == previous['science_version']
        assert current['science_baseline_commit'] == previous['science_baseline_commit']
        value = dict(source,status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),published_commit=commit,
            branch='main',origin=ORIGIN,source_and_restore_clean=True,remote_main_confirmed_equal=True,restore_root=str(restore),delta_files_restored=len(allowed),
            PNG_restore_check='stat plus original closed producer identity; no PNG rehash',new_full_source_or_restore_scan=False)
        value.pop('delta_files')
        write_new(here/'execution_publication_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key != 'delta_files'},ensure_ascii=False))


if __name__ == '__main__':
    main()
