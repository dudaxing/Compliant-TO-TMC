"""Read saved GIF metadata and extract an existing frame for visual inspection."""
from pathlib import Path
import json
from PIL import Image

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/functional_views/right_margin_20261007/complete_001/view')
OUTPUT = Path(__file__).resolve().parent/'image_inspection_001'
OUTPUT.mkdir(exist_ok=False)
records = []
for label in ['gamma1e6','right2col']:
    with Image.open(ROOT/label/'actual_states.gif') as gif:
        assert gif.n_frames == 24
        records.append(dict(label=label,frames=gif.n_frames,size=list(gif.size),duration_ms=gif.info.get('duration')))
        if label == 'right2col':
            gif.seek(13)
            gif.convert('RGB').save(OUTPUT/'right2col_actual_peak_frame.png')
(OUTPUT/'gif_inspection.json').write_text(json.dumps(dict(status='pass',records=records,new_scientific_calls=0),indent=2)+'\n',encoding='utf-8')
print(json.dumps(records))
