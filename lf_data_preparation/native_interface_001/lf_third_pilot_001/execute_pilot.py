"""One authorized third-design pilot, cached observations and convergence view."""
from time import perf_counter, sleep
STARTED = perf_counter()
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from math import fsum
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

REL = 'lf_data_preparation/native_interface_001/lf_third_pilot_001'
CARD = 'L-PILOT1'
LABEL = 'lf_third_pilot'
KINDS = ('test_child', 'api', 'model', 'solve', 'force', 'tangent', 'save', 'summary',
         'view_child', 'convergence_plot')
MECHANICAL = ('force_started', 'force_completed', 'tangent_started', 'tangent_completed')


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def sha(path, checkpoint=lambda: None):
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            checkpoint()
            digest.update(block)
    checkpoint()
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    stage, run = root/REL, root/REL/'run_001'
    protocol_file = (root/args.protocol).resolve()
    protocol = read(protocol_file)
    auth_file = stage/'author/authorization.json'
    auth = read(auth_file)
    assert protocol_file.parent == stage and protocol['card'] == auth['card'] == CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['protocol_sha256'] == sha(protocol_file)
    assert auth['source_baseline_commit'] == protocol['source_baseline_commit']
    assert (protocol['test_seconds'], protocol['controller_seconds'], protocol['view_seconds'],
            protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (60, 1800, 600, 2700, 2760, 8*1024**3)
    assert not run.exists() and not (stage/'stop_requested.txt').exists()
    run.mkdir()
    source = root/'hf_repo'
    production, view = root/protocol['candidate_directory'], root/protocol['view_directory']
    assert production == run/LABEL and view == run/'view'
    counts = {kind+suffix: 0 for kind in KINDS for suffix in ('_started', '_completed')}
    events = Counter()
    pins = protocol['source_bindings']
    receipt_file = run/'execution_receipt.json'
    progress = run/'accepted_progress.jsonl'
    receipt = dict(card=CARD, status='running', protocol_sha256=auth['protocol_sha256'],
        authorization_sha256=sha(auth_file), source_baseline_commit=auth['source_baseline_commit'],
        new_sources_pinned_individually=True, counts=counts, accepted_states=0,
        requested_absolute_targets_mm=protocol['targets_mm'], zero_start=True,
        saved_parent_or_state_used=False, extend_path=False, HP_calls=0, JIT_calls=0,
        candidate_copies=0, default_installations_by_wrapper=0,
        mechanical_hooks_monitored=False, mechanical_hook_scope='Production NativeMean aliases only; toy tests and pure viewer are separate child processes',
        qualification_scope='Independent third-design load-only 0/.25/.50 pilot; no original25 path, independent HP, pressure, effective clamp, release, stability or HF5 qualification')
    write(receipt_file, receipt)
    error, peak, phase, TMCErrorClass = None, 0, 'bootstrap', None
    try:
        import psutil
        process = psutil.Process()

        def checkpoint(event=None):
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
            reason = ('external_stop_requested' if (stage/'stop_requested.txt').exists() else
                'sampled_RSS_limit' if peak > protocol['sampled_RSS_bytes'] else
                'whole_helper_elapsed_limit' if perf_counter()-STARTED > protocol['helper_seconds'] else None)
            if reason:
                receipt['resource_stop_reason'] = reason
                if TMCErrorClass is not None:
                    raise TMCErrorClass(reason, code='time_limit')
                raise RuntimeError(reason)
            if event is not None:
                events[event] += 1

        def observed(delegate, kind):
            def call(*values, **keywords):
                checkpoint()
                counts[kind+'_started'] += 1
                before = tuple(counts[key] for key in MECHANICAL)
                value = delegate(*values, **keywords)
                counts[kind+'_completed'] += 1
                if kind in ('save', 'summary', 'convergence_plot'):
                    assert before == tuple(counts[key] for key in MECHANICAL)
                    receipt[kind+'_extra_force_tangent_calls'] = 0
                checkpoint()
                return value
            return call

        def child_once(argv, cwd, log, limit, kind):
            checkpoint()
            counts[kind+'_started'] += 1
            started = perf_counter()
            child_stop = child_error = None
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg')
            with log.open('xb') as output:
                child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
                try:
                    while child.poll() is None:
                        try:
                            checkpoint()
                            if perf_counter()-started > limit:
                                raise RuntimeError(kind+'_elapsed_limit')
                        except Exception as exception:
                            child_stop = child_stop or str(exception)
                            if not (stage/'stop_requested.txt').exists():
                                (stage/'stop_requested.txt').write_text(child_stop, encoding='utf-8')
                        sleep(.1)
                except BaseException as exception:
                    child_error = exception
                    child_stop = child_stop or type(exception).__name__
                finally:
                    if child.poll() is None:
                        try:
                            if not (stage/'stop_requested.txt').exists():
                                (stage/'stop_requested.txt').write_text(child_stop or kind+'_interrupted', encoding='utf-8')
                        finally:
                            child.wait()
            elapsed = perf_counter()-started
            if elapsed > limit:
                child_stop = child_stop or kind+'_elapsed_limit'
            if (stage/'stop_requested.txt').exists():
                child_stop = child_stop or 'external_stop_requested'
            receipt[kind+'_terminal'] = dict(exit_code=child.returncode, elapsed_seconds=elapsed,
                limit_seconds=limit, stop_reason=child_stop,
                cleanup='Actual child waited; cooperative stop request, no force or hard-time-cap claim')
            if child_error is not None:
                raise child_error
            if child.returncode != 0 or child_stop is not None:
                raise RuntimeError(kind+' non-success; no retry or following stage')
            counts[kind+'_completed'] += 1
            checkpoint()

        checkpoint()
        assert all(sha(root/name, checkpoint) == pin for name, pin in pins.items())
        geometry_file, task_file = root/protocol['geometry_file'], root/protocol['task_file']
        manifest_file = root/protocol['input_manifest']
        manifest, task, original = read(manifest_file), read(task_file), read(root/protocol['original_task_file'])
        assert manifest['status'] == 'success' and manifest['data_only'] is True
        assert geometry_file == manifest_file.parent/manifest['outputs']['geometry_file']
        assert sha(geometry_file, checkpoint) == manifest['geometry']['descriptor_file_sha256']
        assert sha(root/protocol['original_task_file'], checkpoint) == manifest['bound_task_file_sha256']
        expected_task = deepcopy(original)
        expected_task['path'] = dict(kind='load_only', targets_mm=[0., .25, .5])
        expected_task['input']['target_mm'] = .5
        assert set(protocol['task_metadata']) == {'task_id', 'purpose', 'parameter_origin'}
        expected_task.update(protocol['task_metadata'])
        assert task == expected_task
        assert protocol['targets_mm'] == task['path']['targets_mm'] == [0., .25, .5]
        assert original['path']['kind'] == 'ordered_cycle' and len(original['path']['targets_mm']) == 25
        assert original['input']['target_mm'] == 1.2
        old_settings = read(root/protocol['settings_source_result'])['settings']
        assert protocol['settings']['time_limit_seconds'] == 1800.
        assert {k:v for k,v in protocol['settings'].items() if k != 'time_limit_seconds'} == {
            k:v for k,v in old_settings.items() if k != 'time_limit_seconds'}
        assert protocol['gates'] == read(root/protocol['gates_source_protocol'])['gates']
        assert protocol['options'] == dict(response_mode='mechanical', tangent_mode='chunk256', initial_guess='port_projection')
        receipt.update(input_manifest_sha256=sha(manifest_file, checkpoint),
            pilot_task_file_sha256=sha(task_file, checkpoint), original25_task_sha256=manifest['bound_task_sha256'],
            task_scope='New independent load_only .5 task; original25 task retained as input provenance, not completed or continued')
        phase = 'tests'
        child_once([sys.executable, '-X', 'utf8', '-B']+protocol['tests_argv'], source,
                   run/'tests_stdout.log', protocol['test_seconds'], 'test_child')
        receipt['tests_scope'] = 'Three selected one-cell synthetic controller methods; not third-gripper production or HP'

        sys.path.insert(0, str(source/'src'))
        from hf_eval import native_evaluate, native_mean
        from hf_eval.data import canonical_hash
        from hf_eval.displacement import DisplacementSettings
        from hf_eval.tmc import TMCError
        TMCErrorClass = TMCError
        assert Path(native_evaluate.__file__).resolve() == source/'src/hf_eval/native_evaluate.py'
        assert Path(native_mean.__file__).resolve() == source/'src/hf_eval/native_mean.py'
        assert canonical_hash(task) == protocol['task_sha256']
        native_mean._assemble_mechanical_force = observed(native_mean._assemble_mechanical_force, 'force')
        native_mean._tangent_chunked = observed(native_mean._tangent_chunked, 'tangent')
        native_mean.build_native_project = observed(native_mean.build_native_project, 'model')
        native_evaluate.write_native_mean = observed(native_evaluate.write_native_mean, 'save')
        native_evaluate.summarize_saved_native_result = observed(native_evaluate.summarize_saved_native_result, 'summary')
        original_solve = native_evaluate.solve_native_mean

        def solve(*values, **keywords):
            def accepted(snapshot):
                fields = ('d', 'R_input', 'q_in', 'q_out', 'relative_residual', 'constraint_residual',
                    'constraint_bound', 'minimum_J', 'relative_global_force_balance', 'newton_checks',
                    'bisection_depth', 'state_sha256', 'leg', 'original_target_index', 'is_original_target')
                row = {key: snapshot.record[key] for key in fields}
                row.update(index=receipt['accepted_states'], elapsed_seconds=perf_counter()-STARTED)
                with progress.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(row, allow_nan=False)+'\n')
                receipt['accepted_states'] += 1
                checkpoint()
            keywords['on_accept'] = accepted
            result = observed(original_solve, 'solve')(*values, **keywords)
            rows = [snapshot.record for snapshot in result.accepted]
            minimum_J = min((float(snapshot.arrays['J'].min()) for snapshot in result.accepted), default=None)
            fixed = max((abs(fsum((float(snapshot.state.lift[i]), float(snapshot.state.fluctuation[i]))))
                for snapshot in result.accepted for i in result.project.model.fixed_dofs), default=0.)
            cached = dict(actual_accepted_states=len(rows), minimum_J=minimum_J, maximum_fixed_split_sum_mm=fixed,
                maximum_relative_residual=max((row['relative_residual'] for row in rows), default=0.),
                native_constraint_bound_pass=all(abs(row['constraint_residual']) <= row['constraint_bound'] for row in rows),
                maximum_relative_global_force_balance=max((row['relative_global_force_balance'] for row in rows), default=0.))
            gates = protocol['gates']
            cached['passed'] = bool(rows) and minimum_J > 0 and cached['maximum_relative_residual'] <= float(gates['production_residual']) and cached['native_constraint_bound_pass'] and cached['maximum_relative_global_force_balance'] <= float(gates['global_force_balance']) and fixed <= float(gates['fixed_displacement_mm'])
            receipt['cached_production_gates'] = cached
            return result

        native_evaluate.solve_native_mean = solve
        phase = 'production'
        response = observed(native_evaluate.evaluate_native, 'api')(geometry_file, task_file, production,
            repo_root=root, settings=DisplacementSettings(**protocol['settings']), **protocol['options'])
        receipt.update(response_status=response['status'], API_failure=response.get('failure'))
        if response['status'] != 'success':
            raise RuntimeError('Pilot API non-success; actual typed partial retained, no viewer')
        result = read(production/'result.json')
        N = result['accepted_states']
        assert N >= 3 and N == len(result['states']) == receipt['accepted_states']
        assert result['status'] == 'success' and result['path_kind'] == 'load_only' and result['path_completed']
        assert result['unload_endpoint_reached'] is None and result['reached_displacement'] == .5
        assert result['loading_peak_reached'] and result['task_target_executed']
        assert result['targets_mm'] == protocol['targets_mm'] and result['target_origin'] == 0.
        assert result['settings'] == protocol['settings'] and 'continuation' not in result
        for key in ('response_mode', 'tangent_mode', 'initial_guess'):
            assert response['invocation'][key] == protocol['options'][key]
        originals = [row for row in result['states'] if row['is_original_target']]
        assert [row['original_target_index'] for row in originals] == [0, 1, 2]
        assert [row['d'] for row in originals] == protocol['targets_mm']
        assert [row['leg'] for row in originals] == ['origin', 'loading', 'loading']
        assert receipt['cached_production_gates']['passed']
        assert all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
        assert all(counts[kind+suffix] == 1 for kind in ('api', 'model', 'solve', 'save', 'summary')
                   for suffix in ('_started', '_completed'))
        for kind in ('force', 'tangent'):
            assert counts[kind+'_started'] == result['call_counts'][kind+'_calls']
            assert counts[kind+'_completed'] == result['call_counts'][kind+'_calls_completed']
        assert result['call_counts']['HP_calls'] == result['call_counts']['JIT_calls'] == 0
        receipt['call_counts'] = result['call_counts']
        receipt['production_imported_HF_modules'] = {name: str(Path(module.__file__).resolve())
            for name, module in tuple(sys.modules.items()) if name == 'hf_eval' or name.startswith('hf_eval.')}
        assert all(Path(path).is_relative_to(source/'src/hf_eval') for path in receipt['production_imported_HF_modules'].values())
        checkpoint()
        phase = 'viewer_binding'
        viewer_pins = dict(protocol['pure_view_bindings'])
        assert all(pins[name] == pin for name, pin in viewer_pins.items())

        def bind_new(path, expected=None):
            pin = sha(path, checkpoint)
            assert expected is None or expected == pin
            viewer_pins[path.relative_to(root).as_posix()] = pin

        bind_new(production/'result.json')
        model_file = production/result['model']['descriptor_path']
        bind_new(model_file, result['model']['descriptor_file_sha256'])
        saved_model = read(model_file)
        bind_new(model_file.parent/saved_model['arrays']['path'], saved_model['arrays']['sha256'])
        for row in result['states']:
            bind_new(production/row['descriptor_path'], row['descriptor_file_sha256'])
            for key in ('state', 'forces'):
                bind_new(production/row[key]['path'], row[key]['sha256'])
        view_protocol = run/'view_protocol.json'
        write(view_protocol, dict(bindings=viewer_pins, scope='New third-design load-only pilot; original pure viewer without reference'))
        remaining = min(protocol['view_seconds'], protocol['helper_seconds']-(perf_counter()-STARTED))
        checkpoint()
        assert remaining > 0
        phase = 'viewer'
        child_once([sys.executable, '-X', 'utf8', '-B', str(root/protocol['viewer_source']),
            '--repo', str(source), '--protocol', str(view_protocol), '--output', str(view),
            '--case', LABEL+'='+str(production), '--stop-file', str(stage/'stop_requested.txt'),
            '--time-limit', str(remaining)], root, run/'view_child_stdout.log', remaining, 'view_child')
        views = read(view/'view.json')
        assert views['status'] == 'pass' and all(views[key] == N for key in
            ('geometry_started', 'geometry_completed', 'nodal_started', 'nodal_completed'))
        assert views['new_F_T_model_solver_HP_calls'] == 0 and views['mechanical_hooks_monitored'] is False
        assert views['contact_pressure_clamping_qualified'] is False and len(views['cases']) == 1
        assert not views['cases'][0]['reference_available'] and views['cases'][0]['saved_accepted_states'] == N
        assert views['cases'][0]['unload_endpoint_reached'] is None
        assert {path.relative_to(view).as_posix() for path in view.rglob('*.png')} == {'comparison.png', 'distances_forces.png', 'peak_fields.png'}
        assert LABEL+'/actual_states.gif' in views['outputs']
        receipt.update(view_actual_counts={key: views[key] for key in
            ('geometry_started', 'geometry_completed', 'nodal_started', 'nodal_completed')},
            view_NPZ_files=1+2*N, view_decoded_fields=27+18*N, actual_view_PNGs=3, actual_GIF_frames=N,
            GIF_frame_count_basis='Original successful viewer checks GIF n_frames against actual accepted rows',
            production_input_NPZ_files=1, production_input_fields=4, old_records_rewritten=False)
        phase = 'convergence'
        module_spec = importlib.util.spec_from_file_location('_third_pilot_convergence', root/protocol['convergence_source'])
        convergence = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(convergence)
        receipt['convergence'] = observed(convergence.plot_convergence, 'convergence_plot')(
            production/'result.json', run/'convergence', checkpoint)
        assert receipt['convergence']['mechanics_re_evaluated'] is False
        assert receipt['convergence']['source_result_sha256'] == sha(production/'result.json', checkpoint)
        assert receipt['convergence']['source_status'] == result['status']
        assert {path.name for path in (run/'convergence').iterdir()} == {'convergence.json', 'convergence.png'}
        for event in ('convergence_read_started', 'convergence_read_completed',
                      'convergence_plot_started', 'convergence_plot_completed', 'convergence_written'):
            assert events[event] == 1
    except BaseException as exception:
        error = exception
        receipt['exception'] = dict(phase=phase, exception_class=type(exception).__name__,
            code=getattr(exception, 'code', None), reason=str(exception))
    finally:
        receipt['last_scientific_or_display_phase'] = phase
        phase = 'closure'
        try:
            checkpoint()
            receipt['outputs'] = {}
            for path in run.rglob('*'):
                if path.is_file() and path != receipt_file:
                    receipt['outputs'][path.relative_to(root).as_posix()] = dict(
                        sha256=sha(path, checkpoint), bytes=path.stat().st_size)
            receipt['all_bindings_unchanged'] = all(sha(root/name, checkpoint) == pin for name, pin in pins.items())
            assert receipt['all_bindings_unchanged']
            checkpoint()
            receipt['output_identity_seal'] = 'complete_inside_original_helper_window'
        except BaseException as exception:
            receipt['output_identity_seal'] = 'incomplete_or_skipped; no closed-window hash retry'
            receipt['closure_exception'] = dict(exception_class=type(exception).__name__, reason=str(exception))
            error = error or exception
        receipt.update(status='pass' if error is None else 'not_pass', events=dict(events),
            elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=peak,
            elapsed_scope='Earliest helper clock: pins/tests/imports/one API/cache-save/pure viewer/convergence/seal; before receipt write')
        write(receipt_file, receipt)
        try:
            if error is None:
                checkpoint()
        except BaseException as exception:
            error = exception
            receipt.update(status='not_pass', final_write_stop=str(exception), elapsed_seconds=perf_counter()-STARTED)
            write(receipt_file, receipt)
        print(json.dumps({key: receipt[key] for key in ('status', 'accepted_states', 'elapsed_seconds', 'peak_sampled_RSS_bytes')}), flush=True)
    if error is not None:
        raise error


if __name__ == '__main__':
    main()
