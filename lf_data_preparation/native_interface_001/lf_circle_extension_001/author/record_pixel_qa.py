"""Record four completed root image inspections without opening media again."""
from datetime import datetime, timezone
import json
from pathlib import Path
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/lf_circle_extension_001'
STAGE=ROOT/REL
receipt=json.loads((STAGE/'run_001/execution_receipt.json').read_bytes())
assert receipt['status']=='pass'
files=[]
for name in ('view/comparison.png','view/distances_forces.png','view/peak_fields.png','convergence/convergence.png'):
    path=REL+'/run_001/'+name; seal=receipt['outputs'][path]
    assert (ROOT/path).stat().st_size==seal['bytes']
    files.append(dict(path=path,inspection_count=1,original_window_identity=seal))
record=dict(card='L-CEXT1',status='pass_pixel_inspection_with_minor_annotation',inspection_count=4,files=files,
    inspected_utc=datetime.now(timezone.utc).isoformat(),
    scope='Each new PNG viewed once using view_image(detail=original); displayed output was resized to width2048. No full-resolution pixel claim, redraw, media rehash or extra GIF decode.',
    observations=[
        'Full mirrored x1 mechanism and lower-half local circle/raster/closest witness are legible. Peak and last both label child state1/d0.75 as expected; the page explicitly identifies .5 source-anchor revalidation and inherited prefix.',
        'Response and distance/force plots contain only the two child samples .5/.75. Actual Q1 minimum and more distant reference-tip distance are distinct. Signed Fx/Fy total/material/Hu curves are readable and keep the lower-half weak-resultant scope.',
        'Four peak field panels separate solid mean J/Green strain and free-medium mean J/Hu Frobenius; summary integration-point extrema differ from displayed element means/norms by definition.',
        'Convergence shows one low-residual anchor check plus seven new loading checks, six accepted line searches and no failure/bisection. Accepted residuals are below the1e-9 gate. In the constraint panel the upper-right legend covers the visible location of the .75 bound marker; its exact7.5e-11 mm bound and saved residual remain available in convergence JSON. This minor annotation issue is retained without redraw.'
    ],science_qualification_unchanged=True)
with (STAGE/'author/pixel_QA.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print('Four completed inspections recorded; no new media read.')
