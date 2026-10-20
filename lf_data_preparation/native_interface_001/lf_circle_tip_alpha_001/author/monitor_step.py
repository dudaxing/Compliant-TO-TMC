"""Read only this experiment's ordinary progress records, without payload I/O."""
import json
from pathlib import Path
stage=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001')
record={}
for key,name in [('outer','step_launch.json'),('helper','run_001/execution_receipt.json')]:
    path=stage/name
    if path.is_file():
        data=json.loads(path.read_bytes())
        record[key]={k:data[k] for k in ('status','phase','accepted_states','elapsed_seconds','cleanup_verified','error') if k in data}
progress=stage/'run_001/accepted_progress.jsonl'
if progress.is_file():
    rows=[json.loads(line) for line in progress.read_text(encoding='utf-8').splitlines() if line.strip()]
    record['progress']=dict(accepted_states=len(rows),last=rows[-1] if rows else None)
print(json.dumps(record,ensure_ascii=False))
