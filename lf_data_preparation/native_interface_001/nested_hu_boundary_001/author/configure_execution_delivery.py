"""Future M-BOUND1 closure configuration; requires actual approved run/reviews.

This source preparation grants no approval and performs no candidate run.
"""
from pathlib import Path
from hashlib import sha256
import ast
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
BASE = 'eb68c00d50b28de89a475c18a0879be4a4482f68'
STAGE = ROOT/REL
SOURCE_RECEIPT = EXT.parent/'MBOUND1_source_prepare_001/publication_receipt.json'
SOURCE_RECEIPT_SHA = 'c8b2c2087e445c51abbf82af7cae1a2ee382f4c797ab6a81e3e93a6d717093fb'
PROTOCOL_SHA = 'f27d201b01efc5c49212a43536e928ba6ac88ba4346ac6949dccdfcac8d94e33'
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

assert not (STAGE/'author/execution_delivery_config.json').exists()
assert not (EXT/'execution_delivery_config.json').exists()
protocol = read(STAGE/'protocol.json')
assert sha(STAGE/'protocol.json') == PROTOCOL_SHA
assert protocol['prepared'] and not protocol['authorized'] and not protocol['executed']
assert protocol['schema_version'] == 'saved-Q1-Hu-boundary-card-1.0' and len(protocol['bindings']) == 45
assert set(protocol['phases']) == {'hu_boundary'} and len(protocol['expected_output_files']) == 10

# These records must come from the later human-approved actual run; none is made here.
auth = read(STAGE/'author/authorization.json')
evidence = read(STAGE/'author/direct_human_reply.json')
assert evidence['authorization_from_direct_human_reply'] is True and evidence['card'] == 'M-BOUND1'
assert evidence['approved_source_commit'] == auth['approved_source_commit'] == BASE and auth['authorized'] is True
assert auth['human_evidence_sha256'] == sha(STAGE/'author/direct_human_reply.json')
assert auth['direct_human_answer'] == evidence['direct_human_answer'] and evidence['direct_human_answer'].strip()
assert evidence['reply_context'].strip()
helper = read(STAGE/'run_001/execution_receipt.json')
outer = read(STAGE/'hu_boundary_launch.json')
assert helper['status'] == outer['status'] == 'pass'
assert helper['protocol_sha256'] == outer['protocol_sha256'] == PROTOCOL_SHA
assert helper['calls'] == protocol['expected_calls'] and helper['counts'] == protocol['expected_counts']
assert outer['invocations'] == 1 and outer['exit_code'] == 0 and outer['stop_reason'] is None
assert helper['all_bindings_unchanged'] and outer['all_bindings_unchanged']
assert not (STAGE/'stop_requested.txt').exists()
assert set(path.name for path in (ROOT/protocol['output_directory']).iterdir()) == set(protocol['expected_output_files'])
assert set(helper['output_SHA256']) == set(protocol['expected_output_files'])-{'execution_receipt.json'}
assert all(sha(ROOT/protocol['output_directory']/name) == pin for name, pin in helper['output_SHA256'].items())

review = read(EXT/'final_delivery_static_review.json')
assert review['status'] == 'pass_actual_results_documentation_and_incremental_delivery_static_review'
for name, pin in review['reviewed_external_SHA256'].items():
    assert sha(EXT/name) == pin, (name, 'reviewed external file')
for name, pin in review['reviewed_repository_SHA256'].items():
    assert sha(ROOT/name) == pin, (name, 'reviewed repository file')
for name in ('terminal_execution_review.json', 'physical_results_review.json', 'visual_review.json'):
    status = read(STAGE/'author'/name)['status']
    assert (status == 'completed_actual_saved_result_interpretation_no_new_scientific_gate'
        if name == 'physical_results_review.json' else status.startswith('pass'))
doc = read(STAGE/'author/documentation_receipt.json')
assert doc['status'] == 'pass_actual_execution_documentation_closed' and doc['execution_closed']
assert doc['source_commit'] == BASE and sha(STAGE/'RESULTS.md') == doc['result_sha256']
assert sha(STAGE/'NEXT_STEP_REVIEW.md') == doc['next_step_sha256']
assert doc['actions']['new_candidate_runs'] == doc['actions']['new_NPZ_decodes'] == doc['actions']['new_projection_fsum_integral_render'] == 0

assert sha(SOURCE_RECEIPT) == SOURCE_RECEIPT_SHA
source = read(SOURCE_RECEIPT)
assert source['status'] == 'published_and_incrementally_restored_pass'
assert source['published_commit'] == BASE and source['source_and_restore_clean'] and source['remote_main_confirmed_equal']
assert source['authorized'] is False and source['executed'] is False
source_archive = STAGE/'author/M_BOUND1_source_publication_receipt.json'
assert source_archive.exists() and source_archive.read_bytes() == SOURCE_RECEIPT.read_bytes()

for name in ('final_delivery_static_review.json', 'deliver_execution.py', 'configure_execution_delivery.py'):
    assert not (STAGE/'author'/name).exists()
    if name.endswith('.py'):
        ast.parse((EXT/name).read_text(encoding='utf-8'))
    (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
peers = {f'{REL}/author/{name}': sha(STAGE/'author'/name) for name in (
    'terminal_execution_review.json', 'physical_results_review.json', 'visual_review.json', 'final_delivery_static_review.json')}
records = {f'{REL}/{name}': sha(STAGE/name) for name in (
    'author/direct_human_reply.json', 'author/authorization.json', 'author/documentation_receipt.json', 'author/M_BOUND1_source_publication_receipt.json',
    'author/deliver_execution.py', 'author/configure_execution_delivery.py', 'RESULTS.md', 'NEXT_STEP_REVIEW.md',
    'author/record_authorization.py', 'author/review_terminal.py', 'author/close_docs.py', 'author/PHYSICAL_REVIEW_CHECKLIST.md',
    'run_001/execution_receipt.json', 'hu_boundary_launch.json', 'hu_boundary_stdout.log')}
config = dict(protocol_sha256=PROTOCOL_SHA, binding_count=45,
    expected_calls=protocol['expected_calls'], expected_counts=protocol['expected_counts'],
    output_files=protocol['expected_output_files'], peer_reviews=peers, record_pins=records)
raw = (json.dumps(config, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
with (EXT/'execution_delivery_config.json').open('xb') as stream:
    stream.write(raw)
(STAGE/'author/execution_delivery_config.json').write_bytes(raw)
assert all(sha(ROOT/name) == pin for name, pin in protocol['bindings'].items())
print(json.dumps(dict(status='actual_execution_delivery_configured', protocol_sha256=PROTOCOL_SHA, bindings=45)))
