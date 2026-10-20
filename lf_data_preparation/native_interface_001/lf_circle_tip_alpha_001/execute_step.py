"""One zero-start alpha experiment with original gates and saved-state displays."""
from time import perf_counter, sleep
STARTED = perf_counter()
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from math import fsum
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
CARD, LABEL = 'L-CTIPALPHA1', 'wave_circle_tip_alpha1'
BASE = '0687a138ca60ac09f6555b09132646e8a30bd5d7'
THREAD_ENV = dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16')


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n',
                    encoding='utf-8', newline='\n')


def main():
    protocol_file, auth_file = STAGE/'protocol.json', STAGE/'author/authorization.json'
    protocol, auth = read(protocol_file), read(auth_file)
    assert protocol['card'] == auth['card'] == CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['protocol_sha256'] == sha256(protocol_file.read_bytes()).hexdigest()
    assert auth['authorized_execution_source_commit'] == protocol['source_baseline_commit'] == BASE
    assert auth['approval_card'] == CARD and isinstance(auth['direct_human_request'], str) and auth['direct_human_request'].strip()
    assert (protocol['controller_seconds'], protocol['viewer_seconds'], protocol['helper_seconds'],
            protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (14400, 900, 16200, 16260, 64*1024**3)
    assert protocol['cpu_thread_limit'] == 16 and protocol['cpu_thread_environment'] == THREAD_ENV
    assert {name:os.environ.get(name) for name in THREAD_ENV} == THREAD_ENV
    run, stop = ROOT/protocol['output_directory'], STAGE/'stop_requested.txt'
    production, view = ROOT/protocol['production_directory'], ROOT/protocol['view_directory']
    assert production == run/LABEL and view == run/'view'
    assert not run.exists() and not stop.exists()
    run.mkdir(parents=True, exist_ok=False)
    receipt_file, progress = run/'execution_receipt.json', run/'accepted_progress.jsonl'
    calls, events, binding_reads = Counter(), Counter(), Counter()
    process, peak, TMCErrorClass = psutil.Process(), 0, None
    phase, outputs, seal_scope = 'bootstrap', {}, 'not_complete'
    receipt = dict(card=CARD, status='running', protocol_sha256=auth['protocol_sha256'],
        authorization_sha256=sha256(auth_file.read_bytes()).hexdigest(),
        source_baseline_commit=protocol['source_baseline_commit'], new_sources_pinned_individually=True,
        accepted_states=0, zero_start=True, saved_parent_or_state_used=False, extend_path=False,
        new_tests=0, default_installations=0, HP_calls_by_wrapper=0,
        mechanical_hooks_monitored=False,
        mechanical_hook_scope='Only original evaluate/solve/on_accept observed; F/T counts from returned cache metadata, not universal hooks',
        result_objects_retained_by_observer=False,
        cpu_thread_limit=16,cpu_thread_environment={name:os.environ[name] for name in THREAD_ENV},
        cpu_resource_scope='Per-library configuration before HF imports; not measured use of16 cores; unchanged CPU backend',
        viewer_internal_RSS_limit_bytes=8*1024**3,
        memory_resource_scope='Helper/outer sampled64GiB; original pure viewer retains stricter8GiB internal gate',
        qualification_scope='New alpha2.5e-7 zero-start loading through the unchanged13 absolute targets to1.06mm; no inheritance of old-alpha HP, no unloading, pressure, effective grip, release, stability, alpha-convergence, domain-width convergence or HF5 qualification')

    def checkpoint(event='resource_check'):
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
        reason = ('external_stop_requested' if stop.exists() else
                  'sampled_RSS_limit' if peak > protocol['sampled_RSS_bytes'] else
                  'whole_helper_elapsed_limit' if perf_counter()-STARTED > protocol['helper_seconds'] else None)
        if reason:
            receipt['resource_stop_reason'] = reason
            if TMCErrorClass is not None:
                raise TMCErrorClass(reason, code='time_limit')
            raise RuntimeError(reason)
        events[event] += 1

    def digest(path):
        value = sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                checkpoint()
                value.update(block)
        checkpoint()
        return value.hexdigest()

    def bindings():
        for name, pin in (protocol['input_bindings'] | protocol['source_bindings']).items():
            binding_reads[name] += 1
            assert digest(ROOT/name) == pin, name

    def seal():
        sealed = {}
        for path in sorted(run.rglob('*')):
            if path.is_file() and path != receipt_file:
                sealed[path.relative_to(ROOT).as_posix()] = dict(sha256=digest(path), bytes=path.stat().st_size)
        checkpoint()
        return sealed

    def child_once(argv, limit):
        checkpoint()
        calls['view_child_started'] += 1
        started, child_stop, child_error = perf_counter(), None, None
        env = dict(os.environ, **THREAD_ENV, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg')
        with (run/'view_child_stdout.log').open('xb') as output:
            child = subprocess.Popen(argv, cwd=protocol['working_directory'], env=env,
                                     stdout=output, stderr=subprocess.STDOUT)
            try:
                while child.poll() is None:
                    try:
                        checkpoint()
                        if perf_counter()-started > limit:
                            raise RuntimeError('view_child_elapsed_limit')
                    except Exception as error:
                        child_stop = child_stop or str(error)
                        if not stop.exists():
                            stop.write_text(child_stop, encoding='utf-8')
                    sleep(.1)
            except BaseException as error:
                child_error, child_stop = error, child_stop or type(error).__name__
            finally:
                if child.poll() is None:
                    if not stop.exists():
                        stop.write_text(child_stop or 'view_child_interrupted', encoding='utf-8')
                    child.wait()
        elapsed = perf_counter()-started
        if elapsed > limit or stop.exists():
            child_stop = child_stop or 'viewer_elapsed_or_stop_request'
        receipt['view_child_terminal'] = dict(exit_code=child.returncode, elapsed_seconds=elapsed,
            limit_seconds=limit, stop_reason=child_stop,
            cleanup='Actual child waited; cooperative stop, no force or hard-time-cap claim')
        if child_error is not None:
            raise child_error
        if child.returncode != 0 or child_stop is not None:
            raise RuntimeError('Viewer non-success; no retry or following stage')
        calls['view_child_completed'] += 1
        checkpoint()

    write(receipt_file, receipt)
    try:
        phase = 'bindings_and_task_contract'
        geometry_file, task_file = ROOT/protocol['geometry_file'], ROOT/protocol['task_file']
        geometry_descriptor = read(geometry_file)
        sole_old_payload = geometry_file.with_name(geometry_descriptor['arrays']['path']).relative_to(ROOT).as_posix()
        all_pins = protocol['input_bindings'] | protocol['source_bindings']
        assert {name for name in all_pins if Path(name).suffix.lower() in ('.npz','.npy','.png','.gif','.gz','.csv','.zip')} == {sole_old_payload}
        bindings()
        task, parent = read(task_file), read(ROOT/protocol['original_task_file'])
        baseline = read(ROOT/protocol['baseline_file'])
        assert protocol['baseline_file'] in protocol['input_bindings']
        assert protocol['comparison_source'] in protocol['source_bindings']
        targets = [0., .25, .5, .75, .9, .95, .98, 1., 1.02, 1.03, 1.04, 1.05, 1.06]
        assert parent['path'] == dict(kind='load_only', targets_mm=targets)
        assert parent['input']['target_mm'] == 1.06
        assert parent['regularization'] == dict(alpha=5e-7, length_mm=80.)
        assert set(protocol['task_metadata']) == {'task_id', 'purpose', 'parameter_origin', 'description'}
        expected = deepcopy(parent)
        expected.update(protocol['task_metadata'])
        expected['regularization']['alpha'] = 2.5e-7
        assert task == expected
        assert task['path'] == dict(kind='load_only', targets_mm=targets)
        assert protocol['targets_mm'] == task['path']['targets_mm'] and task['input']['target_mm'] == 1.06
        assert task['workpiece'] == dict(kind='fixed_rigid', shape='circle', center_mm=[80., 40.],
                                        radius_mm=9., fixed_components=[0, 1])
        assert geometry_descriptor['grid']['shape_yx'] == [80,184]
        assert geometry_descriptor['grid']['extent_mm'] == [92.,40.]
        assert geometry_descriptor['grid']['cell_size_mm'] == [.5,.5]
        assert geometry_descriptor['grid']['origin_mm'] == [0.,0.]
        assert task['geometry'] == dict(geometry_id=geometry_descriptor['geometry_id'],
            descriptor_sha256=geometry_descriptor['descriptor_sha256'])
        assert task['background_symmetry'] == dict(points_mm=[[0.,40.],[92.,40.]],components=[1])
        assert task['material'] == dict(E_MPa=1.,nu=.3,formulation='plane_strain')
        assert task['third_medium'] == dict(gamma=1e-6)
        assert task['regularization'] == dict(alpha=2.5e-7,length_mm=80.)
        assert geometry_descriptor['thickness_mm'] == 20.
        assert protocol['settings'] == read(ROOT/protocol['settings_source_protocol'])['settings'] | {'time_limit_seconds':14400.}
        assert protocol['settings']['time_limit_seconds'] == 14400.
        assert protocol['settings']['constraint_tolerance'] == float(protocol['gates']['average_constraint'])
        assert protocol['gates'] == read(ROOT/protocol['gates_source_protocol'])['gates']
        assert protocol['options'] == dict(response_mode='mechanical', tangent_mode='chunk256', initial_guess='port_projection')
        receipt.update(task_file_sha256=digest(task_file), parent_task_file_sha256=digest(ROOT/protocol['original_task_file']),
            task_scope='Relative to the original STEP10 load_only13-target task, only regularization.alpha5e-7->2.5e-7 and four explanatory experiment metadata fields change; all remaining task fields are exact. Numerical settings change only controllerclock14400s')
        sys.path.insert(0, str(ROOT/'hf_repo/src'))
        from hf_eval import native_evaluate
        from hf_eval.displacement import DisplacementSettings
        from hf_eval.tmc import TMCError
        TMCErrorClass = TMCError
        assert Path(native_evaluate.__file__).resolve() == ROOT/'hf_repo/src/hf_eval/native_evaluate.py'
        original_solve = native_evaluate.solve_native_mean

        def solve(*values, **keywords):
            calls['solve_started'] += 1
            previous_callback = keywords.get('on_accept')

            def accepted(snapshot):
                record = snapshot.record
                fields = ('d', 'R_input', 'q_in', 'q_out', 'relative_residual', 'constraint_residual',
                    'constraint_bound', 'minimum_J', 'relative_global_force_balance', 'newton_checks',
                    'bisection_depth', 'state_sha256', 'leg', 'original_target_index', 'is_original_target')
                row = {key:record[key] for key in fields}
                row.update(index=receipt['accepted_states'], elapsed_seconds=perf_counter()-STARTED,
                           cached_workpiece=deepcopy(record['workpiece']))
                with progress.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(row, allow_nan=False)+'\n')
                receipt['accepted_states'] += 1
                if previous_callback is not None:
                    previous_callback(snapshot)
                checkpoint('accepted_state')

            keywords['on_accept'] = accepted
            result = original_solve(*values, **keywords)
            calls['solve_completed'] += 1
            rows = [snapshot.record for snapshot in result.accepted]
            minimum_J = min((float(snapshot.arrays['J'].min()) for snapshot in result.accepted), default=None)
            fixed = max((abs(fsum((float(snapshot.state.lift[i]), float(snapshot.state.fluctuation[i]))))
                for snapshot in result.accepted for i in result.project.model.fixed_dofs), default=0.)
            cached = dict(actual_accepted_states=len(rows), minimum_J=minimum_J,
                maximum_fixed_split_sum_mm=fixed,
                maximum_relative_residual=max((row['relative_residual'] for row in rows), default=0.),
                native_constraint_bound_pass=all(abs(row['constraint_residual']) <= row['constraint_bound'] for row in rows),
                maximum_relative_global_force_balance=max((row['relative_global_force_balance'] for row in rows), default=0.))
            gates = protocol['gates']
            cached['passed'] = bool(rows) and minimum_J > 0 and cached['maximum_relative_residual'] <= float(gates['production_residual']) and cached['native_constraint_bound_pass'] and cached['maximum_relative_global_force_balance'] <= float(gates['global_force_balance']) and fixed <= float(gates['fixed_displacement_mm'])
            receipt.update(cached_production_gates=cached, production_call_counts=deepcopy(result.metadata['call_counts']),
                           actual_settings=deepcopy(result.metadata['settings']))
            return result

        phase = 'production'
        native_evaluate.solve_native_mean = solve
        try:
            checkpoint()
            calls['api_started'] += 1
            response = native_evaluate.evaluate_native(geometry_file, task_file, production, repo_root=ROOT,
                targets=protocol['targets_mm'], settings=DisplacementSettings(**protocol['settings']), **protocol['options'])
            calls['api_completed'] += 1
        finally:
            native_evaluate.solve_native_mean = original_solve
        receipt.update(response_status=response['status'], API_failure=deepcopy(response.get('failure')))
        if response['status'] != 'success':
            raise RuntimeError('Original API non-success; actual typed partial retained, no display')
        assert receipt['cached_production_gates']['passed']
        result_file = production/'result.json'
        saved = read(result_file)
        N = saved['accepted_states']
        assert N >= len(targets) and N == len(saved['states']) == receipt['accepted_states']
        assert saved['status'] == 'success' and saved['path_kind'] == 'load_only' and saved['path_completed']
        assert saved['unload_endpoint_reached'] is None and saved['reached_displacement'] == 1.06
        assert saved['loading_peak_reached'] and saved['task_target_executed']
        assert saved['targets_mm'] == protocol['targets_mm'] and saved['target_origin'] == 0.
        assert saved['settings'] == receipt['actual_settings'] == protocol['settings'] and 'continuation' not in saved
        originals = [row for row in saved['states'] if row['is_original_target']]
        assert [row['original_target_index'] for row in originals] == list(range(len(targets)))
        assert [row['d'] for row in originals] == protocol['targets_mm']
        assert [row['leg'] for row in originals] == ['origin'] + ['loading']*(len(targets)-1)
        assert all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
        assert all(calls[kind+suffix] == 1 for kind in ('api', 'solve') for suffix in ('_started', '_completed'))
        assert saved['call_counts'] == receipt['production_call_counts']
        assert saved['call_counts']['solver_invocations'] == 1
        assert saved['call_counts']['HP_calls'] == saved['call_counts']['JIT_calls'] == 0
        for key, value in protocol['options'].items():
            assert response['invocation'][key] == value
        checkpoint()

        phase = 'viewer_binding'
        display_started = perf_counter()
        display_deadline = min(display_started+protocol['viewer_seconds'], STARTED+protocol['helper_seconds'])

        def display_checkpoint(event='resource_check'):
            checkpoint(event)
            if perf_counter() > display_deadline:
                raise RuntimeError('Shared saved-display elapsed limit')

        viewer_pins = dict(protocol['pure_view_bindings'])
        assert all(protocol['source_bindings'][name] == pin for name, pin in viewer_pins.items())

        def bind_plain(path, expected=None):
            display_checkpoint()
            pin = digest(path)
            assert expected is None or pin == expected
            viewer_pins[path.relative_to(ROOT).as_posix()] = pin

        def bind_payload(path, expected):
            # Identity declared by the original producer; the clean viewer checks/decode it once.
            display_checkpoint()
            assert len(expected) == 64 and path.stat().st_size > 0
            viewer_pins[path.relative_to(ROOT).as_posix()] = expected

        bind_plain(result_file)
        model_file = production/saved['model']['descriptor_path']
        bind_plain(model_file, saved['model']['descriptor_file_sha256'])
        model = read(model_file)
        bind_payload(model_file.parent/model['arrays']['path'], model['arrays']['sha256'])
        for row in saved['states']:
            bind_plain(production/row['descriptor_path'], row['descriptor_file_sha256'])
            for key in ('state', 'forces'):
                bind_payload(production/row[key]['path'], row[key]['sha256'])
        view_protocol = run/'view_protocol.json'
        write(view_protocol, dict(bindings=viewer_pins, scope='New-alpha actual accepted cache only; no old-alpha reference or physics qualification transfer'))
        remaining = display_deadline-perf_counter()
        assert remaining > 0
        phase = 'viewer'
        child_once([sys.executable, '-X', 'utf8', '-B', str(ROOT/protocol['viewer_source']),
            '--repo', str(ROOT/'hf_repo'), '--protocol', str(view_protocol), '--output', str(view),
            '--case', LABEL+'='+str(production), '--stop-file', str(stop), '--time-limit', str(remaining)], remaining)
        views, summary = read(view/'view.json'), read(view/LABEL/'summary.json')
        assert views['status'] == 'pass' and len(views['cases']) == 1
        for key in ('geometry_started', 'geometry_completed', 'nodal_started', 'nodal_completed',
                    'boundary_started', 'boundary_completed', 'region_started', 'region_completed'):
            assert views[key] == N
        assert views['new_F_T_model_solver_HP_calls'] == 0 and views['mechanical_hooks_monitored'] is False
        assert views['contact_pressure_clamping_qualified'] is False
        assert views['cases'][0]['saved_accepted_states'] == N and not views['cases'][0]['reference_available']
        assert views['cases'][0]['unload_endpoint_reached'] is None
        assert {path.relative_to(view).as_posix() for path in view.rglob('*.png')} == {'comparison.png', 'distances_forces.png', 'peak_fields.png', 'right_medium.png'}
        assert LABEL+'/actual_states.gif' in views['outputs']
        assert views['archives_decoded'] == 1+2*N and views['fields_decoded'] == 27+18*N
        assert views.get('right_medium') is not None and summary.get('right_medium') is not None
        receipt['right_medium_view_metadata'] = deepcopy(views['right_medium'])
        receipt['right_medium_summary'] = deepcopy(summary['right_medium'])
        rows = summary['rows']
        assert len(rows) == N
        for ordinal, (row, state) in enumerate(zip(rows, saved['states'])):
            assert (row['index'], row['original_target_index'], row['leg'], row['d_mm'], row['state_sha256']) == (
                ordinal, state['original_target_index'], state['leg'], state['d'], state['state_sha256'])
            assert row['R_input_N'] == state['R_input'] and row['q_out_mm'] == state['q_out']
        receipt.update(view_actual_counts={key:views[key] for key in
            ('geometry_started', 'geometry_completed', 'nodal_started', 'nodal_completed',
             'boundary_started', 'boundary_completed', 'region_started', 'region_completed',
             'archives_decoded', 'fields_decoded')}, actual_view_PNGs=4, actual_GIF_frames=N,
            GIF_frame_count_basis='Successful clean viewer checks actual GIF frame count against N accepted states')
        display_checkpoint()
        phase = 'convergence'
        spec = importlib.util.spec_from_file_location('_circle_alpha_convergence', ROOT/protocol['convergence_source'])
        convergence = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(convergence)
        calls['convergence_plot_started'] += 1
        receipt['convergence'] = convergence.plot_convergence(result_file, run/'convergence', display_checkpoint, label=LABEL)
        calls['convergence_plot_completed'] += 1
        assert receipt['convergence']['mechanics_re_evaluated'] is False
        assert receipt['convergence']['source_result_sha256'] == digest(result_file)
        assert receipt['convergence']['source_status'] == saved['status']
        for event in ('convergence_read_started', 'convergence_read_completed', 'convergence_plot_started',
                      'convergence_plot_completed', 'convergence_written'):
            assert events[event] == 1
        display_checkpoint()
        phase = 'alpha_comparison'
        spec = importlib.util.spec_from_file_location('_circle_alpha_comparison', ROOT/protocol['comparison_source'])
        comparison = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(comparison)
        convergence_report = read(run/'convergence/convergence.json')
        calls['alpha_comparison_started'] += 1
        receipt['alpha_comparison'] = comparison.render(baseline, summary, convergence_report,
            run/'alpha_comparison', ROOT, display_checkpoint)
        calls['alpha_comparison_completed'] += 1
        assert receipt['alpha_comparison'] == dict(status='pass', baseline_rows=13, new_rows=N,
            matched_pairs=13, outputs=['comparison.png','comparison.json','REVIEW.md'])
        assert {path.name for path in (run/'alpha_comparison').iterdir() if path.is_file()} == {
            'comparison.png','comparison.json','REVIEW.md'}
        assert all(calls['alpha_comparison'+suffix] == 1 for suffix in ('_started','_completed'))
        receipt['alpha_comparison_source'] = dict(path=protocol['baseline_file'],
            sha256=protocol['input_bindings'][protocol['baseline_file']], original_alpha=5e-7,
            new_alpha=2.5e-7, scope='Same-definition raw target values and differences only; no old HP transfer or parameter-convergence gate')
        display_checkpoint()
        phase = 'table_and_review'
        write(run/'state_table.json', dict(card=CARD, source_result=str(result_file.relative_to(ROOT)),
            source_summary=str((view/LABEL/'summary.json').relative_to(ROOT)), rows=rows,
            comparison='alpha_comparison/comparison.json', alpha=2.5e-7,
            scope='Exact saved-viewer rows including original internal bisections; parameter differences descriptive only, no qualification transfer'))
        table = ['|index|leg|d (mm)|R input (N)|q out (mm)|body Fy total (N)|minimum Q1 boundary distance (mm)|',
                 '|---:|---|---:|---:|---:|---:|---:|']
        for row in rows:
            table.append('|'+ '|'.join(str(row[key]) for key in ('index', 'leg', 'd_mm', 'R_input_N',
                'q_out_mm', 'total_body_Fy_N', 'minimum_boundary_distance_mm'))+'|')
        text = ('# Alpha2.5e-7 circular workpiece: saved-state review\n\n'
            'Zero-start alpha2.5e-7 experiment relative to the original alpha5e-7 STEP10 physical task: lower-half wave mechanism, fixed raster circle r9 at (80,40) mm, on the92x40mm reference domain with Lr80mm. Only alpha, four experiment metadata fields and the separate14400s controller clock change. Coordinates x1; '
            'full-structure views and GIF use a visual symmetry mirror, while numerical tables retain '
            'the original lower-half values. All actual accepted states are shown, including controller bisections.\n\n'
            'The boundary distance is unsigned between exposed Q1 edges; boundary intersection/near-touch '
            'and region overlap are separate observations. Containment is not tested. Weak-form body total '
            'includes material and Hu contributions; it is not qualified contact pressure or effective grip. '
            'Right-medium observations use the dynamically selected resident reference cells x89..92 (six columns,480cells) and the actual displaced x92 boundary; the tip is selected by reference(80,30), not an old node ID. No new archive reads or domain-width convergence claim. '
            'Input zero-start loading0->1.06mm at alpha2.5e-7 is a new case and does not qualify unloading, release, stability, '
            'independent HP, alpha convergence or HF5 qualification. The original13 absolute targets and original residual/mean/fixed/J/global-balance gates remain. The alpha5e-7 baseline is the13 origin/loading target rows from PATH1; new controller bisections remain in the new history and do not create interpolated pairs. Values and differences are descriptive, signed lower-half weak resultants, not contact pressure.\n\n'
            '[Response](wave_circle_tip_alpha1/response.json) · [Result](wave_circle_tip_alpha1/result.json) · '
            '[Exact rows](state_table.json) · [Viewer summary](view/wave_circle_tip_alpha1/summary.json) · '
            '[Convergence JSON](convergence/convergence.json) · [Alpha raw values and differences](alpha_comparison/comparison.json) · [Alpha comparison review](alpha_comparison/REVIEW.md)\n\n'
            '![Actual states](view/wave_circle_tip_alpha1/actual_states.gif)\n\n'
            '![Response](view/comparison.png)\n\n![Boundary and forces](view/distances_forces.png)\n\n'
            '![Peak fields](view/peak_fields.png)\n\n![Right medium](view/right_medium.png)\n\n![Actual convergence](convergence/convergence.png)\n\n![Alpha comparison](alpha_comparison/comparison.png)\n\n'
            + '\n'.join(table)+'\n')
        (run/'REVIEW.md').write_text(text, encoding='utf-8', newline='\n')
        events['table_written'] += 1
        events['review_written'] += 1
        display_checkpoint()
        actual_png_paths = {path.relative_to(run).as_posix() for path in run.rglob('*.png')}
        assert actual_png_paths == {'view/comparison.png','view/distances_forces.png',
            'view/peak_fields.png','view/right_medium.png','convergence/convergence.png',
            'alpha_comparison/comparison.png'}
        receipt.update(display_elapsed_seconds=perf_counter()-display_started,
                       shared_display_seconds=protocol['viewer_seconds'], state_table_rows=N,
                       actual_total_PNGs=len(actual_png_paths))
        phase = 'final_binding_and_seal'
        bindings()
        receipt['all_bindings_unchanged'] = True
        outputs = seal()
        seal_scope = 'complete_inside_original_helper_window'
        checkpoint()
        receipt['status'] = 'pass'
    except BaseException as error:
        receipt.update(status='not_pass', error=dict(phase=phase, exception_class=type(error).__name__,
            code=getattr(error, 'code', None), reason=str(error)))
        memory = process.memory_info()
        if not stop.exists() and perf_counter()-STARTED <= protocol['helper_seconds'] and memory.rss <= protocol['sampled_RSS_bytes']:
            try:
                outputs = seal()
                seal_scope = 'actual_partial_inside_original_helper_window'
            except BaseException:
                seal_scope = 'not_complete_before_resource_close'
    receipt.update(phase=phase, call_counts=dict(calls), events=dict(events), outputs=outputs,
        output_identity_seal=seal_scope, wrapper_binding_file_reads=dict(binding_reads),
        binding_read_scope='One unique old LF source-geometry NPZ only; streamed SHA passes counted, original API/model snapshot rereads delegated. No old model/state/media input or universal file-open hook',
        new_payload_view_binding_scope='Producer-declared SHA plus stat only before viewer; final new-output seal streamed inside this original helper window',
        elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak,
        helper_seconds=protocol['helper_seconds'], sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()), completed_utc=datetime.now(timezone.utc).isoformat(),
        old_records_rewritten=False, new_mechanical_kernels=0, new_tests=0,
        forced_GC_calls=0, external_retries=0, source_bindings=protocol['source_bindings'])
    write(receipt_file, receipt)
    print(json.dumps(dict(status=receipt['status'], phase=phase, call_counts=dict(calls),
        accepted_states=receipt['accepted_states'], error=receipt.get('error'))), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('L-CTIPALPHA1 closed not_pass; no retry or following phase')


if __name__ == '__main__':
    main()
