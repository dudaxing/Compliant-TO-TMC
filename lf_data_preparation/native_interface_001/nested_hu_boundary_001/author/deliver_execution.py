"""Incremental M-BOUND1 closure publication/restoration; ordinary bytes only."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE = Path('D:/hf-restore-20260930')
EXT = Path(__file__).resolve().parent
BASE = 'eb68c00d50b28de89a475c18a0879be4a4482f68'
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
MODULE = 'hf_repo/src/hf_eval/saved_q1_hu_boundary.py'
PROTOCOL_SHA = 'f27d201b01efc5c49212a43536e928ba6ac88ba4346ac6949dccdfcac8d94e33'
M = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',REL+'/README.md'}
PREVIOUS = ROOT/REL/'author/M_BOUND1_source_publication_receipt.json'
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
read = lambda p: json.loads(p.read_bytes())
sha = lambda p: sha256(p.read_bytes()).hexdigest()
git = lambda root,*a: subprocess.check_output(['git','-c','gc.auto=0',*a],cwd=root)

def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def identity(root,name):
    p = root/name
    return dict(path=name,bytes=p.stat().st_size,sha256=sha(p))

def execution_checks(root,config):
    assert sha(root/REL/'protocol.json') == config['protocol_sha256'] == PROTOCOL_SHA
    p = read(root/REL/'protocol.json')
    assert p['prepared'] and p['authorized'] is False and p['executed'] is False
    assert p['schema_version'] == 'saved-Q1-Hu-boundary-card-1.0'
    assert p['selected_endpoint_cell_ids'] == [10371,10407,10408]
    assert [(r['index'],r['leg'],r['d_mm']) for r in p['selected_states']] == [(6,'loading',.85),(13,'loading',1.2)]
    assert len(p['bindings']) == config['binding_count'] == 45
    assert all(sha(root/n) == pin for n,pin in p['bindings'].items())
    assert sha(root/MODULE) == p['bindings'][MODULE]
    assert [list(plan['selected_fields']) for plan in p['selected_archive_plan']] == [
        ['element_regularization_force'],['element_regularization_force']]
    assert p['expected_calls'] == config['expected_calls'] and p['expected_counts'] == config['expected_counts']
    assert set(p['phases']) == {'hu_boundary'}
    assert (p['phases']['hu_boundary']['helper_seconds'],p['phases']['hu_boundary']['outer_seconds'],p['sampled_RSS_bytes']) == (180,240,8589934592)
    assert not (root/REL/'stop_requested.txt').exists()
    for name,pin in config['record_pins'].items():
        assert sha(root/name) == pin,(name,'record pin')
    for name,pin in config['peer_reviews'].items():
        assert sha(root/name) == pin
        status = read(root/name)['status']
        if name.endswith('/physical_results_review.json'):
            assert status == 'completed_actual_saved_result_interpretation_no_new_scientific_gate'
        else:
            assert status.startswith('pass')
    auth = read(root/REL/'author/authorization.json')
    evidence = read(root/REL/'author/direct_human_reply.json')
    assert evidence['authorization_from_direct_human_reply'] is True and evidence['card'] == 'M-BOUND1'
    assert evidence['approved_source_commit'] == auth['approved_source_commit'] == BASE and auth['authorized'] is True
    assert auth['human_evidence_sha256'] == sha(root/REL/'author/direct_human_reply.json')
    assert auth['direct_human_answer'] == evidence['direct_human_answer'] and evidence['direct_human_answer'].strip()
    assert evidence['reply_context'].strip()
    helper = read(root/REL/'run_001/execution_receipt.json')
    outer = read(root/REL/'hu_boundary_launch.json')
    assert helper['status'] == outer['status'] == 'pass'
    assert helper['protocol_sha256'] == outer['protocol_sha256'] == PROTOCOL_SHA
    assert helper['all_bindings_unchanged'] and outer['all_bindings_unchanged']
    assert helper['calls'] == config['expected_calls'] and helper['counts'] == config['expected_counts']
    assert outer['invocations'] == 1 and outer['exit_code'] == 0 and outer['stop_reason'] is None
    assert set(config['output_files']) == set(p['expected_output_files']) and len(config['output_files']) == 10
    assert set(n.name for n in (root/p['output_directory']).iterdir()) == set(config['output_files'])
    assert set(helper['output_SHA256']) == set(config['output_files'])-{'execution_receipt.json'}
    assert all(sha(root/p['output_directory']/n) == pin for n,pin in helper['output_SHA256'].items())
    doc = read(root/REL/'author/documentation_receipt.json')
    assert doc['status'] == 'pass_actual_execution_documentation_closed' and doc['execution_closed']
    assert doc['source_commit'] == BASE and sha(root/REL/'RESULTS.md') == doc['result_sha256']
    assert sha(root/REL/'NEXT_STEP_REVIEW.md') == doc['next_step_sha256']
    assert doc['actions']['new_candidate_runs'] == doc['actions']['new_NPZ_decodes'] == doc['actions']['new_projection_fsum_integral_render'] == 0
    assert {r['path'] for r in doc['front_history']} == FRONTS
    for row in doc['front_history']:
        prior = git(root,'show',BASE+':'+row['path'])
        current = (root/row['path']).read_bytes()
        assert len(prior) == row['old_bytes'] and sha256(prior).hexdigest() == row['old_sha256']
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha(root/row['path']) == row['new_sha256']
    for name in [REL+'/README.md',REL+'/RESULTS.md',REL+'/NEXT_STEP_REVIEW.md',*sorted(FRONTS)]:
        text = (root/name).read_text(encoding='utf-8').split('<details>',1)[0]
        assert '\ufffd' not in text
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if '://' in target or target.startswith('#'): continue
            path = ((root/name).parent/target.split('#')[0]).resolve()
            path.relative_to(root)
            assert path.exists(),(name,target)
    return p,doc

parser = argparse.ArgumentParser()
parser.add_argument('mode',choices=('finalize','verify'))
args = parser.parse_args()
config = read(EXT/'execution_delivery_config.json')
assert (ROOT/REL/'author/execution_delivery_config.json').read_bytes() == (EXT/'execution_delivery_config.json').read_bytes()
previous = read(PREVIOUS)
assert previous['status'] == 'published_and_incrementally_restored_pass'
assert previous['published_commit'] == BASE and previous['authorized'] is False and previous['executed'] is False
assert previous['source_and_restore_clean']
oldraw = git(ROOT,'show',BASE+':'+M)
assert sha256(oldraw).hexdigest() == previous['manifest_sha256']
old = json.loads(oldraw)
old_entries = {e['path']:e for e in old['files']}
delta_path = EXT/'execution_delivery_delta_verify.json'

if args.mode == 'finalize':
    assert not delta_path.exists() and git(ROOT,'rev-parse','HEAD').decode().strip() == BASE
    assert git(ROOT,'branch','--show-current').decode().strip() == 'main'
    assert git(ROOT,'remote','get-url','origin').decode().strip() == ORIGIN
    assert (ROOT/M).read_bytes() == oldraw and not git(ROOT,'diff','--name-only')
    paths = [n.decode('utf-8') for n in git(ROOT,'ls-files','-z').split(b'\0') if n and n.decode('utf-8') != M]
    changed = {n.decode('utf-8') for n in git(ROOT,'diff','--cached','--name-only','-z',BASE).split(b'\0') if n}
    new = set(paths)-old_entries.keys()
    assert not (old_entries.keys()-set(paths)) and changed == FRONTS|new
    assert all(n.startswith(REL+'/') for n in new)
    p,doc = execution_checks(ROOT,config)
    delta = [identity(ROOT,n) for n in sorted(changed)]
    replacements = {e['path']:e for e in delta}
    manifest = dict(old,created_utc=datetime.now(timezone.utc).isoformat(),
        storage_stage='nested_saved_q1_hu_boundary_execution_closed_001',previous_delivery_commit=BASE,
        files=[replacements[n] if n in changed else old_entries[n] for n in paths])
    raw = (json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    (ROOT/M).write_bytes(raw)
    receipt = dict(status='incremental_execution_delivery_pass',previous_delivery_commit=BASE,
        manifest_sha256=sha256(raw).hexdigest(),ordinary_manifest_files=len(paths),ordinary_manifest_bytes=sum(e['bytes'] for e in manifest['files']),
        delta_files=delta,new_files=len(new),changed_old_files=len(FRONTS),delta_bytes=sum(e['bytes'] for e in delta),
        unchanged_manifest_entries_exactly_inherited=len(old_entries)-len(FRONTS),inherited_restoration_receipt=str(PREVIOUS),
        protocol_sha256=config['protocol_sha256'],binding_count=len(p['bindings']),peer_reviews=config['peer_reviews'],
        authorized=True,executed=True,execution_closed=True,new_full_source_scan=False,
        new_NPZ_decodes_or_contraction_or_render_in_delivery=0,whole_HF5_complete=False)
    write_new(delta_path,receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('delta_files','peer_reviews')},ensure_ascii=False))
else:
    source = read(delta_path)
    assert source['status'] == 'incremental_execution_delivery_pass' and source['execution_closed']
    commit = git(ROOT,'rev-parse','HEAD').decode().strip()
    assert commit != BASE and git(ROOT,'rev-parse','HEAD^').decode().strip() == BASE
    assert git(ROOT,'ls-remote','--heads','origin','main').decode().split() == [commit,'refs/heads/main']
    for root in (ROOT,RESTORE):
        assert git(root,'rev-parse','HEAD').decode().strip() == commit
        assert git(root,'branch','--show-current').decode().strip() == 'main'
        assert git(root,'remote','get-url','origin').decode().strip() == ORIGIN and not git(root,'status','--porcelain')
    assert (ROOT/M).read_bytes() == (RESTORE/M).read_bytes() and sha(RESTORE/M) == source['manifest_sha256']
    assert (RESTORE/REL/'author/execution_delivery_config.json').read_bytes() == (EXT/'execution_delivery_config.json').read_bytes()
    manifest = read(RESTORE/M)
    entries = {e['path']:e for e in manifest['files']}
    assert len(entries) == len(manifest['files']) == source['ordinary_manifest_files']
    assert sum(e['bytes'] for e in entries.values()) == source['ordinary_manifest_bytes']
    paths = {n.decode('utf-8') for n in git(RESTORE,'ls-files','-z').split(b'\0') if n}
    assert paths-{M} == entries.keys()
    delta = source['delta_files']
    delta_names = {e['path'] for e in delta}
    changed = {n.decode('utf-8') for n in git(ROOT,'diff','--name-only','-z',BASE,commit).split(b'\0') if n}
    assert changed == delta_names|{M}
    assert all(identity(RESTORE,e['path']) == e == entries[e['path']] for e in delta)
    unchanged = old_entries.keys()-delta_names
    assert len(unchanged) == source['unchanged_manifest_entries_exactly_inherited']
    assert all(entries[n] == old_entries[n] for n in unchanged)
    assert manifest['science_version'] == old['science_version'] == '0.5.0'
    assert manifest['science_baseline_commit'] == old['science_baseline_commit']
    execution_checks(RESTORE,config)
    receipt = dict(status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),
        published_commit=commit,previous_delivery_commit=BASE,branch='main',origin=ORIGIN,remote_main_confirmed_equal=True,
        source_and_restore_clean=True,restore_root=str(RESTORE),manifest_sha256=source['manifest_sha256'],
        ordinary_manifest_files=len(entries),ordinary_manifest_bytes=source['ordinary_manifest_bytes'],
        delta_files_restored_and_hashed=len(delta),delta_bytes=source['delta_bytes'],unchanged_manifest_entries_inherited=len(unchanged),
        inherited_restoration_receipt=str(PREVIOUS),protocol_sha256=config['protocol_sha256'],binding_count=config['binding_count'],
        peer_reviews=config['peer_reviews'],authorized=True,executed=True,execution_closed=True,new_full_source_or_restore_scan=False,
        new_NPZ_decodes_or_contraction_or_render_in_delivery=0,original_science_and_qualification_unchanged=True,whole_HF5_complete=False)
    write_new(EXT/'publication_receipt.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))
