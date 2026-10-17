"""Record four already completed human-visible image inspections; never reopen media."""
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/lf_circle_step_001'
STAGE = ROOT / REL
receipt = json.loads((STAGE / 'run_001/execution_receipt.json').read_bytes())
assert receipt['status'] == 'pass'
names = ['view/comparison.png', 'view/distances_forces.png', 'view/peak_fields.png', 'convergence/convergence.png']
files = []
for name in names:
    rel = REL + '/run_001/' + name
    seal = receipt['outputs'][rel]
    assert (ROOT / rel).stat().st_size == seal['bytes']
    files.append(dict(path=rel, producer_seal=seal, pixel_inspections=1))
record = dict(card='L-CSTEP1', status='pass_pixel_inspection_with_minor_annotation',
    recorded_utc=datetime.now(timezone.utc).isoformat(), count=4, files=files,
    observations=[
        'Four new PNGs were each viewed once using view_image(original). The renderer resized previews; this is visual QA, not an exhaustive full-resolution pixel audit.',
        'Comparison: actual x1 lower-half and mirrored full structure, fixed circular stair boundary, analytic reference and closest/tip witnesses are legible. Peak and last both identify child1 at 1.00 mm, as expected for load_only.',
        'Distances/forces: two saved states .75 and 1.00 mm, input reaction and q_out, unsigned boundary/tip distances and signed total/material/Hu body forces are visible.',
        'Peak fields: plotted solid/medium element means and Hu Frobenius norm are distinct from the reported quadrature extrema and signed forces.',
        'Convergence: eight base checks, six accepted line trials, no failed trials or bisections. Residual and both constraint bounds are visible.',
        'Minor annotation issue retained: the outside legend overlaps part of the right convergence-panel title. Data and both bound markers remain visible; no redraw or additional inspection was performed.',
        'No old media were opened and no additional GIF decode was performed. Positive unsigned distance and weak body resultant do not establish effective clamping pressure.'
    ], recording_read_scope='Ordinary execution receipt and producer seal/stat only; no media open/hash/decode/render, tests or scientific computation.')
target = STAGE / 'author/pixel_QA.json'
with target.open('x', encoding='utf-8', newline='\n') as handle:
    json.dump(record, handle, ensure_ascii=False, indent=2, allow_nan=False)
    handle.write('\n')
print(json.dumps(dict(status=record['status'], count=record['count'])))
