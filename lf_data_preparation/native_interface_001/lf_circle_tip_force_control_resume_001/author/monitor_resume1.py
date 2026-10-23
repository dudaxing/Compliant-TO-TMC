"""Read only ordinary new progress; never decode scientific payload or media."""
import json
from pathlib import Path
import time
B=Path('D:/hfrs1_001')
def read(name):
    p=B/name
    return json.loads(p.read_bytes()) if p.exists() else None
t=read('top_start.json');o=read('outer_start.json');d=read('run_001/display_start.json')
now=time.monotonic()
row=dict(stage='L-CTIPFRESUME1',observed_monotonic=now,
    elapsed_top=None if t is None else now-t['start_monotonic'],
    elapsed_helper=None if o is None else now-o['start_monotonic'],
    display=d,QA_seconds_remaining=None if d is None else d['root_QA_before_monotonic']-now,
    helper_receipt=read('run_001/helper_receipt.json'),execution_receipt=read('execution_receipt.json'),
    installation=read('installation_receipt.json'),seal=read('seal_receipt.json'))
for name in ('run_001/pytest.log','run_001/viewer.log','outer.log'):
    p=B/name
    row[name]=p.read_text(encoding='utf-8',errors='replace').splitlines()[-4:] if p.exists() else []
print(json.dumps(row,ensure_ascii=False))
