"""Freeze reviewed ordinary closure records and delivery tools, no scientific run."""
from pathlib import Path
from hashlib import sha256
import ast
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/nested_material_volume_001'
STAGE = ROOT/REL
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
assert not (STAGE/'author/execution_delivery_config.json').exists()
protocol = read(STAGE/'protocol.json')
assert protocol['prepared'] and not protocol['authorized'] and not protocol['executed']
review = read(EXT/'final_delivery_static_review.json')
assert review['status'] == 'pass_actual_results_documentation_and_incremental_delivery_static_review'
for name,pin in review['reviewed_external_files_SHA256'].items():
    assert sha(EXT/name) == pin,(name,'reviewed external file')
for name,pin in review['reviewed_repo_files_SHA256'].items():
    assert sha(ROOT/name) == pin,(name,'reviewed repository file')
for name in ('final_delivery_static_review.json','deliver_execution.py','configure_execution_delivery.py'):
    assert not (STAGE/'author'/name).exists()
    if name.endswith('.py'):
        ast.parse((EXT/name).read_text(encoding='utf-8'))
    (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
peers = {f'{REL}/author/{n}':sha(STAGE/'author'/n) for n in (
    'terminal_execution_review.json','physical_results_review.json','visual_review.json','final_delivery_static_review.json')}
records = {f'{REL}/{n}':sha(STAGE/n) for n in (
    'author/authorization.json','author/documentation_receipt.json','author/M_VOLUME1_source_publication_receipt.json',
    'author/existing_workpiece_function_audit.json','author/deliver_execution.py','author/configure_execution_delivery.py',
    'RESULTS.md','NEXT_STEP_REVIEW.md','run_001/execution_receipt.json',
    'volume_launch.json','volume_stdout.log')}
config = dict(protocol_sha256=sha(STAGE/'protocol.json'),binding_count=len(protocol['bindings']),
    expected_calls=protocol['expected_calls'],expected_counts=protocol['expected_counts'],
    output_files=protocol['expected_output_files'],peer_reviews=peers,record_pins=records)
raw = (json.dumps(config,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
with (EXT/'execution_delivery_config.json').open('xb') as stream:
    stream.write(raw)
(STAGE/'author/execution_delivery_config.json').write_bytes(raw)
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
print(json.dumps(dict(status='actual_execution_delivery_configured',protocol_sha256=config['protocol_sha256'],bindings=config['binding_count'])))
