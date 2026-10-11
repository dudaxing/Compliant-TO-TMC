"""Record the root's actual three-PNG inspection; no image decode or render."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

root = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
rel = 'lf_data_preparation/native_interface_001/saved_continuation_001/run_001/view'
view = json.loads((root/rel/'view.json').read_bytes())
assert view['status'] == 'pass'
names = ('comparison.png','distances_forces.png','peak_fields.png')
pins = {rel+'/'+name:sha256((root/rel/name).read_bytes()).hexdigest() for name in names}
assert all(view['outputs'][name] == pins[rel+'/'+name] for name in names)
review = dict(
    status='pass_actual_three_PNG_pixel_inspection_no_new_render',
    created_utc=datetime.now(timezone.utc).isoformat(),
    actual_tool='tools.view_image on all three existing PNG files, returned images inspected by root',
    inspected_repository_SHA256=pins,actual_PNGs_inspected=3,
    observations=[
        'Comparison shows actual x1 peak and final unloading geometry, fixed square and visual mirror; geometry is similar across the 0.05 mm descent.',
        'Peak tip enlargement annotates positive bottom distance and other finite distances; these are unsigned geometry observations, not forces.',
        'Force panel labels signed lower-body Fy total/material/regularization, input R and cached two-side magnitude separately.',
        'Distance/Fx panel and peak solid Green / medium mean J / Hu Frobenius fields have visible axes, units, legends and color scales.',
    ],
    interpretation='Only same-task first descending suffix; no pressure/effective-clamp/stability/HP qualification.',
    GIF_inspection='Actual existing GIF provided for user review; no claim of manual inspection of all frames.',
    actions=dict(new_HF_imports=0,new_NPZ_decodes=0,new_F_T=0,new_HP=0,new_solves=0,new_renders=0),
    executed_new_science=False,
)
target = Path(__file__).resolve().parent/'root_pixel_review.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status=review['status'],actual_PNGs_inspected=3)))
