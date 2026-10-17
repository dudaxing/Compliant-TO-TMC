"""Record four already completed image inspections, without reopening media."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/lf_circle_step_002'
STAGE = ROOT/REL
receipt = json.loads((STAGE/'run_001/execution_receipt.json').read_bytes())
assert receipt['status']=='pass'
files = []
for name in ('view/comparison.png','view/distances_forces.png','view/peak_fields.png','convergence/convergence.png'):
    rel = REL+'/run_001/'+name
    seal = receipt['outputs'][rel]
    assert (ROOT/rel).stat().st_size==seal['bytes']
    files.append(dict(path=rel,producer_seal=seal,pixel_inspections=1))
record = dict(card='L-CSTEP2',status='pass_pixel_inspection_with_minor_annotation',
    recorded_utc=datetime.now(timezone.utc).isoformat(),count=4,files=files,
    observations=[
        'Each of the four new PNGs was viewed once via view_image(original). Previews were resized by the renderer; this was visual QA, not an exhaustive full-resolution pixel audit.',
        'Comparison: x1 lower-half and visually mirrored full mechanism, raster circle, analytic reference and closest/tip witnesses are legible. Peak and last both show child1 at1.15 mm for load_only. The closest pair is beneath the circle; the far-right tip remains separated.',
        'Distance/force plot: both saved states1.00/1.15, unsigned minimum/tip distances and signed lower-body total/material/Hu Fx/Fy are visible. No local normal pressure is inferred.',
        'Peak fields: solid/medium element means and Hu Frobenius norm are legible; reported quadrature extrema and maximum absolute Hu component are different statistics.',
        'Convergence: seven base checks, five accepted line trials, zero rejected trials or failed attempts and no bisections. Accepted residuals and both constraint-bound markers are visible; exact zero is retained by symlog.',
        'Minor existing annotation issue retained: the outside legend overlaps part of the right-panel title. Data and both constraint-bound markers remain visible. No redraw or repeat inspection was performed.',
        'No old media were opened and no extra GIF decode was performed. Positive unsigned distance and nonzero weak resultant do not establish effective clamping pressure.'
    ],recording_read_scope='Ordinary execution receipt and producer seals/stat only; no media open/hash/decode/render, tests or science.')
with (STAGE/'author/pixel_QA.json').open('x',encoding='utf-8',newline='\n') as handle:
    json.dump(record,handle,ensure_ascii=False,indent=2)
    handle.write('\n')
target = STAGE/'author/record_pixel_qa.py'
assert not target.exists()
shutil.copyfile(Path(__file__),target)
print(json.dumps(dict(status=record['status'],count=4)))
