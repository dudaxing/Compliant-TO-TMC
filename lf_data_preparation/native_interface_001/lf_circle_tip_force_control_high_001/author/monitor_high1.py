"""Observe only new ordinary progress; never open scientific caches or media."""
import json
from pathlib import Path
import time

BASE=Path('D:/hfh1_001')
def read_if(name):
    path=BASE/name
    return json.loads(path.read_bytes()) if path.exists() else None
top=read_if('top_start.json'); helper=read_if('helper_start.json')
row=dict(stage='L-CTIPFHIGH1',observed_monotonic=time.monotonic(),
    elapsed_top_seconds=None if top is None else time.monotonic()-top['start_monotonic'],
    elapsed_helper_seconds=None if helper is None else time.monotonic()-helper['start_monotonic'],
    science_progress=read_if('run_001/science_progress.json'),
    display_start=read_if('run_001/display_start.json'),
    helper_receipt=read_if('helper_receipt.json'),seal_receipt=read_if('seal_receipt.json'))
path=BASE/'helper.log'
row['helper_log_tail']=path.read_text(encoding='utf-8',errors='replace').splitlines()[-3:] if path.exists() else []
print(json.dumps(row,ensure_ascii=False))
