"""Freeze unchanged009 mechanics for an independent eleven-target1.8mm task."""
from pathlib import Path
from time import perf_counter
from hashlib import sha256
import json
import shutil
import subprocess

STARTED = perf_counter()
ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
BASELINE = '07134ea6cd9aa0ab2de4bf97f80a8e8ca44c241e'
TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]
NAMES = ('core_audit_mechanical.py','audit_cycle010.py','prepare_cycle010.py','execute_cycle010.py','launch_cycle010.py')
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
digest = lambda p:sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')


def checkpoint():
    if perf_counter()-STARTED > 60 or (STAGE/'stop_requested.txt').exists():
        raise RuntimeError('Input/source preparation window closed')


def main():
    prior = STAGE.parent/'coarse_square_cycle_009'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASELINE
    assert not (STAGE/'input_inventory.json').exists() and not (STAGE/'sources').exists()
    old = read(prior/'input_inventory.json')
    sources009 = read(prior/'source_freeze.json')['sources']
    for phase in ('production','reference'):
        r = read(prior/(phase+'_launch.json'))
        assert r['status'] == 'pass' and r['exit_code'] == 0 and r['invocations'] == 1
        assert r['stop_reason'] is None and r['all_bindings_unchanged']
    previous_run = read(prior/'execution_receipt.json')
    previous_ref = read(prior/'reference/summary.json')
    previous_result = read(prior/'result/result.json')
    assert previous_run['status'] == previous_ref['status'] == 'pass'
    assert previous_result['status'] == 'success' and previous_result['accepted_states'] == 9
    assert previous_ref['accepted_states'] == 9 and previous_ref['HP_calls_completed'] == 18
    assert previous_ref['result_sha256'] == previous_run['result_sha256'] == digest(prior/'result/result.json')
    assert len(old['input_bindings']) == 63
    inputs = dict(old['input_bindings'])
    assert all(digest(ROOT/n) == v for n,v in inputs.items())
    assert all(digest(ROOT/n) == digest(prior/'sources'/Path(n).name) == v for n,v in sources009.items())
    checkpoint()
    task = read(STAGE/'task.json'); previous_task = read(prior/'task.json')
    allowed = {'task_id','purpose','parameter_origin','description','input','path'}
    assert {k:v for k,v in task.items() if k not in allowed} == {k:v for k,v in previous_task.items() if k not in allowed}
    assert task['input'] == dict(previous_task['input'],target_mm=1.8)
    assert task['path'] == dict(kind='ordered_cycle',targets_mm=TARGETS)
    model = ROOT/old['case']['workpiece_model_file']
    assert digest(model) == 'a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049'
    shutil.copyfile(prior/'direction.npz',STAGE/'direction.npz')
    assert digest(STAGE/'direction.npz') == digest(prior/'direction.npz')
    row = dict(old['case'],targets_mm=TARGETS)
    for name in ('task','direction'):
        file = STAGE/(name+('.json' if name == 'task' else '.npz'))
        row[name+'_file'] = file.relative_to(ROOT).as_posix()
        row[name+'_file_sha256'] = digest(file)
    legacy = read(STAGE.parent/'coarse_square_cycle_003/source_freeze.json')['sources']
    sources = {n:digest(ROOT/n) for n in legacy}
    assert len(sources) == 63 and all(v == sources009[n] for n,v in sources.items())
    transition = {n:dict(previous_sha256=v,current_sha256=sources[n]) for n,v in legacy.items() if v != sources[n]}
    assert transition == old['source_transition']
    for name in NAMES:
        path = STAGE/name; sources[path.relative_to(ROOT).as_posix()] = digest(path)
    assert len(sources) == len({Path(n).name for n in sources}) == 68
    (STAGE/'sources').mkdir()
    for n,v in sources.items():
        copy = STAGE/'sources'/Path(n).name
        shutil.copyfile(ROOT/n,copy); assert digest(copy) == v
    freeze = STAGE/'source_freeze.json'
    write(freeze,dict(schema_version='native-workpiece-cycle-source-freeze-1.0',baseline_commit=BASELINE,
        sources=sources,source_transition=transition,
        scope='Current009 original63 mechanics unchanged; retain four003 historical transitions; five new task wrappers only'))
    extras = [STAGE/n for n in ('task.json','direction.npz','README.md')]
    extras += [prior/n for n in ('input_inventory.json','source_freeze.json','execution_receipt.json',
        'reference/summary.json','result/result.json','production_launch.json','reference_launch.json')]
    for p in extras:
        inputs[p.relative_to(ROOT).as_posix()] = digest(p)
    assert len(inputs) == 73
    settings = dict(old['settings'],time_limit_seconds=900.)
    limits = dict(old['execution_limits'],production_seconds=900,reference_seconds=300,
                  production_outer_seconds=960,reference_outer_seconds=360)
    inventory = dict(old,baseline_commit=BASELINE,case=row,settings=settings,execution_limits=limits,
        input_bindings=inputs,source_freeze_sha256=digest(freeze),source_transition=transition,
        qualification='Only new independent zero-start eleven-target1.8mm fixed square and all actual accepted indices; no inherited old-state qualification',
        resource_origin='Explicit new900/960 production300/360 reference8GiB card; not a previous-card extension',
        reference_call_rule='Fresh80/120 for each actual accepted index, including repeats/bisections; original all-cell/all-DOF force/PORT-Jv/CSC/KKT/body gates; no energy/pressure/moment/all-column qualification')
    assert {k:v for k,v in settings.items() if k != 'time_limit_seconds'} == {k:v for k,v in old['settings'].items() if k != 'time_limit_seconds'}
    assert inventory['gates'] == old['gates'] and row['tangent_mode'] == 'chunk256'
    checkpoint()
    write(STAGE/'input_inventory.json',inventory)
    print(json.dumps(dict(status='prepared_only',sources=68,input_bindings=73,targets_mm=TARGETS,
        model_sha256=digest(model),helper_elapsed_seconds=perf_counter()-STARTED,
        force_calls=0,tangent_calls=0,solver_calls=0,HP_calls=0)))


if __name__ == '__main__':
    main()
