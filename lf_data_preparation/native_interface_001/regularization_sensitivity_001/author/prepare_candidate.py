"""Prepare ordinary alpha-task JSON and source files, without executing HF."""
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/regularization_sensitivity_001'
BASE = '5af8b5eb3d6780065075b8a331b774d8dad57d67'
PARENT = 'lf_data_preparation/native_interface_001/nested_cycle_001'
STAGE = ROOT/REL
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip() == 'main'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
assert not STAGE.exists()
assert read(EXT/'mesh_task_audit.json')['status'] == 'pass_metadata_and_inherited_provenance_same_physical_task'
assert read(EXT/'parameter_task_audit.json')['status'] == 'completed_readonly_parameter_task_comparability_audit_no_new_science'
author_receipt = read(EXT/'worker_author_receipt.json')
assert author_receipt['status'] == 'prepared_external_source_AST_only_not_execution'
assert all(sha(EXT/name) == pin for name, pin in author_receipt['files_SHA256'].items())
parent_task = read(ROOT/PARENT/'task.json')
task = deepcopy(parent_task)
prefix = parent_task['path']['targets_mm'][:15]
assert prefix == [0., .25, .5, .65, .75, .8, .85, .9, .95, 1., 1.05, 1.1, 1.15, 1.2, 1.15]
task.update(task_id='EXPLORATORY_fixed_square_h05_alpha5em7_prefix15__M_ALPHA1',
            purpose='same_task_single_factor_regularization_sensitivity',
            parameter_origin='M-ALPHA1: only alpha changes; original same-task 15-target ordered prefix, fresh zero start.',
            description='Original fixed square, geometry, domain and gamma; alpha half value, original loading plus one local unloading step. Sensitivity only.')
task['regularization']['alpha'] = 5e-7
task['path']['targets_mm'] = prefix
nonphysical = {'task_id','purpose','parameter_origin','description'}
left, right = ({k:v for k,v in source.items() if k not in nonphysical} for source in (parent_task, task))
assert {k:v for k,v in left.items() if k not in ('regularization','path')} == {k:v for k,v in right.items() if k not in ('regularization','path')}
assert task['regularization'] == {'alpha':5e-7,'length_mm':80.0}
assert task['third_medium']['gamma'] == 1e-6 and task['path']['kind'] == 'ordered_cycle'
old_manifest = read(ROOT/PARENT/'manifest.json')
manifest = deepcopy(old_manifest)
manifest['cases'] = [dict(label='alpha_half', geometry=old_manifest['cases'][0]['geometry'],
                          task=REL+'/task.json', output=REL+'/run_001/alpha_half')]
manifest['options']['settings']['time_limit_seconds'] = 9000.0
assert {k:v for k,v in manifest['options']['settings'].items() if k!='time_limit_seconds'} == {
    k:v for k,v in old_manifest['options']['settings'].items() if k!='time_limit_seconds'}

STAGE.mkdir()
(STAGE/'author').mkdir()
write_new(STAGE/'task.json', task)
write_new(STAGE/'manifest.json', manifest)
for name in ('execute_alpha_cycle.py','compare_alpha_views.py','M-ALPHA1_CARD.md'):
    if name.endswith('.py'):
        ast.parse((EXT/name).read_text(encoding='utf-8'))
    (STAGE/name).write_bytes((EXT/name).read_bytes())
