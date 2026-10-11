"""Record direct human M-SUPPORT1 approval; no scientific candidate call."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/nested_material_support_001'
SOURCE = Path('D:/hf-native-workpiece-api-author-20261009/MSUPPORT1_source_prepare_001/publication_receipt.json')
BASE = 'fa872739247a2a5d96043b1c05d28e9f08a77b88'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
assert subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True) == ''
protocol = json.loads((STAGE/'protocol.json').read_text(encoding='utf-8'))
assert not (ROOT/protocol['output_directory']).exists() and not (STAGE/'support_launch.json').exists()
assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == pin for name,pin in protocol['bindings'].items())
prior = json.loads(SOURCE.read_text(encoding='utf-8'))
assert prior['status'] == 'published_and_incrementally_restored_pass' and prior['published_commit'] == BASE
assert not prior['M_SUPPORT1_executed'] and not prior['M_SUPPORT1_authorized']
receipt = dict(status='direct_human_authorization_recorded_before_one_execution',recorded_utc=datetime.now(timezone.utc).isoformat(),
    approved_source_commit=BASE,questionItemId='["request_user_input_async","call_c72f36f1eb354ad29b98976afc85ee1b",0]',
    direct_human_answer='批准按 M-SUPPORT1 卡执行',card='lf_data_preparation/native_interface_001/nested_material_support_001/M-SUPPORT1_CARD.md',
    card_sha256=hashlib.sha256((STAGE/'M-SUPPORT1_CARD.md').read_bytes()).hexdigest(),
    protocol_sha256=hashlib.sha256((STAGE/'protocol.json').read_bytes()).hexdigest(),authorized=True,executed_at_record=False,
    resource=dict(helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=8589934592),
    scope='Two original loading states6/13; three existing NPZ/eight fields; two support APIs and original C-order material assembly replays, explicit local-L1 regrouping check; five tables and two reference/support figures.',
    stop_rule='Once, first error, no retry/repair-rerun/extension/force; no new kernel/tangent/HP/equilibrium or pressure/grip qualification',
    historical_protocol_false_flags='Frozen preparation history; direct authorization is this distinct record.')
with (STAGE/'author/authorization.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
assert not (STAGE/'author/M_SUPPORT1_source_publication_receipt.json').exists()
(STAGE/'author/M_SUPPORT1_source_publication_receipt.json').write_bytes(SOURCE.read_bytes())
print(json.dumps(dict(status=receipt['status'],approved_source_commit=BASE,bindings_checked=len(protocol['bindings'])),ensure_ascii=False))
