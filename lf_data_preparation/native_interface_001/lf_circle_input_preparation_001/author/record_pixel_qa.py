"""Record the one completed root inspection; no image read or rehash."""
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_circle_input_preparation_001'
e=json.loads((STAGE/'run_001/execution_receipt.json').read_bytes())
assert e['status']=='pass'
name=(STAGE/'run_001/circle_prepared.png').relative_to(ROOT).as_posix()
seal=e['outputs'][name]
assert (ROOT/name).stat().st_size==seal['bytes']
record=dict(card='L-CPREP1',status='pass_pixel_inspection',inspection_count=1,
    inspected_utc=datetime.now(timezone.utc).isoformat(),path=name,original_window_identity=seal,
    scope='One root view_image inspection of the new PNG; no redraw, additional decoding or payload hash by recorder.',
    observations=['Three panels show actual undeformed lower-half geometry, original phases/support/ports, local staircase boundary and actual fixed nodes.',
        'Physical stair edges use a solid line; analytic semicircle and former square envelope are separate reference outlines.',
        'UNDEFORMED/NOT SOLVED, x1 coordinates, zoom-only panels and port reference-arrow semantics are visible.',
        'Circle count line (510 cells/565 nodes/1130 fixed DOFs) is readable; panel C second whole-model line overlaps some y40 node markers. This is a minor annotation issue; exact counts remain in diagnostics and model JSON. No replot performed.'],
    science_qualification_unchanged=True)
with (STAGE/'author/pixel_QA.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print('One completed pixel inspection recorded; no media read')
