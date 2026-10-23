"""Finite ordinary delivery/link/source checks, not a mechanics test run."""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

A=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
DEST=ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_high_preparation_001'
def read(path): return json.loads(path.read_bytes())
def identity(path):
    raw=path.read_bytes(); return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
state=read(DEST/'author/PREPARATION_STATE.json')
assert state['status']=='preparation_complete_independent_review_PASS'
assert state['high_force_executed'] is False and state['NPZ_payload_opens_hashes_or_decodes']==0
assert state['force_calls']==state['tangent_calls']==state['equilibrium_calls']==state['HP_calls']==state['tests']==0
production=read(DEST/'author/PRODUCTION_IDENTITY.json')['files']
assert len(production)==57
for row in production:
    assert identity(ROOT/row['path'])=={key:row[key] for key in ('bytes','sha256')},row['path']
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('href','src') and value: self.links.append(value)
checked=[]
for name in ('PREPARATION.md','L-CTIPFHIGH1_CARD.md','RECOVERY.md','SOURCE_BINDING.md',
             'COMPARISON_GATES.md','FUNCTION_PLAN.md','inspection.html'):
    path=DEST/name; raw=path.read_text(encoding='utf-8')
    if path.suffix=='.html':
        parser=Links(); parser.feed(raw); links=parser.links
    else:
        links=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',raw)
    for link in links:
        if urlsplit(link).scheme or link.startswith('#'): continue
        target=(path.parent/unquote(link.split('#')[0])).resolve()
        assert target.exists(),(name,link)
        checked.append(dict(document=name,link=link,exists=True))
binding=read(DEST/'SOURCE_BINDING.json')
context=[]
for row in binding['ordinary_files']:
    if row['role']=='reference_probe_result': continue
    target=DEST/'source_context'/Path(row['path']).relative_to('D:/hpr1_001')
    assert identity(target)=={key:row[key] for key in ('bytes','sha256')}
    context.append(target.relative_to(DEST).as_posix())
qa=read(DEST/'author/SCHEMATIC_QA.json')
assert qa['pixel_inspections']==1 and identity(DEST/'control_schematic.png')==qa['image_identity']
assert not any(p.suffix.lower() in ('.npz','.zip') for p in DEST.rglob('*') if p.is_file())
result=dict(stage='L-CTIPFHIGHPREP1',status='PASS',source_PY_unchanged=57,
    context_original_ordinary_files=context,relative_links_checked=checked,
    schematic_byte_identity_matches_original_QA=True,no_scientific_payloads_delivered=True,
    source_payload_reads_or_decodes=0,old_media_pixel_reads=0,new_mechanics_tests_or_calls=0,
    scope='New ordinary preparation delivery only; no archive/NPZ/media decode or HF import.')
target=DEST/'author/PREPUBLICATION_CHECK.json'
assert not target.exists()
target.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(status='PASS',production=57,ordinary_context=len(context),relative_links=len(checked),new_science=0)))
