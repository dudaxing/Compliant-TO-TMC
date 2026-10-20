"""Copy ordinary author records and check new documentation links; no payload I/O."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_001'
names=('publish_step.py','finalize_records.py')
for name in names:
    target=STAGE/'author'/name
    assert not target.exists()
    target.write_bytes((AUTHOR/name).read_bytes())
ordinary={'.py','.json','.jsonl','.ndjson','.md','.log','.txt'}
checks={}
for path in STAGE.rglob('*'):
    if path.is_file() and path.suffix in ordinary:
        raw=path.read_bytes()
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),path
        if path.suffix=='.py':ast.parse(raw)
checks['new_ordinary_syntax_and_whitespace']=True
checked=[]
for name in ('RESULTS.md','NEXT_STEPS.md','run_001/REVIEW.md'):
    path=STAGE/name
    if name=='run_001/REVIEW.md' and not path.is_file():continue
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        if link.startswith('<') and link.endswith('>'):
            link=link[1:-1]
        if '://' in link or link.startswith('#'):continue
        target=(path.parent/link.split('#')[0]).resolve()
        target.relative_to(ROOT)
        assert target.exists(),(name,link)
        checked.append(dict(document=name,link=link))
checks['new_document_links_exist']=True
history=json.loads((STAGE/'author/front_history.json').read_bytes())
for row in history['files']:
    raw=(ROOT/row['path']).read_bytes();old=raw[row['prefix_bytes']:]
    assert len(old)==row['old_bytes'] and sha256(old).hexdigest()==row['old_sha256']
    assert raw.count(old)==1
checks['seven_original_front_suffixes_preserved_once']=True
report=dict(status='pass_ordinary_final_documents',checks=checks,checked_links=checked,
            science_or_media_payload_reads=0,scientific_tests_or_reexecution=0)
(STAGE/'author/FINAL_DOC_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(status=report['status'],links=len(checked),fronts=len(history['files']))))
