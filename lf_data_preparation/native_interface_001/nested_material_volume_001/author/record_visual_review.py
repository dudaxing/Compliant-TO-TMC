"""Record root's actual PNG inspection; no rendering or scientific calculations."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import struct

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/nested_material_volume_001'
EXT=Path(__file__).resolve().parent
records=[]
for name in ('nine_point_material_P.png','material_depth_volume_comparison.png'):
    path=ROOT/REL/'run_001'/name
    raw=path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    width,height=struct.unpack('>II',raw[16:24])
    records.append(dict(path=f'{REL}/run_001/{name}',bytes=len(raw),sha256=sha256(raw).hexdigest(),
        dimensions_pixels=[width,height],root_actual_view_image=True,detail='original'))
report=dict(status='pass_actual_images_inspected_with_limits',recorded_utc=datetime.now(timezone.utc).isoformat(),
    inspected_by='root via view_image, both original pixel images',images=records,
    observations=[
        'All four state/cell cases and both force components are identifiable; sample eta order is bottom -1, middle0, top+1, xi order left to right.',
        'Saved P_iY retains sign, MPa labels, independent signed color scales per panel and formatted sample annotations. State13 bottom-right samples dominate visually.',
        'Q bars retain signed N values. Only three Q columns partition volume; V, original W and old T are comparison columns. State6 middle Q and state13 bottom Q dominate.',
        'V/W bar heights overlap visually, but exact residuals remain in CSV; visual agreement does not replace numeric observations.',
        'These are reference sampling and local material-contribution diagrams; existing M-PTRACE1 deformation remains the structure view.'],
    limits=[
        'Independent scales forbid comparison of absolute magnitude by colors or equal bar height between panels.',
        'Dominant peak samples make smaller points nearly gray; formatted annotations and exact CSV preserve them.',
        'Annotations use scientific-format rounding; exact CSV/JSON values are authoritative.',
        'No new deformation, Hu-inclusive pressure, effective grip, continuum cause or solver correctness is established by these images.'],
    original_images_preserved=True,new_render_calls=0,NPZ_decodes_or_API_or_contractions=0)
with (EXT/'visual_review.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=report['status'],images=len(records),dimensions=[r['dimensions_pixels'] for r in records])))
