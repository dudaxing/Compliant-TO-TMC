"""Incremental delivery of prepared, numerically unexecuted M-SUPPORT1 sources.

Uses the actual frozen protocol and preparation receipt. This delivery tool
does not authorize or execute the candidate, decode arrays or render plots.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT=Path(__file__).parent
BASE='96bfea73ebb538d413dd01b722fa1f3a6d43913d'
M='handoff/repository_manifest.json'
REL='lf_data_preparation/native_interface_001/nested_material_support_001'
MODULE='hf_repo/src/hf_eval/saved_material_support.py'
FRONTS={'docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md','lf_data_preparation/native_interface_001/nested_material_trace_001/README.md'}
PREVIOUS=Path('D:/hf-native-workpiece-api-author-20261009/MPTRACE1_execution_review_001/publication_receipt.json')
OUT=EXT/'source_delivery_delta_verify.json'
# Frozen from the actual prepared protocol and preparation receipt.
# Peer report paths are staged before this source-delivery tool is used.
FROZEN={'protocol_sha256': '42f4cab8a966b4f8f082b06da169b13e878420e067c0f0b3c9d629ea32fb0947',
 'binding_count': 36,
 'phase': 'support',
 'helper_seconds': 180,
 'outer_seconds': 240,
 'sampled_RSS_bytes': 8589934592,
 'expected_calls': {'NPZ_read_started': 3,
                    'NPZ_read_completed': 3,
                    'selected_array_fields': 8,
                    'support_started': 2,
                    'support_completed': 2,
                    'global_replay': 2,
                    'PNG_writes': 2},
 'card_path': 'lf_data_preparation/native_interface_001/nested_material_support_001/M-SUPPORT1_CARD.md',
 'peer_reports': ['lf_data_preparation/native_interface_001/nested_material_support_001/author/support_static_physics_review.json',
                  'lf_data_preparation/native_interface_001/nested_material_support_001/author/final_source_static_review.json'],
 'preparation_actions': {'AST_parse_only': 4,
                         'candidate_imports': 0,
                         'NPZ_decodes': 0,
                         'new_material_scatter_projection_fsum_plot_calls': 0,
                         'force_kernel_tangent_HP_solver_calls': 0}}
assert FROZEN is not None, 'Missing frozen M-SUPPORT1 source configuration'

git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT)
read=lambda path:json.loads(path.read_bytes())
assert not OUT.exists() and git('rev-parse','HEAD').decode().strip()==BASE
assert git('branch','--show-current').decode().strip()=='main'
assert git('remote','get-url','origin').decode().strip()=='https://github.com/dudaxing/Compliant-TO-TMC.git'
previous=read(PREVIOUS)
assert previous['status']=='published_and_incrementally_restored_pass'
assert previous['published_commit']==BASE and previous['source_and_restore_clean'] and previous['execution_closed']
old_raw=git('show',BASE+':'+M)
assert (ROOT/M).read_bytes()==old_raw
assert sha256(old_raw).hexdigest()==previous['manifest_sha256']=='36765b646be480a826c2f41ca7498e3bc6823032503a7afed977d02a4983ccfd'
old=json.loads(old_raw)
entries={entry['path']:entry for entry in old['files']}
assert len(entries)==18474 and sum(e['bytes'] for e in entries.values())==9283531733
paths=[p.decode('utf-8') for p in git('ls-files','-z').split(b'\0') if p and p.decode('utf-8')!=M]
changed={p.decode('utf-8') for p in git('diff','--cached','--name-only','-z',BASE).split(b'\0') if p}
new=set(paths)-entries.keys()
assert not (entries.keys()-set(paths)) and changed & entries.keys()==FRONTS and changed==FRONTS|new
assert MODULE in new and all(p==MODULE or p.startswith(REL+'/') for p in new)
assert not git('diff','--name-only')
cache={}

def identity(name):
    if name not in cache:
        path=ROOT/name
        cache[name]=dict(path=name,bytes=path.stat().st_size,sha256=sha256(path.read_bytes()).hexdigest())
    return cache[name]

protocol=read(ROOT/REL/'protocol.json')
assert identity(REL+'/protocol.json')['sha256']==FROZEN['protocol_sha256']
assert protocol['prepared'] and protocol['authorized'] is False and protocol['executed'] is False
assert len(protocol['bindings'])==FROZEN['binding_count']
assert all(identity(p)['sha256']==pin for p,pin in protocol['bindings'].items())
assert [(i['index'],i['original_target_index'],i['leg'],i['d_mm']) for i in protocol['selected_states']]==[(6,6,'loading',.85),(13,13,'loading',1.2)]
archive_plan=protocol['selected_archive_plan']
assert len(archive_plan)==3
assert list(archive_plan[0]['selected_fields'])==['coordinates','connectivity','edofs','workpiece_nodes']
assert all(list(a['selected_fields'])==['element_material_force','global_material_force'] for a in archive_plan[1:])
assert sum(len(a['selected_fields']) for a in archive_plan)==8
assert protocol['expected_calls']==FROZEN['expected_calls']
assert set(protocol['phases'])=={FROZEN['phase']}
phase=protocol['phases'][FROZEN['phase']]
assert (phase['helper_seconds'],phase['outer_seconds'],protocol['sampled_RSS_bytes'])==(FROZEN['helper_seconds'],FROZEN['outer_seconds'],FROZEN['sampled_RSS_bytes'])
assert not (ROOT/protocol['output_directory']).exists()
assert not (ROOT/REL/(FROZEN['phase']+'_launch.json')).exists()
preparation=read(ROOT/REL/'author/preparation_receipt.json')
assert preparation['status']=='source_prepared_not_executed' and not preparation['authorized'] and not preparation['executed']
assert preparation['preparation_actions']==FROZEN['preparation_actions']
assert all(value==0 for key,value in preparation['preparation_actions'].items() if key!='AST_parse_only')
assert preparation['protocol_sha256']==FROZEN['protocol_sha256'] and preparation['bindings']==FROZEN['binding_count']
assert {h['path'] for h in preparation['front_history']}==FRONTS
for history in preparation['front_history']:
    prior=git('show',BASE+':'+history['path'])
    current=(ROOT/history['path']).read_bytes()
    assert len(prior)==history['old_bytes'] and sha256(prior).hexdigest()==history['old_sha256']
    assert current[history['history_start_byte']:history['history_end_byte_exclusive']]==prior
    assert identity(history['path'])['sha256']==history['new_sha256']
peers={}
for name in FROZEN['peer_reports']:
    assert name.startswith(REL+'/author/') and read(ROOT/name)['status'].startswith('pass')
    peers[name]=identity(name)['sha256']
links=[]
for name in [REL+'/README.md',FROZEN['card_path'],*sorted(FRONTS)]:
    text=(ROOT/name).read_text(encoding='utf-8').split('<details>',1)[0]
    assert '\ufffd' not in text
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if '://' in target or target.startswith('#'):continue
        path=((ROOT/name).parent/target.split('#')[0]).resolve()
        path.relative_to(ROOT)
        assert path.exists(),(name,target)
        links.append(dict(document=name,target=target))
delta=[identity(p) for p in sorted(changed)]
manifest=dict(old)
manifest.update(created_utc=datetime.now(timezone.utc).isoformat(),storage_stage='nested_saved_material_support_source_prepared_001',
    previous_delivery_commit=BASE,files=[identity(p) if p in changed else entries[p] for p in paths])
raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
(ROOT/M).write_bytes(raw)
receipt=dict(status='incremental_source_delivery_pass',created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
    manifest_sha256=sha256(raw).hexdigest(),ordinary_manifest_files=len(paths),ordinary_manifest_bytes=sum(e['bytes'] for e in manifest['files']),
    new_files=len(new),changed_old_files=len(FRONTS),new_or_changed_files_directly_hashed=len(delta),delta_bytes=sum(e['bytes'] for e in delta),
    unchanged_manifest_entries_exactly_inherited=len(entries)-len(FRONTS),inherited_restoration_receipt=str(PREVIOUS),new_full_source_scan=False,
    protocol_checks=[dict(protocol=REL+'/protocol.json',protocol_sha256=identity(REL+'/protocol.json')['sha256'],bindings_checked=FROZEN['binding_count'],phase=FROZEN['phase'])],
    peer_reviews=peers,delta_files=delta,local_links_checked=len(links),M_SUPPORT1_authorized=False,M_SUPPORT1_executed=False,
    NPZ_decodes_or_support_or_render_in_delivery=0,original_science_and_qualification_unchanged=True,whole_HF5_complete=False)
with OUT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('delta_files','peer_reviews')},ensure_ascii=False))
