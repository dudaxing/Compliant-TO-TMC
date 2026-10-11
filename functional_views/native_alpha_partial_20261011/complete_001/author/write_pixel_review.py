"""Record the root's actual view_image inspection of existing six PNG files."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'functional_views/native_alpha_partial_20261011/complete_001/run_001/view'
FILES = ('loading_120_forces.png','alpha_response_comparison.png','comparison.png',
    'peak_fields.png','loading_085_forces.png','distances_forces.png')
record = dict(status='pass_actual_six_PNG_pixel_inspection_no_new_render',
    recorded_utc=datetime.now(timezone.utc).isoformat(),source_commit='7887aa1138f8e46a2b15f47a1060aa7d72cfe651',
    inspection_method='Root viewed each existing PNG through view_image original; tools may resize returned display. No file modification or new image generation.',
    PNGs=[dict(path=REL+'/'+name,sha256=sha256((ROOT/REL/name).read_bytes()).hexdigest()) for name in FILES],
    observations=[
        'Two actual force snapshots show failed loading indices6/13, x1 and visual mirror, three total/material/regularization panels, same all-body-node glyph scale and no pressure qualification.',
        'Full structure and fixed square visible; peak/last are both loading index13, not an unload state.',
        'Peak finite-surface zoom labels bottom distance0.0009697mm and right distance0.2994mm; distance witness and green ray arrows are geometry, not force.',
        'Six-panel alpha comparison shows nearly overlapping reaction/output curves, visible lower-body-force differences and separate free-medium minJ points near loading0.85. This is two-value sensitivity only.',
        'Peak fields label saved-F Green principal strain, cell mean J and Hu Frobenius norm, with colorbars distinct from integration-point minJ/max Hu component.',
        'Distance/Fx plot retains signed Fx and unsigned finite-distance/ray labels; no pressure curves or new unload data.'
    ],nonblocking_display_limits=[
        'The shared fourteen-state force scale makes early0.85 and Hu arrows small or visually absent; that does not mean zero force. Use stored values and force curves.',
        'GIF was not freshly regenerated or manually inspected at all14 frames in this pixel review; two helper-produced frame copies were inspected. Runtime receipt records14frames.',
        'Original comparison supertitle says orange distances while individual default-color distance lines are named in the legend; frozen viewer was not edited or rerun.'
    ],actions=dict(new_NPZ_decodes=0,new_HF_imports=0,new_observers=0,new_F_T=0,
        new_HP=0,new_solves=0,new_renders=0,new_scientific_arithmetic=0),
    original_M_ALPHA1_status='not_pass',unload_completed=False,pressure_effective_clamp_stability_HF5_qualified=False)
with (Path(__file__).parent/'root_pixel_review.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(record,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=record['status'],PNG_files=len(FILES)),ensure_ascii=False))
