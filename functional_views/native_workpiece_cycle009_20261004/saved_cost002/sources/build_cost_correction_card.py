"""New saved-only cost view for a witnessed legend/axis-label collision."""
from pathlib import Path
from hashlib import sha256
import json
import shutil

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).parent
VIEW=ROOT/'functional_views/native_workpiece_cycle009_20261004'
OLD=VIEW/'saved_render_001'
CARD=VIEW/'saved_cost002'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
old=read(OLD/'render_launch.json')
assert old['status']=='pass' and old['exit_code']==0 and old['invocations']==1
assert old['all_bindings_unchanged'] and read(OLD/'render_receipt.json')['programs_completed']==3
pins={}
for name,expected in read(OLD/'protocol.json')['bindings'].items():
    assert sha(ROOT/name)==expected
    pins[name]=expected
for name in ('protocol.json','render_launch.json','render_receipt.json','cost_001/tangent_cost.png'):
    pins[rel(OLD/name)]=sha(OLD/name)
candidate=AUTHOR/'plot_tangent_cost002.py'
assert sha(candidate)=='e86a5de77784dae63ca86fd5b33e0c4e703a6f08d145054cc7b7983d09dca351'
assert not CARD.exists()
CARD.mkdir()
shutil.copyfile(candidate,CARD/candidate.name)
shutil.copyfile(OLD/'launch_phase.py',CARD/'launch_phase.py')
worker=(OLD/'render_saved_once.py').read_bytes()
assert worker.count(b'programs_completed"]==3')==1
with (CARD/'render_saved_once.py').open('xb') as stream:
    stream.write(worker.replace(b'programs_completed"]==3',b'programs_completed"]==1'))
shutil.copyfile(Path(__file__),CARD/Path(__file__).name)
(CARD/'sources').mkdir()
for name in (candidate.name,'render_saved_once.py','launch_phase.py',Path(__file__).name):
    source=CARD/name
    compile(source.read_bytes(),str(source),'exec')
    pins[rel(source)]=sha(source)
    shutil.copyfile(source,CARD/'sources'/name)
    pins[rel(CARD/'sources'/name)]=sha(source)
protocol=dict(schema_version='saved-cycle009-cost-label-correction-1.0',bindings=pins,
    sampled_RSS_bytes=8*1024**3,
    phases={'render':dict(argv=[rel(CARD/'render_saved_once.py')],helper_seconds=120,outer_seconds=150)},
    render_programs=[[rel(CARD/candidate.name),'--output',rel(CARD/'render_001')]],
    reason='Root viewed the original PNG: legend covers the Peak/1.75 mm label. Only legend and footer positions change; old closed three-view card unchanged.',
    new_mechanics_or_geometry_calls=0,mechanical_hooks_monitored=False,
    scope='Same saved timing and numbers; new layout only; no mechanical or geometry rerun',
    stop_policy='One invocation; first error closes new card; no retry/force/budget extension')
with (CARD/'protocol.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(protocol,stream,indent=2);stream.write('\n')
print(json.dumps(dict(status='prepared_not_executed',bindings=len(pins),protocol_sha256=sha(CARD/'protocol.json'))))
