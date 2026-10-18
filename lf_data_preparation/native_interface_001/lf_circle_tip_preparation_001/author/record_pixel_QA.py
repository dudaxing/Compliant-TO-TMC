"""Record the one root inspection; read ordinary records and use media stat only."""
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001'
stage=ROOT/REL
read=lambda name:json.loads((stage/name).read_bytes())
receipt=read('run_001/execution_receipt.json')
launch=read('preparation_launch.json')
assert receipt['status']==launch['status']=='pass'
name=REL+'/run_001/tip_prepared.png'
assert (ROOT/name).stat().st_size==receipt['outputs'][name]['bytes']
assert not (stage/'author/pixel_QA.json').exists()
record=dict(card='L-CTIPPREP1',status='pass_pixel_review',inspections=1,
    media=[dict(path=name,inspections=1)],
    inspection_tool='view_image, once at root after the completed preparation',
    inspection_scope='Only the one new tip_prepared.png; no old media, arrays or GIF inspected',
    original_pixels=[2550,1700],tool_display_pixels=[1920,1280],
    observations=[
        'Four readable panels show the lower half at physical x1, finite-edge distances, right medium and comparison.',
        'Candidate orange actual Q1 lower boundary lies at y31 directly above the reference tip (80,30).',
        'Baseline and candidate distances are clearly distinguished; exact minimum equality is not claimed unique or first contact.',
        'Original LF right x80, historical HF right x84 and current right x92 are distinguished.',
        'Candidate right x89 to x92 six-column strip and free outer ux/uy except top uy are visible.',
        'Historical x74/84 margin1 is explicitly separated from candidate x80/92 margin3; baseline geometry only is reselected on the new92 grid.',
        'No deformed state, force or pressure is portrayed; no material plot regeneration needed.'
    ],producer_seal_inherited=receipt['outputs'][name],
    post_inspection_payload_reads=0,
    created_utc=datetime.now(timezone.utc).isoformat())
raw=json.dumps(record,ensure_ascii=False,indent=2)+'\n'
(stage/'author/pixel_QA.json').write_text(raw,encoding='utf-8',newline='\n')
(AUTHOR/'pixel_QA.json').write_text(raw,encoding='utf-8',newline='\n')
(stage/'author/record_pixel_QA.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(status=record['status'],inspections=1,media_stat_bytes=(ROOT/name).stat().st_size)))
