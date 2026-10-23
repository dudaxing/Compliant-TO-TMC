"""Prepare ordinary task/specification files only; no HF or scientific imports."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).parent
OUT = AUTHOR / 'delivery'
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_low_input_preparation_001'
OLD = 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001'
HIGH = 'lf_data_preparation/native_interface_001/lf_circle_tip_probe_001'
GEOMETRY = 'lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001/run_001/model/source_geometry/geometry.json'
BASELINE = 'dc4a8ec9263f6df7b3cf21957e0a3cd39b75ceee'


def read(name):
    return json.loads((ROOT / name).read_bytes())


def write(name, value):
    (OUT / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def identity(name):
    raw = (ROOT / name).read_bytes()
    return dict(path=name, bytes=len(raw), sha256=sha256(raw).hexdigest())


def differences(old, new, prefix=''):
    if isinstance(old, dict) and isinstance(new, dict):
        assert old.keys() == new.keys()
        return [item for key in old for item in differences(old[key], new[key], prefix+'/'+key)]
    return [] if old == new else [dict(field=prefix, old=old, new=new)]


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASELINE
    OUT.mkdir(exist_ok=False)
    task = read(OLD+'/alpha_task.json')
    low = deepcopy(task)
    low.update(task_id='EXPLORATORY_wave_circle_r9_c80_domain92_Lr80_alpha25em8_low_hold050__L_CTIPLOW1',
        purpose='low_input_guided_probe_matched_control_fresh_parent',
        parameter_origin='2026-10-23 user-authorized preparation only: fresh fixed-body loading [0,.25,.50], then a future guided probe q[0,.025] at held mean .50. No execution authorization is implied.',
        description='New explicit complete short fixed-workpiece parent; same original physics except input peak/path. Its successful original terminal .50 state alone may seed the future guided probe. Old intermediate states are not substituted.')
    low['input']['target_mm'] = .50
    low['path']['targets_mm'] = [0., .25, .50]
    diff = differences(task, low)
    assert {x['field'] for x in diff} == {'/task_id', '/purpose', '/parameter_origin', '/description', '/input/target_mm', '/path/targets_mm'}
    write('parent_task.json', low)
    write('TASK_DIFF.json', dict(source=OLD+'/alpha_task.json', changes=diff,
        physical_changes=['input.target_mm:1.06->0.50', 'path.targets_mm:13 original loading targets->explicit [0,.25,.50]'],
        all_other_task_values_exact=True, metadata_changes_are_not_mechanics=True))
    original = read(OLD+'/run_001/wave_circle_tip_alpha1/result.json')
    nonclock = {k:v for k,v in original['settings'].items() if k != 'time_limit_seconds'}
    settings = nonclock | {'time_limit_seconds':3600.}
    geometry = read(GEOMETRY)
    archive = (ROOT/GEOMETRY).with_name(geometry['arrays']['path'])
    old_half = next(x for x in read(OLD+'/run_001/state_table.json')['rows'] if x['d_mm'] == .5)
    files = [GEOMETRY, OLD+'/alpha_task.json', OLD+'/protocol.json',
        OLD+'/run_001/wave_circle_tip_alpha1/result.json', OLD+'/run_001/state_table.json',
        HIGH+'/RESULTS.md', HIGH+'/NEXT_STEPS.md', HIGH+'/run_001/view/state_table.json',
        'hf_repo/pyproject.toml', 'hf_repo/scripts/windows_owned_process_sup2.py']
    files += sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'hf_repo/src').rglob('*.py'))
    write('SOURCE_BINDINGS.json', dict(baseline_commit=BASELINE, files=[identity(n) for n in files],
        geometry_archive=dict(path=archive.relative_to(ROOT).as_posix(), bytes=archive.stat().st_size,
            declared_sha256=geometry['arrays']['sha256'], payload_read_or_rehashed=False,
            basis='Existing producer descriptor SHA declaration plus current stat only; actual identity must be checked inside the future authorized run.'),
        scope='Ordinary JSON/text/source reads and geometry NPZ stat only; no HF import, build, scientific payload read or media open.'))
    write('PROPOSED_EXECUTION.json', dict(stage='L-CTIPLOW1', status='prepared_not_authorized_or_run',
        prepared_from_commit=BASELINE, repo_relative_paths=True,
        geometry_file=GEOMETRY, parent_task_file=REL+'/parent_task.json',
        parent=dict(api='hf_eval.native_evaluate.evaluate_native', zero_start=True,
            targets_mm=[0.,.25,.50], saved_result=None, selected_state_index=None, extend_path=False,
            settings=settings, options=dict(response_mode='mechanical', tangent_mode='chunk256', initial_guess='port_projection'),
            settings_call_contract='Pass DisplacementSettings(**settings) only; omit API time_limit_seconds and minimum_increment arguments. Explicit modes; do not use zero-start defaults.',
            output='run_001/parent_fixed',
            readiness='success/path_completed/target_reached/loading_peak_reached true; exact original target coverage; last accepted original target .50; original numerical gates all accepted states'),
        probe=dict(api='hf_eval.native_probe.evaluate_native_guided_probe',
            saved_result='run_001/parent_fixed/result.json', selected_state_index='len(successful_parent.states)-1, not hard-coded 2',
            body_q_targets_mm=[0.,.025], held_input_mean_mm=.50, time_limit_seconds=3600.,
            output='run_001/probe_low', settings_inheritance='All new parent nonclock settings and modes; only probe clock is explicit.',
            fresh_q0='Original parent split lift/fluctuation and signed R; fresh F/T, checks=1 and identity unchanged; no repair/projection.',
            motion='Original body membership; all body ux=q, uy=0 and rotation=0. Original supports/symmetry retained. No remask.'),
        inherited_grid_expectation=dict(cells=14720,nodes=14985,dofs=29970,body_cells=510,body_nodes=565,
            note='Inherited metadata expectations, not a newly built or array-validated low-input model.'),
        original_gates=dict(relative_free_residual=1e-9, mean_constraint='Original scale-dependent constraint_bound; tolerance 1e-10',
            positive_J=True, relative_global_force_balance=1e-6, prescribed_displacement_mm=8e-11),
        comparison=dict(high_table=HIGH+'/run_001/view/state_table.json',
            exact_common_q_mm=[0.,.025], preserve_extra_actual_states=True, interpolation=False,
            signed_scalars=['Q total/material/Hu', 'each condition Q(q)-Q(0)', 'difference of those increments', 'R_input_N', 'ON-body Fy and guide ledger',
                'input_mean_mm', 'tip to physical raster body boundary', 'body to actual free right boundary', 'global/nonbody-medium minJ/max|Hu|', 'same right480 reference cells J/Hu', 'all convergence histories'],
            exclusions='No high/low force difference is automatically pure contact/friction/capacity; no zero-preload subtraction replacing raw values.'),
        proposed_resources=dict(parent_controller_seconds=3600, probe_controller_seconds=3600,
            shared_viewer_seconds=900, helper_seconds=9000, outer_seconds=9060,
            sampled_memory_GiB=64, per_library_thread_limit=16, viewer_memory_GiB=8,
            thread_libraries=['OMP','OPENBLAS','MKL','NUMEXPR'], GPU=False),
        execution_policy='Future implementation/freeze/static review before unique launch. Sequential separately supervised parent, probe and viewer processes. Each API once. First terminal error stops downstream science/display; retain partial. Original internal backtracking/bisection allowed; no external retry, repair rerun, extension, force, HP, tests, default installation or automatic rollback.',
        display_plan=dict(new_PNGs=4,new_GIFs=1,
            PNGs=['Actual x1 low probe geometry and tip at q0/terminal', 'Signed low forces, held input and all low/parent convergence diagnostics', 'Low right480 and all nonbody-medium J/Hu witnesses', 'High/low same-q original force/components/increments and geometry-medium scalars'],
            GIF='All actual accepted low probe states, actual frame count; no interpolation or old media opening.',
            array_reads='New low probe fields J/Hu only, at most 17 archives/34 fields; positions/model from new ordinary JSON. Original high state_table only; no old high NPZ or image pixels.',
            note='Four plots are a planned display budget, not generated evidence. Parent reference and terminal geometry can use new probe reference coordinates and its identity-matched q0 positions; this does not promise all parent intermediate deformations. Figure details freeze with the thin wrapper.'),
        qualification='Numerical guided displacement response only; no independent HP, pressure, effective grasp, bearing, release, stability, alpha/domain independence or HF5.',
        prerequisite='This preparation is complete only after independent finite review. Future wrapper sources/observer bindings and precise launch command must be frozen and statically reviewed under a new approved execution card. This file is not an executable launcher.'))
    write('PREPARATION_RESULT.json', dict(stage='L-CTIPLOWPREP1', status='ordinary_preparation_complete_pending_independent_review',
        created_utc=datetime.now(timezone.utc).isoformat(), client_date='2026-10-23', baseline_commit=BASELINE,
        authorization='Prepare only per latest user instruction; do not initiate trial.',
        task_changes=len(diff), nonclock_settings_exact=True, production_source_edits=0,
        new_HF_imports=0,new_model_builds=0,new_F=0,new_T=0,new_HP=0,new_equilibrium_solves=0,new_tests=0,
        individual_NPZ_reads=0,media_reads=0,
        old_half_selection_clue=dict(source=OLD+'/run_001/state_table.json',
            original_target_index=2, tip_distance_mm=old_half['tip_to_raster_boundary_mm'],
            scope='Historical .50 intermediate observation only; not the new parent/result or proof of no contact.'),
        budget_basis=dict(old_loading_to_half_cumulative_seconds=original['states'][2]['elapsed_seconds'],
            old_full_106_evaluation_seconds=original['timing_seconds']['evaluation'],
            probe1_outer_seconds=1186.2599043999799,
            note='Historical observations support proposed limits, not runtime guarantees or a resource authorization.'),
        no_low_result_exists=True, numerical_success=None))
    print(json.dumps(dict(status='prepared', directory=str(OUT),task_changes=len(diff),source_files=len(files))))


if __name__ == '__main__':
    main()
