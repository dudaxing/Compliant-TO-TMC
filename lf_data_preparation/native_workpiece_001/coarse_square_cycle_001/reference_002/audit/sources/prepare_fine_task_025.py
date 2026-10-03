"""Prepare the existing native fine gripper original 0.025 mm TEST without mechanics."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    source_inventory = ROOT/'lf_data_preparation/native_force_001/input_inventory.json'
    prior = next(row for row in json.loads(source_inventory.read_text(encoding='utf-8'))['cases']
                 if row['alias'] == 'gripper_native_fine')
    for name, pin in (('geometry_file','geometry_file_sha256'), ('geometry_npz_file','geometry_npz_sha256'),
                      ('task_file','task_file_sha256'), ('prior_model_file','prior_model_sha256')):
        if digest(ROOT/prior[name]) != prior[pin]:
            raise RuntimeError('Changed reviewed input: '+prior[name])
    task = json.loads((ROOT/prior['task_file']).read_text(encoding='utf-8'))
    task.update(task_id='TEST_native_fine_task_025_20261003', purpose='mean_driven_task_test',
        parameter_origin='Numerical execution of the existing native h0.5 fine candidate original 0.025 mm TEST; unchanged reviewed physics; H2/H3 unresolved',
        description='Execute the original 0.025 mm numerical TEST through targets [0,0.005,0.010,0.025] mm from undeformed zero lift on the existing fine candidate. Free output and no workpiece; different design from the coarse candidate, not mesh convergence or H2/H3 research qualification')
    task['input']['target_mm'] = .025
    task_path = STAGE/'task.json'
    with task_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(task, stream, indent=2)
        stream.write('\n')
    with np.load(ROOT/prior['prior_model_file'], allow_pickle=False) as archive:
        model = {name: archive[name].copy() for name in archive.files}
    b_in = model['b_in']
    direction = b_in/np.max(np.abs(b_in))
    direction[model['fixed_dofs']] = 0.
    direction_path = STAGE/'direction.npz'
    with direction_path.open('xb') as stream:
        np.savez_compressed(stream, direction=direction, multiplier_direction=np.array(0.))
    lifting_path = STAGE/'lifting.npz'
    with lifting_path.open('xb') as stream:
        np.savez_compressed(stream, lift_origin=np.zeros(len(b_in)), lift_shape=np.zeros(len(b_in)))
    inputs = {key: prior[key] for key in ('alias','geometry_file','geometry_file_sha256','geometry_npz_file','geometry_npz_sha256','geometry_id','prior_model_file','prior_model_sha256','elements','dofs')}
    inputs.update(task_file=task_path.relative_to(ROOT).as_posix(), task_file_sha256=digest(task_path),
        prior_task_file=prior['task_file'], prior_task_sha256=prior['task_file_sha256'],
        direction_file=direction_path.relative_to(ROOT).as_posix(), direction_file_sha256=digest(direction_path),
        direction_array_sha256=sha256(direction.tobytes()).hexdigest(),
        lifting_file=lifting_path.relative_to(ROOT).as_posix(), lifting_file_sha256=digest(lifting_path),
        targets_mm=[0., .005, .010, .025], fixed_DOFs=len(model['fixed_dofs']), free_DOFs=len(model['free_dofs']), result_directory='result')
    gates = dict(production_residual='1e-9', independent_residual='1e-8', force_evaluation='1e-9',
        average_constraint='1e-10', global_force_balance='1e-6', fixed_displacement_mm='8e-11',
        hp80_hp120='1e-40', total_force='1e-11', material_force='1e-9', regularization_force='1e-9',
        total_tangent='1e-10', material_tangent='1e-9', regularization_tangent='1e-9',
        augmented_force_tangent='1e-10', augmented_constraint_tangent='1e-10')
    settings = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
        force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
        max_bisections=4, minimum_increment=.001/16, time_limit_seconds=1500.)
    inventory = dict(schema_version='native-mean-input-inventory-1.0', baseline_commit='66398e9245c63c05d225f015cf50f1d95909344d',
        case=inputs, settings=settings, gates=gates, test_id=task['task_id'],
        stage_metadata=dict(purpose='existing_native_fine_candidate_original_task_TEST',
            stored_task_target_mm=.025, requested_targets_mm=[0., .005, .010, .025],
            minimum_increment_basis='Inherited preceding fine 0.001 mm / 16 = 6.25e-5 mm; not recalculated from the first new target',
            task_target_role='Original 0.025 mm construction TEST is retained and is this path target; no HF3/HF5 research target'),
        preparation_source=dict(inventory_file=source_inventory.relative_to(ROOT).as_posix(),
            sha256=digest(source_inventory), selected_alias='gripper_native_fine',
            role='Geometry, original task and saved intrinsic model only; no historical displacement reused'),
        direction_definition='v=b_in/max(abs(b_in)); actual fixed DOFs zero; dimensionless; multiplier direction 0 N/mm',
        state_authority='D(lift)+D(fluctuation); zero lift origin and shape; independent mean measurement',
        reference_definition='Per accepted state HP80/120 on all elements with disconnected local numbering, then exact Decimal scatter to real DOFs; no spatial sampling',
        qualification='Existing native fine candidate original 0.025 mm no-workpiece numerical TEST only; different design, not mesh convergence; independent qualification is separate',
        execution_limits=dict(production_seconds=1500, reference_seconds=720, sampled_RSS_bytes=8*1024**3,
            production_outer_seconds=1560, reference_outer_seconds=780, view_outer_seconds=120),
        stop_policy='First stage error stops; no repair, retry, force or reopening a closed window',
        reference_call_rule='2 times actual accepted-state count including all bisections; requested four targets -> at least 8 calls, 102400 element-precision instances')
    with (STAGE/'input_inventory.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(inventory, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(prepared='native fine gripper original 0.025 mm TEST through [0,0.005,0.010,0.025] mm', elements=inputs['elements'], dofs=inputs['dofs'], force_calls=0,tangent_calls=0,HP_calls=0,solver_calls=0)))


if __name__ == '__main__':
    main()
