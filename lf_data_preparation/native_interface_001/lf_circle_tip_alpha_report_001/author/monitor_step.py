"""Read this card's ordinary terminal receipts only."""
import json
from pathlib import Path
stage = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001')
record = {}
for key, name in [('outer','step_launch.json'),('helper','run_001/execution_receipt.json')]:
    path = stage/name
    if path.is_file():
        data = json.loads(path.read_bytes())
        record[key] = {k:data[k] for k in ('status','phase','counts','elapsed_seconds','cleanup_verified') if k in data}
print(json.dumps(record, ensure_ascii=False))