(STAGE/'launch_alpha.py').write_bytes((ROOT/PARENT/'launch_cycle.py').read_bytes())
for name in ('MESH_TASK_AUDIT.md','mesh_task_audit.json','PARAMETER_TASK_AUDIT.md',
             'parameter_task_audit.json','IMPLEMENTATION_OPTIONS.md','prepare_candidate.py','worker_author_receipt.json'):
    (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
proof = EXT.parent/'MBOUND1_execution_review_001/publication_receipt.json'
assert read(proof)['published_commit'] == BASE and read(proof)['status'] == 'published_and_incrementally_restored_pass'
(STAGE/'author/M_BOUND1_execution_publication_receipt.json').write_bytes(proof.read_bytes())

old_protocol = read(ROOT/PARENT/'protocol.json')
paths = {name for name in old_protocol['bindings'] if name.startswith('hf_repo/')}
paths.update({PARENT+'/task.json',PARENT+'/manifest.json',PARENT+'/run_001/fixed_square/model/model.json',
              PARENT+'/run_001/fixed_square/result.json', PARENT+'/run_001/accepted_progress.jsonl',
              'hf_repo/src/hf_eval/native_region_geometry.py','hf_repo/src/hf_eval/workpiece_nodal.py',
              'hf_repo/scripts/measure_native_workpiece_regions.py',
              'functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py',
              'functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/summary.json',
              'functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/states.csv',
              manifest['cases'][0]['geometry'],manifest['cases'][0]['geometry'].replace('geometry.json','geometry.npz')})
paths.update(path.relative_to(ROOT).as_posix() for path in STAGE.rglob('*') if path.is_file())
bindings = {name:sha(ROOT/name) for name in sorted(paths)}
protocol = dict(schema_version='same-task-alpha-prefix-card-1.0', card='M-ALPHA1', prepared=True,
    authorized=False, executed=False, preparation_baseline_commit=BASE,
    manifest_file=REL+'/manifest.json', candidate_directory=REL+'/run_001/alpha_half',
    view_directory=REL+'/run_001/view', targets_mm=prefix, expected_original_targets=15,
    baseline_result=PARENT+'/run_001/fixed_square/result.json',
    baseline_model=PARENT+'/run_001/fixed_square/model/model.json',
    baseline_summary='functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/summary.json',
    baseline_csv='functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/states.csv',
    viewer_source='functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py',
    view_seconds=600, sampled_RSS_bytes=8*1024**3,
    expected_counts=read(ROOT/PARENT/'run_001/fixed_square/model/model.json')['region_metadata']['counts'],
    gates=deepcopy(old_protocol['gates']),
    phases=dict(production=dict(helper_seconds=9600,outer_seconds=9660,
        argv=[REL+'/execute_alpha_cycle.py','--repo','.','--protocol',REL+'/protocol.json'])),
    bindings=bindings, scope='One new alpha-only 15-target ordered prefix from zero, existing production gates, one pure saved-view child and original-target comparison; no HP, force repairs, pressure/grip/stability/HF5 qualification.',
    numerical_authorization_required='Separate actual direct-human M-ALPHA1 approval, recorded before any candidate import or numerical call.')
write_new(STAGE/'protocol.json', protocol)
receipt = dict(status='ordinary_candidate_prepared_not_authorized_not_executed', source_baseline_commit=BASE,
    task_sha256=sha(STAGE/'task.json'), manifest_sha256=sha(STAGE/'manifest.json'),
    protocol_sha256=sha(STAGE/'protocol.json'), bindings_checked=len(bindings),
    physical_difference={'regularization.alpha':{'baseline':1e-6,'candidate':5e-7}},
    path_difference='Original ordered-cycle prefix of 15 targets; one unloading step, no remaining unload targets.',
    settings_difference={'time_limit_seconds':{'baseline':14400.,'candidate':9000.}},
    old_launcher_copied_exactly=sha(STAGE/'launch_alpha.py')==sha(ROOT/PARENT/'launch_cycle.py'),
    AST_parsed_only=['execute_alpha_cycle.py','compare_alpha_views.py'],
    actual_scientific_actions=dict(HF_imports=0,NPZ_decodes=0,models=0,API=0,force_tangent=0,
                                 equilibrium=0,HP=0,new_renders=0),
    authorized=False,executed=False,whole_HF5_complete=False)
write_new(STAGE/'author/preparation_receipt.json', receipt)
assert all(sha(ROOT/name)==pin for name,pin in bindings.items())
print(json.dumps(dict(status=receipt['status'],bindings=len(bindings), protocol_sha256=receipt['protocol_sha256'])))
