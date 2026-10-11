"""Freeze ordinary source/documentation delivery metadata, without HF work."""
from pathlib import Path
from hashlib import sha256
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/regularization_sensitivity_001'
STAGE = ROOT/REL
BASE = '5af8b5eb3d6780065075b8a331b774d8dad57d67'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())

assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
assert not (EXT/'preparation_delivery_config.json').exists()
protocol = read(STAGE/'protocol.json')
assert not protocol['authorized'] and not protocol['executed']
assert not (STAGE/'run_001').exists() and not (STAGE/'author/authorization.json').exists()
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
doc = read(STAGE/'author/documentation_receipt.json')
assert doc['status'] == 'pass_preparation_documentation_no_execution'
assert doc['report_sha256'] == sha(STAGE/'PREPARATION_RESULTS.md')
assert doc['README_sha256'] == sha(STAGE/'README.md')
assert all(sha(STAGE/'author'/name) == pin for name,pin in doc['peer_reports'].items())
for name in ('delivery_tool_static_review.json','delivery_tool_static_review.md',
             'deliver_preparation.py','configure_preparation_delivery.py'):
    source, target = EXT/name, STAGE/'author'/name
    assert source.is_file() and not target.exists()
    if name.endswith('.py'):
        ast.parse(source.read_text(encoding='utf-8'))
    target.write_bytes(source.read_bytes())
reviews = {REL+'/author/'+name:sha(STAGE/'author'/name) for name in (
    'input_scope_static_review.json','physics_static_review.json','delivery_tool_static_review.json')}
assert all(read(ROOT/name)['status'].startswith('pass') for name in reviews)
records = {REL+'/author/'+name:sha(STAGE/'author'/name) for name in (
    'preparation_receipt.json','documentation_receipt.json','M_BOUND1_execution_publication_receipt.json',
    'worker_author_receipt.json','prepare_candidate.py','close_preparation_docs.py',
    'deliver_preparation.py','configure_preparation_delivery.py')}
fronts = ['docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md']
for entry in doc['front_history']:
    current = (ROOT/entry['path']).read_bytes()
    original = subprocess.check_output(['git','show',BASE+':'+entry['path']],cwd=ROOT)
    assert current[entry['history_start_byte']:entry['history_end_byte_exclusive']] == original
    assert sha256(original).hexdigest() == entry['old_sha256'] and sha(ROOT/entry['path']) == entry['new_sha256']
stage_paths = {path.relative_to(ROOT).as_posix() for path in STAGE.rglob('*') if path.is_file()}
config_rel = REL+'/author/preparation_delivery_config.json'
final_review_rel = REL+'/author/final_delivery_static_review.json'
assert not (ROOT/config_rel).exists() and not (ROOT/final_review_rel).exists()
config = dict(schema_version='same-task-alpha-preparation-delivery-1.0', source_baseline_commit=BASE,
    protocol_sha256=sha(STAGE/'protocol.json'),binding_count=len(protocol['bindings']),
    allowed_delta_paths=sorted(stage_paths|set(fronts)|{config_rel,final_review_rel}),
    review_pins=reviews,record_pins=records,
    documentation_files=fronts+[REL+'/README.md',REL+'/PREPARATION_RESULTS.md',REL+'/M-ALPHA1_CARD.md'],
    final_review_path=final_review_rel,
    final_review_scope='Independent final review reads this frozen config and all existing delta bytes; its own new report is the sole planned future file, hashed with the actual staged delta.',
    prepared=True,authorized=False,executed=False,whole_HF5_complete=False)
raw = (json.dumps(config,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
for path in (EXT/'preparation_delivery_config.json',ROOT/config_rel):
    with path.open('xb') as stream:
        stream.write(raw)
print(json.dumps(dict(status='delivery_config_prepared_not_numerical',allowed_delta_files=len(config['allowed_delta_paths']),config_sha256=sha(ROOT/config_rel))))
