"""Prepare a new integration overlay from closed M-RESUME1 source bytes."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

root = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
external = Path(__file__).resolve().parent
stage = root/'lf_data_preparation/native_interface_001/saved_continuation_001'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip() == 'd45f6ee92d8a0d6ca740772a1762abdc691489fa'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root)
protocol = json.loads((stage/'protocol.json').read_bytes())
assert json.loads((stage/'production_launch.json').read_bytes())['status'] == 'pass'
sources = sorted((stage/'candidate/hf_repo').rglob('*.py'))
assert len(sources) == 8
pins = {}
for source in sources:
    rel = source.relative_to(root).as_posix()
    raw = source.read_bytes()
    assert sha256(raw).hexdigest() == protocol['bindings'][rel]
    name = source.relative_to(stage/'candidate').as_posix()
    destination = external/'candidate'/name
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
    pins[name] = sha256(raw).hexdigest()
with (external/'overlay_origin.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(dict(status='prepared_closed_source_overlay',source_commit='d45f6ee92d8a0d6ca740772a1762abdc691489fa',
        origin_card='M-RESUME1',origin_source_sha256=pins,new_tests_or_science_executed=False),indent=2)+'\n')
print(json.dumps(dict(status='prepared_closed_source_overlay',files=8,new_science_calls=0)))
