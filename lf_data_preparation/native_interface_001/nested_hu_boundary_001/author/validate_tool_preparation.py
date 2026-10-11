"""Record reviewed external tool readiness without importing or executing it."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
BASE = 'eb68c00d50b28de89a475c18a0879be4a4482f68'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()
git = lambda *args: subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()

assert git('rev-parse','HEAD') == BASE and not git('status','--porcelain')
protocol = read(ROOT/REL/'protocol.json')
assert sha(ROOT/REL/'protocol.json') == 'f27d201b01efc5c49212a43536e928ba6ac88ba4346ac6949dccdfcac8d94e33'
assert len(protocol['bindings']) == 45
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
assert not (ROOT/protocol['output_directory']).exists()
assert not any((ROOT/REL/name).exists() for name in ('hu_boundary_launch.json','hu_boundary_stdout.log',
    'stop_requested.txt','author/authorization.json','author/direct_human_reply.json'))
review = read(EXT/'tool_static_review.json')
assert review['status'] == 'pass_static_prepared_tools_not_execution'
records = {}
parsed = []
for name,pin in review['frozen_external_sources'].items():
    path = EXT/name
    assert sha(path) == pin
    records[name] = dict(bytes=path.stat().st_size,sha256=pin)
    if path.suffix == '.py':
        ast.parse(path.read_text(encoding='utf-8'))
        parsed.append(name)
assert not any((EXT/name).exists() for name in ('terminal_execution_review.json','physical_results_review.json',
    'visual_review.json','final_delivery_static_review.json','execution_delivery_config.json',
    'execution_delivery_delta_verify.json','publication_receipt.json'))
assert git('rev-parse','HEAD') == BASE and not git('status','--porcelain')
receipt = dict(status='reviewed_external_tools_prepared_not_authorized_not_executed',
    recorded_UTC=datetime.now(timezone.utc).isoformat(),source_main_commit=BASE,formal_repository_unchanged=True,
    protocol_sha256=sha(ROOT/REL/'protocol.json'),original_bindings_checked=45,
    static_tool_review_sha256=sha(EXT/'tool_static_review.json'),external_sources=records,AST_parsed_only=parsed,
    authorized=False,executed=False,actual_launch_and_outputs_absent=True,actual_terminal_reviews_absent=True,
    actions=dict(candidate_imports=0,NPZ_decodes=0,API_runs=0,new_scientific_fsum_force_render_calls=0,
        authorization_writes=0,formal_repository_edits_or_commit_pushes=0),
    next_required_input='Direct human M-BOUND1 approval; automatic goal continuation is not numerical authorization.',
    whole_HF5_complete=False)
with (EXT/'preparation_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=receipt['status'],AST_only=len(parsed),original_bindings_checked=45)))
