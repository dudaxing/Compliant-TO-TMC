"""Record completed human-facing pixel inspection; no media decode or hashing."""
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/lf_batch_forward_001'
e = json.loads((STAGE/'run_001/execution_receipt.json').read_bytes())
assert e['status'] == 'pass'
notes = [
    'Two designs, actual x1 deformations with visual mirror, fixed workpiece and near-tip distances visible; peak and last correctly coincide at short-path 0.50 mm. Force axes and scope legend readable.',
    'Two distance and signed body-Fx rows readable; finite distances remain positive and material/Hu/total curves are separately labelled.',
    'Two solid Green-principal, free-medium mean J and Hu fields readable with separate colour bars; these are saved observations, not pressure maps.',
    'Fine chronological Newton checks, accepted residual/balance and constraint panels readable; exact zero shown and tolerance/bounds labelled; 3 states, 15 checks, no rejected trials or failed attempts.',
    'Wave chronological Newton checks, accepted residual/balance and constraint panels readable; exact zero shown and tolerance/bounds labelled; 3 states, 15 checks, no rejected trials or failed attempts.',
]
rows = []
for path, note in zip(e['display']['PNG_files'], notes):
    seal = e['outputs'][path]
    assert (ROOT/path).stat().st_size == seal['bytes']
    rows.append(dict(path=path, inspection_count=1, method='One functions.view_image call per new PNG, inspected by root',
        status='readable', observation=note, original_window_identity=seal))
assert len(rows) == 5
qa = dict(card='L-BFWD1', status='pass_pixel_inspection', inspected_utc=datetime.now(timezone.utc).isoformat(),
    scope='Exactly one root pixel inspection for each of five new PNGs after terminal success; no redraw, extra GIF decoding or scientific recomputation',
    PNGs=rows, GIFs_inspected_again=0, bytes_rehashed_by_this_record=0,
    scientific_qualification_unchanged=True)
with (STAGE/'author/pixel_QA.json').open('x', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('Recorded five completed single inspections; no media read by recorder')
