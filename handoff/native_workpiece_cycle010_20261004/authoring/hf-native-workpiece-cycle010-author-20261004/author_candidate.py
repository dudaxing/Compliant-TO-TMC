"""Author a task-only eleven-target candidate; no imports or FE execution."""
from pathlib import Path
import ast
import difflib
from hashlib import sha256
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
PRIOR = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_009'
BASELINE = '07134ea6cd9aa0ab2de4bf97f80a8e8ca44c241e'
TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]
sha = lambda p:sha256(p.read_bytes()).hexdigest()


def emit(name, raw):
    with (AUTHOR/name).open('xb') as stream:
        stream.write(raw)


def migrate(old_name, new_name, changes):
    before = (PRIOR/old_name).read_bytes()
    after = before
    for old,new,count in changes:
        assert after.count(old.encode()) == count, (old, after.count(old.encode()))
        after = after.replace(old.encode(),new.encode())
    restored = after
    for old,new,count in reversed(changes):
        assert restored.count(new.encode()) == count, new
        restored = restored.replace(new.encode(),old.encode())
    assert restored == before
    compile(ast.parse(after.decode('utf-8')),new_name,'exec')
    emit(new_name, after)
    diff = ''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),
                                      fromfile=old_name,tofile=new_name))
    emit(new_name+'.diff',diff.encode())
    return dict(prior_source=old_name,prior_sha256=sha(PRIOR/old_name),candidate_sha256=sha(AUTHOR/new_name),
                inverse_bytes_exact=True,changes=changes)


task = json.loads((PRIOR/'task.json').read_text(encoding='utf-8'))
task.update(task_id='EXPLORATORY_fixed_workpiece_gripper_coarse_square_cycle010_chunk256_1p8mm',
    purpose='fixed_workpiece_near_contact_1p8mm_ordered_loading_return',
    parameter_origin='User-delegated symmetric workpiece and larger stroke exploration; independent zero-start, preserve all009 targets and add1.8 peak plus1.75 unloading target',
    description='Full eleven-target 0/.5/1/1.5/1.75/1.8/1.75/1.5/1/.5/0 mm fixed16mm square; original mechanical core/gates, fresh80/120 reference on every accepted state after full production success')
task['input'] = dict(task['input'],target_mm=1.8)
task['path'] = dict(kind='ordered_cycle',targets_mm=TARGETS)
emit('task.json',(json.dumps(task,indent=2)+'\n').encode())
notes = {}
notes['execute'] = migrate('execute_cycle009.py','execute_cycle010.py',[
    ('[0,.5,1,1.5,1.75,1.5,1,.5,0]','[0,.5,1,1.5,1.75,1.8,1.75,1.5,1,.5,0]',1)])
notes['reference'] = migrate('audit_cycle009.py','audit_cycle010.py',[
    ('coarse square 1.75 mm cycle','coarse square 1.8 mm cycle',1),
    ('default=240.','default=300.',1),
    ('BASELINE = "97b7e0eecd07aee0bd16c61961dedb360202641c"','BASELINE = "'+BASELINE+'"',1),
    ('TARGETS = [0., .5, 1., 1.5, 1.75, 1.5, 1., .5, 0.]',
     'TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]',1),
    ('time_limit_seconds=600.','time_limit_seconds=900.',1),
    ('production_seconds=600, reference_seconds=240','production_seconds=900, reference_seconds=300',1),
    ('production_outer_seconds=660, reference_outer_seconds=300','production_outer_seconds=960, reference_outer_seconds=360',1),
    ('Nine-target','Eleven-target',2),
    ('coarse_square_cycle_009','coarse_square_cycle_010',1),
    ("PREVIOUS_TASK_PIN = '2d74cda71e66d648fc27ef19a8950ee7b23901ce7cc41ac066c00b566c7f2906'",
     "PREVIOUS_TASK_PIN = 'aa6801849144f85fe6db1ab68db0869d6895b531a556481234f1e0fc9339c54c'",1),
    ('coarse_square_cycle_007/task.json','coarse_square_cycle_009/task.json',1),
    ('prepare_cycle009.py','prepare_cycle010.py',1),
    ('execute_cycle009.py','execute_cycle010.py',1),
    ('launch_cycle009.py','launch_cycle010.py',1),
    ('declared 1.75 mm peak','declared 1.8 mm peak',1),
    ('len(inventory["input_bindings"]) == 63','len(inventory["input_bindings"]) == 73',1),
    ('Expected 63 declared inputs for the new nine-target card','Expected 73 declared inputs for the new eleven-target card',1),
    ('[0,.5,1,1.5,1.75,1.5,1,.5,0]','[0,.5,1,1.5,1.75,1.8,1.75,1.5,1,.5,0]',1),
    ('exactly the declared 240 seconds','exactly the declared 300 seconds',1)])
for name in ('core_audit_mechanical.py','launch_cycle009.py'):
    new = name.replace('009','010')
    emit(new,(PRIOR/name).read_bytes())
    notes[new] = dict(prior_sha256=sha(PRIOR/name),candidate_sha256=sha(AUTHOR/new),bytes_exact=True)
emit('candidate_migration.json',(json.dumps(dict(baseline_commit=BASELINE,targets_mm=TARGETS,
    model_and_core_unchanged=True,notes=notes,scope='Author/static compile only; no tests/FE/HP/official card opened'),indent=2)+'\n').encode())
print(json.dumps(dict(status='authored_not_executed',task_sha256=sha(AUTHOR/'task.json'),sources_static_compile='pass')))
