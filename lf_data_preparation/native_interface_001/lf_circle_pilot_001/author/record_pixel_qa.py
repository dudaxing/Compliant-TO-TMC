"""Record the four completed root inspections; no image read or rehash."""
from datetime import datetime, timezone
import json
from pathlib import Path
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/lf_circle_pilot_001'
STAGE=ROOT/REL
receipt=json.loads((STAGE/'run_001/execution_receipt.json').read_bytes())
assert receipt['status']=='pass'
names=('view/comparison.png','view/distances_forces.png','view/peak_fields.png','convergence/convergence.png')
files=[]
for name in names:
    path=REL+'/run_001/'+name; seal=receipt['outputs'][path]
    assert (ROOT/path).stat().st_size==seal['bytes']
    files.append(dict(path=path,inspection_count=1,original_window_identity=seal))
value=dict(card='L-CPILOT1',status='pass_pixel_inspection',inspection_count=4,files=files,
    inspected_utc=datetime.now(timezone.utc).isoformat(),
    scope='Each of four new PNGs viewed once with view_image(detail=original); tool display resized all four to width2048. No full-resolution pixel-by-pixel claim, redraw, extra GIF decode or media hash by recorder.',
    observations=[
        'Actual x1 full/mirrored and lower-half local geometry are legible. Raster edges and analytic reference are distinct; mechanism remains visibly separated below the circle. Maximum and last panels both identify state2/d0.5, correctly identical for this load-only pilot.',
        'Input R/q_out and signed total/material/Hu global Fy curves show three original accepted samples. Distance/Fx/Fy figure separates boundary minimum from the more distant reference tip; no square-face ray or circular local-normal-force claim.',
        'Peak field panels separate solid mean J/Green principal strain from free-medium mean J/Hu Frobenius; body is separately colored. Color means/norms and summary integration-point extrema are different declared observations.',
        'Convergence figure displays the exact zero origin, two nonzero seven-check groups, original1e-9 gate,15 base checks,12 accepted line-search trials,0 rejects/failed attempts/bisections; accepted constraints lie below saved bounds. Labels and legends are readable at displayed size.'
    ],science_qualification_unchanged=True)
with (STAGE/'author/pixel_QA.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print('Four completed PNG inspections recorded; no media opened by this recorder.')
