"""Install/freeze one task-only cycle010; no mechanical evaluation."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010'
PRIOR = STAGE.with_name('coarse_square_cycle_009')
BASELINE = '07134ea6cd9aa0ab2de4bf97f80a8e8ca44c241e'
TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
digest = lambda p:sha256(p.read_bytes()).hexdigest()
rel = lambda p:p.relative_to(ROOT).as_posix()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')


def install():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASELINE
    assert read(AUTHOR/'candidate_readiness.json')['status'] == 'pass'
    assert read(AUTHOR/'card_readiness.json')['status'] == 'pass'
    names = ['prepare_cycle010.py','execute_cycle010.py','audit_cycle010.py',
             'core_audit_mechanical.py','launch_cycle010.py','task.json','README.md']
    pins = dict(read(PRIOR/'input_inventory.json')['input_bindings'])
    for n,v in read(PRIOR/'source_freeze.json')['sources'].items():
        assert digest(ROOT/n) == digest(PRIOR/'sources'/Path(n).name) == v
        pins[n] = v
    for name in ('input_inventory.json','source_freeze.json','execution_receipt.json',
                 'reference/summary.json','result/result.json','production_launch.json','reference_launch.json'):
        pins[rel(PRIOR/name)] = digest(PRIOR/name)
    assert all(digest(ROOT/n) == v for n,v in pins.items())
    assert not STAGE.exists()
    STAGE.mkdir()
    for name in names:
        shutil.copyfile(AUTHOR/name,STAGE/name)
        pins[rel(STAGE/name)] = digest(STAGE/name)
    (STAGE/'authoring').mkdir()
    for p in AUTHOR.iterdir():
        if p.name not in names and p.suffix in ('.py','.json','.md','.diff'):
            target = STAGE/'authoring'/p.name
            shutil.copyfile(p,target);pins[rel(target)] = digest(target)
    write(STAGE/'prepare_protocol.json',dict(schema_version='native-mechanical-cycle-card-1.0',
        baseline_commit=BASELINE,sampled_RSS_bytes=8*1024**3,bindings=pins,
        phases=dict(prepare=dict(argv=[rel(STAGE/'prepare_cycle010.py')],helper_seconds=60,outer_seconds=90)),
        scope='Input/source freeze only; no FE/constructor/HP',
        stop_policy='Each phase once; first formal failure closes card, no repair/retry/force/extension'))
    print(json.dumps(dict(status='installed_not_prepared',prepare_bindings=len(pins))))


def freeze():
    receipt = read(STAGE/'prepare_launch.json')
    assert receipt['status'] == 'pass' and receipt['exit_code'] == 0 and receipt['invocations'] == 1
    assert receipt['all_bindings_unchanged'] and receipt['stop_reason'] is None
    old,new = read(PRIOR/'input_inventory.json'),read(STAGE/'input_inventory.json')
    assert new['case']['targets_mm'] == TARGETS and new['case']['tangent_mode'] == 'chunk256'
    assert new['settings'] == dict(old['settings'],time_limit_seconds=900.) and new['gates'] == old['gates']
    assert new['execution_limits'] == dict(old['execution_limits'],production_seconds=900,reference_seconds=300,
        production_outer_seconds=960,reference_outer_seconds=360)
    assert len(new['input_bindings']) == 73
    sources = read(STAGE/'source_freeze.json')['sources']
    assert len(sources) == 68
    pins = dict(new['input_bindings'])
    for n,v in sources.items():
        assert digest(ROOT/n) == digest(STAGE/'sources'/Path(n).name) == v
        pins[n] = v;pins[rel(STAGE/'sources'/Path(n).name)] = v
    for name in ('input_inventory.json','source_freeze.json','prepare_protocol.json','prepare_launch.json'):
        pins[rel(STAGE/name)] = digest(STAGE/name)
    for n,v in read(STAGE/'prepare_protocol.json')['bindings'].items():
        assert digest(ROOT/n) == v;pins[n] = v
    write(STAGE/'protocol.json',dict(schema_version='native-mechanical-cycle-card-1.0',baseline_commit=BASELINE,
        sampled_RSS_bytes=8*1024**3,bindings=pins,
        phases=dict(production=dict(helper_seconds=900,outer_seconds=960,argv=[rel(STAGE/'execute_cycle010.py')]),
                    reference=dict(helper_seconds=300,outer_seconds=360,argv=[rel(STAGE/'audit_cycle010.py'),
                        '--input',rel(STAGE),'--output',rel(STAGE/'reference'),'--time-limit','300'])),
        prerequisite='Full production actual pass before fresh80/120 on every actual index; no partial HP replay',
        original_targets_mm=TARGETS,actual_accepted_count='Unknown until run; includes all controller bisections',
        scope='New task/explicit resources; same model/core/gates; no pressure/clamp/energy/moment/all-column/HF5 qualification',
        stop_policy='One invocation each; first formal failure closes entire card, no retry/repair/force/extension'))
    print(json.dumps(dict(status='frozen_not_executed',scientific_bindings=len(pins),sources=68,input_bindings=73,
                         protocol_sha256=digest(STAGE/'protocol.json'))))


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode',choices=('install','freeze'))
args = parser.parse_args()
install() if args.mode == 'install' else freeze()
