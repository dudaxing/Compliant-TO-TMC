"""Freeze the exact ordinary preparation delta before final independent review."""
from hashlib import sha256
from pathlib import Path
import ast
import json
import re
import subprocess
from urllib.parse import unquote

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '9e2e37cce7f0441af042337d1c26c50ae660acc0'
REL = 'functional_views/native_alpha_partial_20261011/complete_001'
STAGE = ROOT/REL
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
protocol,prep = read(STAGE/'protocol.json'),read(STAGE/'author/preparation_receipt.json')
assert protocol['card'] == 'M-AVIEW1' and not protocol['authorized'] and not protocol['executed']
assert prep['protocol_sha256'] == sha(STAGE/'protocol.json')
assert not (STAGE/'run_001').exists() and not (STAGE/'author/authorization.json').exists()
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
for name in ('deliver_view_preparation.py','prepare_view_candidate.py'):
    ast.parse((EXT/name).read_text(encoding='utf-8'))
review = read(EXT/'tool_static_review.json')
assert review['status'].startswith('pass') and not review['authorized'] and not review['executed']
assert all(sha(EXT/name) == pin for name,pin in review['reviewed_external_SHA256'].items())
for name in ('deliver_view_preparation.py','tool_source_notes.md','tool_source_notes.json',
        'tool_static_review.json','TOOL_STATIC_REVIEW.md','configure_view_delivery.py'):
    target = STAGE/'author'/name
    assert not target.exists()
    target.write_bytes((EXT/name).read_bytes())
fronts = [item['path'] for item in prep['front_history']]
links = []
for path in STAGE.rglob('*.md'):
    text = path.read_text(encoding='utf-8')
    for ref in re.findall(r'\]\(([^)]+)\)',text):
        ref = ref.strip('<>')
        if '://' in ref or ref.startswith('#'):
            continue
        target = (path.parent/unquote(ref.split('#',1)[0])).resolve()
        assert target.is_relative_to(ROOT) and target.is_file(), (path,ref)
        links.append(dict(document=path.relative_to(ROOT).as_posix(),reference=ref))
for item in prep['front_history']:
    current = (ROOT/item['path']).read_bytes()
    old = subprocess.check_output(['git','show',BASE+':'+item['path']],cwd=ROOT)
    assert current[item['history_start_byte']:item['history_end_byte_exclusive']] == old
    assert sha256(old).hexdigest() == item['old_sha256'] and sha(ROOT/item['path']) == item['new_sha256']
config_rel,final_rel = REL+'/author/preparation_delivery_config.json',REL+'/author/final_delivery_static_review.json'
assert not (ROOT/config_rel).exists() and not (ROOT/final_rel).exists()
stage_files = {path.relative_to(ROOT).as_posix() for path in STAGE.rglob('*') if path.is_file()}
previous_rel = REL+'/author/M_ALPHA1_execution_publication_receipt.json'
config = dict(schema_version='saved-alpha-view-preparation-delivery-1.0',card='M-AVIEW1',
    source_baseline_commit=BASE,protocol_sha256=sha(STAGE/'protocol.json'),
    binding_pins=protocol['bindings'],front_history=prep['front_history'],
    previous_publication_receipt=dict(path=previous_rel,sha256=sha(ROOT/previous_rel)),
    allowed_delta_paths=sorted(stage_files|set(fronts)|{config_rel,final_rel}),
    final_review_path=final_rel,
    final_review_scope='All frozen delta bytes plus all protocol binding identities; sole future file is this final review, never self-hashed.',
    local_markdown_links_checked=links,
    prepared=True,authorized=False,executed=False,whole_HF5_complete=False)
raw = (json.dumps(config,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
for path in (ROOT/config_rel,EXT/'preparation_delivery_config.json'):
    with path.open('xb') as stream:
        stream.write(raw)
print(json.dumps(dict(status='ordinary_preparation_delivery_config_frozen',
    config_sha256=sha(ROOT/config_rel),allowed_delta_files=len(config['allowed_delta_paths']),
    links_checked=len(links),binding_count=len(protocol['bindings']),authorized=False,executed=False)))
