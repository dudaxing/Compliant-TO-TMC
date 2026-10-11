"""Verify restoration of the same published, numerically unexecuted source delta.

Uses the actual frozen M-SUPPORT1 protocol identity and binding count.
No candidate, array decoding, new support calculation or plotting occurs here.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE=Path('D:/hf-restore-20260930')
EXT=Path(__file__).parent
BASE='96bfea73ebb538d413dd01b722fa1f3a6d43913d'
M='handoff/repository_manifest.json'
REL='lf_data_preparation/native_interface_001/nested_material_support_001'
OUT=EXT/'publication_receipt.json'
# Frozen from the actual prepared source protocol; no numerical run is implied.
FROZEN={'protocol_sha256': '42f4cab8a966b4f8f082b06da169b13e878420e067c0f0b3c9d629ea32fb0947', 'binding_count': 36}
assert FROZEN is not None, 'Missing frozen M-SUPPORT1 source configuration'

git=lambda root,*args:subprocess.check_output(['git',*args],cwd=root)
read=lambda path:json.loads(path.read_bytes())
assert not OUT.exists()
source=read(EXT/'source_delivery_delta_verify.json')
assert source['status']=='incremental_source_delivery_pass'
assert not source['M_SUPPORT1_authorized'] and not source['M_SUPPORT1_executed']
previous=read(Path(source['inherited_restoration_receipt']))
assert previous['status']=='published_and_incrementally_restored_pass'
assert previous['published_commit']==BASE and previous['source_and_restore_clean'] and previous['execution_closed']
commit=git(ROOT,'rev-parse','HEAD').decode().strip()
assert commit!=BASE
for root in (ROOT,RESTORE):
    assert git(root,'rev-parse','HEAD').decode().strip()==commit
    assert git(root,'branch','--show-current').decode().strip()=='main'
    assert git(root,'remote','get-url','origin').decode().strip()=='https://github.com/dudaxing/Compliant-TO-TMC.git'
    assert not git(root,'status','--porcelain')
assert git(ROOT,'ls-remote','--heads','origin','main').decode().split()==[commit,'refs/heads/main']
raw=(ROOT/M).read_bytes()
assert (RESTORE/M).read_bytes()==raw and sha256(raw).hexdigest()==source['manifest_sha256']
manifest=json.loads(raw)
entries={e['path']:e for e in manifest['files']}
assert len(entries)==len(manifest['files'])==source['ordinary_manifest_files']
assert manifest['previous_delivery_commit']==BASE
paths={p.decode('utf-8') for p in git(RESTORE,'ls-files','-z').split(b'\0') if p}
assert paths-{M}==entries.keys()
delta=source['delta_files']
delta_paths={e['path'] for e in delta}
assert len(delta_paths)==len(delta)==source['new_or_changed_files_directly_hashed']
changed={p.decode('utf-8') for p in git(ROOT,'diff','--name-only','-z',BASE,commit).split(b'\0') if p}
assert changed==delta_paths|{M}
old=json.loads(git(ROOT,'show',BASE+':'+M))
old_entries={e['path']:e for e in old['files']}
assert sha256(git(ROOT,'show',BASE+':'+M)).hexdigest()==previous['manifest_sha256']=='36765b646be480a826c2f41ca7498e3bc6823032503a7afed977d02a4983ccfd'
unchanged=old_entries.keys()-delta_paths
assert len(unchanged)==source['unchanged_manifest_entries_exactly_inherited']
assert all(entries[p]==old_entries[p] for p in unchanged)
assert manifest['science_version']==old['science_version']=='0.5.0'
assert manifest['science_baseline_commit']==old['science_baseline_commit']
cache={}

def identity(name):
    if name not in cache:
        path=RESTORE/name
        cache[name]=dict(path=name,bytes=path.stat().st_size,sha256=sha256(path.read_bytes()).hexdigest())
    return cache[name]

for item in delta:assert identity(item['path'])==item==entries[item['path']]
assert len(source['protocol_checks'])==1
for check in source['protocol_checks']:
    assert identity(check['protocol'])['sha256']==check['protocol_sha256']==FROZEN['protocol_sha256']
    protocol=read(RESTORE/check['protocol'])
    assert len(protocol['bindings'])==check['bindings_checked']==FROZEN['binding_count']
    assert all(identity(p)['sha256']==pin for p,pin in protocol['bindings'].items())
    assert protocol['prepared'] and not protocol['authorized'] and not protocol['executed']
    assert not (RESTORE/protocol['output_directory']).exists()
    assert not (RESTORE/REL/(check['phase']+'_launch.json')).exists()
assert all(identity(p)['sha256']==pin for p,pin in source['peer_reviews'].items())
receipt=dict(status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),published_commit=commit,
    previous_delivery_commit=BASE,branch='main',origin='https://github.com/dudaxing/Compliant-TO-TMC.git',remote_main_confirmed_equal=True,
    restore_object_transport='Local Git fetch of same actually published commit after remote-main confirmation; origin unchanged',
    source_and_restore_clean=True,restore_root=str(RESTORE),manifest_sha256=source['manifest_sha256'],ordinary_manifest_files=len(entries),
    ordinary_manifest_bytes=source['ordinary_manifest_bytes'],new_or_changed_files_restored_and_hashed=len(delta),unchanged_manifest_entries_inherited=len(unchanged),
    inherited_restoration_receipt=source['inherited_restoration_receipt'],new_full_source_or_restore_scan=False,
    protocol_checks=source['protocol_checks'],peer_reviews=source['peer_reviews'],M_SUPPORT1_authorized=False,M_SUPPORT1_executed=False,
    NPZ_decodes_or_support_or_render_in_delivery_restore=0,original_science_and_qualification_unchanged=True,whole_HF5_complete=False)
with OUT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt,ensure_ascii=False))
