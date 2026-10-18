"""Record root's already completed one-image inspection; no image reads."""
import json
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_circle_right_preparation_001'
record=dict(card='L-CRIGHT1',status='pass_pixel_inspection_with_nonblocking_layout_note',inspections=1,
    media=[dict(path='lf_data_preparation/native_interface_001/lf_circle_right_preparation_001/run_001/right_prepared.png',inspections=1)],
    observations=[
        'Four panels legible: full lower-half undeformed x1 mechanism, teal x71 and orange x74 Q1 body edges, fixed reference tip(80,30), x80 original LF and x84 actual HF limits.',
        'Local panel separates actual staircase/dotted analytic reference and finite-edge nearest/tip witnesses. Nearest remains1mm; same material reference tip distance4.24264 to2.5mm.',
        'Right zoom shows x83 body edge, shaded x83..84 strip and x84 ux/uy-free nodes except original top uy symmetry. Zoom shows upper part; full80rows are verified by layout data, not inferred from this viewport.',
        'Scalar panel preserves510cells/565nodes/1130DOFs/72physicaledges, medium width4 to1mm and no mechanics qualification.',
        'Nonblocking: local legends overlay part of the mechanism/closest-pair context and full-domain port labels are compact; main boundaries, witnesses and scalar values remain readable. No redraw.'
    ],
    note='一次PNG人工检查通过；局部图例覆盖少量结构背景，关键边界、距离和数表可读，未重绘。',
    identity_basis='Root called view_image exactly once on the new PNG after original helper closed, as scoped; producer seal inherited, no extra payload hash, decode or regeneration.',
    image_regenerations=0)
target=STAGE/'author/pixel_QA.json'
assert not target.exists()
target.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(STAGE/'author/record_pixel_qa.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(status='one_prior_pixel_inspection_recorded',inspections=1,image_reads_by_this_script=0)))
