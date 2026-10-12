"""Freeze the ordinary publication delta after the closed M-ALINK1 run."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/alpha_link_001'
HERE = Path(__file__).resolve().parent
STAGE = ROOT/REL
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()
copies = ('deliver_execution.py','EXECUTION_DELIVERY_TOOL_NOTES.md',
    'delivery_tool_author_receipt.json','prepare_execution_delivery.py')
assert sha(HERE/'deliver_execution.py') == '207c62d865a9bef7c8773a7805fb8ccf3234e0ee102dde010a82c9adf4581889'
for name in copies:
    with (STAGE/'author'/name).open('xb') as output:
        output.write((HERE/name).read_bytes())
manifest = read(ROOT/'handoff/repository_manifest.json')
old = {row['path'] for row in manifest['files']}
assert manifest['science_version'] == '0.5.0'
config_name = REL+'/author/execution_delivery_config.json'
final_name = REL+'/author/execution_delivery_final_review.json'
new = {path.relative_to(ROOT).as_posix() for path in STAGE.rglob('*') if path.is_file()}-old
allowed = new | {config_name,final_name,'docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'}
assert all(Path(name).suffix.lower() in {'.json','.md','.py','.log'} for name in allowed)
docs = read(STAGE/'author/execution_documentation_receipt.json')
config = dict(source_commit=docs['source_commit'],
    protocol_sha256=sha(STAGE/'protocol.json'),allowed_delta_paths=sorted(allowed),
    front_history=docs['front_history'],closed_output_SHA256=docs['closed_output_SHA256'],
    review_pins={REL+'/author/'+name:sha(STAGE/'author'/name) for name in
        ('execution_terminal_scope_review.json','execution_input_identity_review.json',
         'execution_documentation_receipt.json','deliver_execution.py','delivery_tool_author_receipt.json')},
    final_review_path=final_name,
    delta_scope='Closed actual metadata and documentation only; old science/media identities inherited from the sole run and previous manifest')
with (ROOT/config_name).open('x',encoding='utf-8',newline='\n') as output:
    output.write(json.dumps(config,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status='ordinary_execution_delivery_config_frozen',
    allowed_delta_files=len(allowed),publication_source_sha256=sha(STAGE/'author/deliver_execution.py'),
    config_sha256=sha(ROOT/config_name),new_API_mechanics_or_media_reads=0)))
