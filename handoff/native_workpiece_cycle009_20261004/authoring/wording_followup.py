"""Clarify selected comparison states, preserving the seven historical bodies."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).parent
HANDOFF=ROOT/'handoff/native_workpiece_cycle009_20261004'
path=HANDOFF/'document_preservation.json'
record=json.loads(path.read_text(encoding='utf-8'))
changes=[]
for item in record['fronts']:
    front=ROOT/item['path']
    before=front.read_bytes()
    prefix=before[:item['prefix_bytes']]
    old='前三保存态'.encode();new='三份对照保存态（007初态、008峰态、007回零）'.encode()
    assert prefix.count(old)==1
    prefix=prefix.replace(old,new)
    after=prefix+before[item['prefix_bytes']:]
    front.write_bytes(after)
    changes.append(dict(path=item['path'],before_sha256=sha256(before).hexdigest(),after_sha256=sha256(after).hexdigest()))
    item['prefix_bytes']=len(prefix)
    item['current_sha256']=sha256(after).hexdigest()
with path.open('w',encoding='utf-8',newline='\n') as stream:
    json.dump(record,stream,indent=2,ensure_ascii=False);stream.write('\n')
shutil.copyfile(AUTHOR/'delivery_readonly_review.json',HANDOFF/'delivery_readonly_review.json')
shutil.copyfile(Path(__file__),HANDOFF/'authoring'/Path(__file__).name)
note=dict(status='clarified',reason='Independent reviewer noticed ambiguous first-three phrasing; name the actual selected comparison states.',
    changed_fronts=changes,old_bodies_preserved=True,report_changed=False,new_numerical_calls=0,
    archived_diff_whitespace='git diff --cached --check reports context markers in byte-preserved *.diff artifacts; source/docs check excluding archived diffs passed.',
    cost002_source_line_endings='Cost source has CRLF versus old LF; inverse is exact after newline normalization. Author-time raw-exact shorthand is clarified by cost002_visual_review; numerical expressions unchanged.')
with (HANDOFF/'delivery_wording_followup.json').open('x',encoding='utf-8') as stream:
    json.dump(note,stream,indent=2,ensure_ascii=False);stream.write('\n')
print(json.dumps(dict(status='clarified',fronts=len(changes),new_numerical_calls=0)))
