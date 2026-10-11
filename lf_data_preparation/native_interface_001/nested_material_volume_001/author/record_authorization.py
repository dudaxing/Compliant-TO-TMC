"""Record direct M-VOLUME1 human approval before its single numerical run."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/nested_material_volume_001'
STAGE=ROOT/REL
BASE='7ea78ce19ba066dfce8a03892395d5604707dda6'
SOURCE=Path('D:/hf-native-workpiece-api-author-20261009/MVOLUME1_source_prepare_001/publication_receipt.json')
sha=lambda p:sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
git=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT).decode().strip()
assert git('rev-parse','HEAD') == BASE and not git('status','--porcelain')
assert git('branch','--show-current') == 'main' and git('remote','get-url','origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
p=read(STAGE/'protocol.json')
assert sha(STAGE/'protocol.json') == '44b8ea0df17cfe17d2a36f2823a37e29a7163326f8254e8967518a6ba6c3a51b'
assert len(p['bindings']) == 31 and all(sha(ROOT/n) == pin for n,pin in p['bindings'].items())
assert not (ROOT/p['output_directory']).exists() and not (STAGE/'volume_launch.json').exists()
assert not (STAGE/'stop_requested.txt').exists()
prior=read(SOURCE)
assert prior['status'] == 'published_and_incrementally_restored_pass' and prior['published_commit'] == BASE
assert not prior['authorized'] and not prior['executed'] and prior['source_and_restore_clean']
receipt=dict(status='direct_human_authorization_recorded_before_one_execution',recorded_utc=datetime.now(timezone.utc).isoformat(),
    approved_source_commit=BASE,questionItemId='["request_user_input_async","call_KASkj7Jp2l0cYjM0Y1yWxFmy",0]',
    direct_human_answer='批准按 M-VOLUME1 卡执行',card=p['card'],card_sha256=sha(ROOT/p['card']),
    protocol_sha256=sha(STAGE/'protocol.json'),authorized=True,executed_at_record=False,
    resource=dict(helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=8589934592),
    scope='Original loading states6/13, cells10406/10407; three existing NPZ/nine fields, two NumPy APIs, 36/12/4 table rows and two PNGs; original DD weak force and saved top trace retained, same-q-term8eps L1 regrouping only, cross-expression differences descriptive.',
    stop_rule='Once, first error, no retry/repair-rerun/extension/force; no new kernel/tangent/HP/equilibrium or pressure/grip qualification',
    historical_protocol_false_flags='Frozen preparation history; approval is this distinct pre-execution record.')
with (STAGE/'author/authorization.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
assert not (STAGE/'author/M_VOLUME1_source_publication_receipt.json').exists()
(STAGE/'author/M_VOLUME1_source_publication_receipt.json').write_bytes(SOURCE.read_bytes())
print(json.dumps(dict(status=receipt['status'],approved_source_commit=BASE,bindings_checked=31),ensure_ascii=False))
