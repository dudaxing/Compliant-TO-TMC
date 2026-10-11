"""Incremental delivery of the completed M-SUPPORT1 saved diagnostic.

Uses frozen actual documentation and literal peer statuses. This delivery
does not rerun the candidate, decode NPZ arrays or render plots.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT=Path(__file__).parent
BASE='fa872739247a2a5d96043b1c05d28e9f08a77b88'
M='handoff/repository_manifest.json'
REL='lf_data_preparation/native_interface_001/nested_material_support_001'
FRONTS={'docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',REL+'/README.md','lf_data_preparation/native_interface_001/nested_material_trace_001/README.md'}
PREVIOUS=Path('D:/hf-native-workpiece-api-author-20261009/MSUPPORT1_source_prepare_001/publication_receipt.json')
OUT=EXT/'execution_delivery_delta_verify.json'
# Frozen from actual final docs; root archives all four peer records before delivery.
FROZEN={'protocol_sha256': '42f4cab8a966b4f8f082b06da169b13e878420e067c0f0b3c9d629ea32fb0947',
 'results_sha256': 'fce02e25b7b86451b78860646a256bde84013c9f4b9b3f6c5ab33f8747b74980',
 'documentation_receipt_sha256': '8f8392d1a861210edf9e3d164837e9692ca69924ee3b59015ecdb1e75d3a5b68',
 'documentation_actions': {'results_written': 1,
                           'fronts_updated': 4,
                           'peer_records_archived': 3,
                           'raw_author_scripts_archived': 2,
                           'new_candidate_runs': 0,
                           'new_NPZ_decodes': 0,
                           'new_projection_fsum_integral_render': 0},
 'peer_status': {'lf_data_preparation/native_interface_001/nested_material_support_001/author/terminal_execution_review.json': 'pass_actual_saved_execution_terminal_review',
                 'lf_data_preparation/native_interface_001/nested_material_support_001/author/physical_results_review.json': 'completed_actual_saved_result_interpretation_no_new_scientific_gate',
                 'lf_data_preparation/native_interface_001/nested_material_support_001/author/visual_review.json': 'pass_actual_images_inspected_with_limits',
                 'lf_data_preparation/native_interface_001/nested_material_support_001/author/final_results_review.json': 'pass_actual_results_documents_and_delivery_tools_static_review'}}
assert FROZEN is not None, 'Missing frozen M-SUPPORT1 execution delivery configuration'
git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT)
read=lambda p:json.loads(p.read_bytes())
assert not OUT.exists() and git('rev-parse','HEAD').decode().strip()==BASE
assert git('branch','--show-current').decode().strip()=='main'
assert git('remote','get-url','origin').decode().strip()=='https://github.com/dudaxing/Compliant-TO-TMC.git'
previous=read(PREVIOUS)
assert previous['status']=='published_and_incrementally_restored_pass'
assert previous['published_commit']==BASE and previous['source_and_restore_clean']
assert previous['M_SUPPORT1_authorized'] is False and previous['M_SUPPORT1_executed'] is False
old_raw=git('show',BASE+':'+M)
assert (ROOT/M).read_bytes()==old_raw
assert sha256(old_raw).hexdigest()==previous['manifest_sha256']=='ac690b288efb49d27e37eb203a6a7b221f8a9cdae7a6b4947a62599e35e9ca2d'
old=json.loads(old_raw)
entries={e['path']:e for e in old['files']}
assert len(entries)==18489 and sum(e['bytes'] for e in entries.values())==9283706057
paths=[p.decode('utf-8') for p in git('ls-files','-z').split(b'\0') if p and p.decode('utf-8')!=M]
changed={p.decode('utf-8') for p in git('diff','--cached','--name-only','-z',BASE).split(b'\0') if p}
new=set(paths)-entries.keys()
assert not (entries.keys()-set(paths)) and changed & entries.keys()==FRONTS and changed==FRONTS|new
assert all(p.startswith(REL+'/') for p in new) and not git('diff','--name-only')
cache={}
def identity(name):
    if name not in cache:
        p=ROOT/name
        cache[name]=dict(path=name,bytes=p.stat().st_size,sha256=sha256(p.read_bytes()).hexdigest())
    return cache[name]
protocol=read(ROOT/REL/'protocol.json')
assert identity(REL+'/protocol.json')['sha256']==FROZEN['protocol_sha256']
assert len(protocol['bindings'])==36 and all(identity(p)['sha256']==pin for p,pin in protocol['bindings'].items())
authorization=read(ROOT/REL/'author/authorization.json')
assert authorization['authorized'] and authorization['approved_source_commit']==BASE
assert authorization['protocol_sha256']==identity(REL+'/protocol.json')['sha256']
launch=read(ROOT/REL/'support_launch.json')
helper=read(ROOT/REL/'run_001/execution_receipt.json')
assert launch['status']==helper['status']=='pass' and launch['invocations']==1 and launch['exit_code']==0
assert launch['stop_reason'] is None and launch['all_bindings_unchanged'] and helper['all_bindings_unchanged']
assert not (ROOT/REL/'stop_requested.txt').exists()
assert launch['bindings']==protocol['bindings'] and launch['protocol_sha256']==helper['protocol_sha256']==identity(REL+'/protocol.json')['sha256']
assert helper['calls']==protocol['expected_calls']==dict(NPZ_read_started=3,NPZ_read_completed=3,selected_array_fields=8,support_started=2,support_completed=2,global_replay=2,PNG_writes=2)
assert helper['counts']==dict(occurrences_total=5476,cells_total=1444,nodes_total=1406,groups_total=10,whole_total=2)
assert helper['elapsed_seconds']<=180 and launch['elapsed_seconds']<=240
assert max(helper['sampled_peak_RSS_bytes'],launch['peak_sampled_tree_RSS_bytes'])<=protocol['sampled_RSS_bytes']==8*1024**3
assert {p.name for p in (ROOT/REL/'run_001').iterdir()}==set(protocol['expected_output_files'])
assert set(helper['output_SHA256'])==set(protocol['expected_output_files'])-{'execution_receipt.json'}
assert all(identity(REL+'/run_001/'+p)['sha256']==pin for p,pin in helper['output_SHA256'].items())
assert len(protocol['expected_output_files'])==9
assert identity(REL+'/RESULTS.md')['sha256']==FROZEN['results_sha256']
assert identity(REL+'/author/documentation_receipt.json')['sha256']==FROZEN['documentation_receipt_sha256']
documentation=read(ROOT/REL/'author/documentation_receipt.json')
assert documentation['source_commit']==BASE and documentation['execution_closed']
assert documentation['protocol_sha256']==FROZEN['protocol_sha256']
assert identity(REL+'/author/authorization.json')['sha256']==documentation['authorization_sha256']
assert documentation['actions']==FROZEN['documentation_actions']
assert {h['path'] for h in documentation['front_history']}==FRONTS
for history in documentation['front_history']:
    prior=git('show',BASE+':'+history['path'])
    current=(ROOT/history['path']).read_bytes()
    assert len(prior)==history['old_bytes'] and sha256(prior).hexdigest()==history['old_sha256']
    assert current[history['history_start_byte']:history['history_end_byte_exclusive']]==prior
    assert identity(history['path'])['sha256']==history['new_sha256']
peers={}
for name,status in FROZEN['peer_status'].items():
    assert name.startswith(REL+'/author/') and read(ROOT/name)['status']==status
    peers[name]=identity(name)['sha256']
links=[]
for name in [REL+'/RESULTS.md',*sorted(FRONTS)]:
    text=(ROOT/name).read_text(encoding='utf-8').split('<details>',1)[0]
    assert '\ufffd' not in text
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if '://' in target or target.startswith('#'):continue
        p=((ROOT/name).parent/target.split('#')[0]).resolve()
        p.relative_to(ROOT)
        assert p.exists(),(name,target)
        links.append(dict(document=name,target=target))
delta=[identity(p) for p in sorted(changed)]
manifest=dict(old)
manifest.update(created_utc=datetime.now(timezone.utc).isoformat(),storage_stage='nested_two_state_material_support_execution_pass_001',
    previous_delivery_commit=BASE,files=[identity(p) if p in changed else entries[p] for p in paths])
raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
(ROOT/M).write_bytes(raw)
receipt=dict(status='incremental_execution_delivery_pass',created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
    manifest_sha256=sha256(raw).hexdigest(),ordinary_manifest_files=len(paths),ordinary_manifest_bytes=sum(e['bytes'] for e in manifest['files']),
    new_files=len(new),changed_old_files=len(FRONTS),new_or_changed_files_directly_hashed=len(delta),delta_bytes=sum(e['bytes'] for e in delta),
    unchanged_manifest_entries_exactly_inherited=len(entries)-len(FRONTS),inherited_restoration_receipt=str(PREVIOUS),new_full_source_scan=False,
    protocol_checks=[dict(protocol=REL+'/protocol.json',protocol_sha256=identity(REL+'/protocol.json')['sha256'],bindings_checked=36)],
    peer_reviews=peers,delta_files=delta,local_links_checked=len(links),M_SUPPORT1_authorized=True,M_SUPPORT1_executed=True,
    execution_closed=True,NPZ_decodes_or_support_or_render_in_delivery=0,original_science_and_qualification_unchanged=True,whole_HF5_complete=False)
with OUT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('delta_files','peer_reviews')},ensure_ascii=False))
