"""Archive root's actual post-run PNG observations; no media reads."""
import json
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_step_003'
notes=json.loads((AUTHOR/'PIXEL_NOTES.json').read_bytes())
names=('view/comparison.png','view/distances_forces.png','view/peak_fields.png','view/right_medium.png','convergence/convergence.png')
assert set(notes['observations'])==set(names) and notes['all_five_inspected_once'] is True
record=dict(card='L-CTIPSTEP3',status=notes['status'],inspections=5,
    media=[dict(path=REL+'/run_001/'+name,inspections=1) for name in names],
    observations=notes['observations'],image_regenerations=0,
    inspection_scope='Root inspected each five new PNG once after original helper closed. No GIF decode, payload rehash, rendering or science by this recorder. Original producer seal inherited.')
target=ROOT/REL/'author/pixel_QA.json'
assert not target.exists()
target.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(target.parent/'record_pixel_qa.py').write_bytes(Path(__file__).read_bytes())
(target.parent/'PIXEL_NOTES.json').write_bytes((AUTHOR/'PIXEL_NOTES.json').read_bytes())
print(json.dumps(dict(status='prior_pixel_observations_recorded',inspections=5,recorder_media_reads=0)))
