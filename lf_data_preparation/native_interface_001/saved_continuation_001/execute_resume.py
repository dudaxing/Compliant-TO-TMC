"""Future M-RESUME1: focused tests, one saved-start segment, cached views.

This wrapper owns accounting and cooperative resource boundaries. The pinned
candidate owns all saved-input validation and the unchanged Newton policies.
"""
from time import perf_counter, sleep
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
from math import fsum
import argparse
import json
import os
import subprocess
import sys

STAGE = 'lf_data_preparation/native_interface_001/saved_continuation_001'
BASE = '01b5078acaf76fdaabfbdf214da9db16056467bc'
KINDS = ('focused_tests', 'api', 'model', 'solve', 'force', 'tangent', 'save', 'summary', 'view_child')
MECHANICAL = ('force_started', 'force_completed', 'tangent_started', 'tangent_completed')


def sha(path):
    value = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    root, protocol_file = args.repo.resolve(), args.protocol.resolve()
    stage, run = root / STAGE, root / STAGE / 'run_001'
    protocol = read(protocol_file)
    pins, limits = protocol['bindings'], protocol['phases']['production']
    parent_file = root / protocol['parent_result']
    parent, parent_model = read(parent_file), read(parent_file.parent / 'model/model.json')
    parent_protocol = read(root / protocol['parent_protocol'])
    selected = parent['states'][protocol['selected_state_index']]
    targets, options, settings = protocol['targets_mm'], protocol['options'], protocol['settings']
    assert protocol_file.parent == stage and protocol['card'] == 'M-RESUME1'
    assert protocol['source_baseline_commit'] == BASE and protocol['selected_state_index'] == 13
    assert targets == parent['targets_mm'][13:] == [1.2, 1.15]
    assert parent['status'] == 'failed' and parent['failure']['code'] == 'time_limit'
    assert selected['original_target_index'] == 13 and selected['leg'] == 'loading'
    assert selected['d'] == selected['physical_mean_target_mm'] == 1.2 and selected['target_origin'] == 0.0
    assert (options['response_mode'], options['tangent_mode'], options['initial_guess']) == ('mechanical', 'chunk256', 'port_projection')
    assert settings['time_limit_seconds'] == 1800.0
    assert {k:v for k,v in settings.items() if k != 'time_limit_seconds'} == {k:v for k,v in parent['settings'].items() if k != 'time_limit_seconds'}
    assert (limits['helper_seconds'], limits['outer_seconds'], protocol['focused_tests_seconds'], protocol['view_seconds']) == (2700, 2760, 120, 600)
    assert protocol['sampled_RSS_bytes'] == 8 * 1024**3
    assert protocol['gates'] == parent_protocol['gates']
    assert {name:float(value) for name, value in protocol['gates'].items()} == dict(
        production_residual=1e-9, average_constraint=1e-10,
        global_force_balance=1e-6, fixed_displacement_mm=8e-11)
    assert all(sha(root / name) == pin for name, pin in pins.items())
    authorization, reply = read(stage / 'author/authorization.json'), read(stage / 'author/direct_human_reply.json')
    proof_file = stage / 'author/M_RESUME1_source_publication_receipt.json'
    proof = read(proof_file)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert authorization['authorized'] is True and authorization['card'] == reply['card'] == 'M-RESUME1'
    assert authorization['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit'] == head
    assert authorization['protocol_sha256'] == sha(protocol_file)
    assert authorization['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert authorization['human_evidence_sha256'] == sha(stage / 'author/direct_human_reply.json')
    assert authorization['source_publication_receipt_sha256'] == sha(proof_file)
    assert reply['direct_human_answer'].strip() and reply['reply_context'] and authorization['direct_human_answer'] == reply['direct_human_answer']
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared_card'] == 'M-RESUME1'
    assert proof['prepared'] is True and proof['authorized'] is False and proof['executed'] is False
    assert not run.exists() and not (stage / 'stop_requested.txt').exists()
    run.mkdir()
    candidate, view = root / protocol['candidate_directory'], root / protocol['view_directory']
    assert candidate == run / 'resumed_alpha_half' and view == run / 'view'
    source = run / 'source/hf_repo'
    counts = {kind + suffix:0 for kind in KINDS for suffix in ('_started', '_completed')}
    receipt_file, progress = run / 'execution_receipt.json', run / 'accepted_progress.jsonl'
    receipt = dict(schema_version='saved-native-continuation-execution-1.0', status='running',
        protocol_sha256=sha(protocol_file), approved_source_commit=head,
        authorization_sha256=sha(stage / 'author/authorization.json'), human_evidence_sha256=authorization['human_evidence_sha256'],
        counts=counts, accepted_states=0, parent_result=protocol['parent_result'], selected_state_index=13,
        parent_status='failed', parent_full_path_completed=False, parent_unload_endpoint_reached=False,
        requested_absolute_targets_mm=targets, target_origin=0.0, initial_parameter=1.2,
        initial_K='None; fresh F/T anchor validation', saved_force_tangent_matrix_fields_decoded=False,
        HP_calls=0, JIT_calls=0, mechanical_hook_scope='Production native_mean force/tangent entries only; tests isolated, no general mechanical-hook claim',
        qualification_scope='Resumed segment production and saved observations only; no HP/pressure/clamp/stability/HF5 qualification')
    write(receipt_file, receipt)
    error, peak = None, 0
    try:
        import psutil
        process = psutil.Process()
        def checkpoint():
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
            if (stage / 'stop_requested.txt').exists():
                raise RuntimeError('external_stop_requested')
            if peak > protocol['sampled_RSS_bytes'] or perf_counter() - STARTED > limits['helper_seconds']:
                raise RuntimeError('whole_helper_resource_limit')

        def observed(delegate, kind):
            def call(*values, **keywords):
                checkpoint()
                counts[kind + '_started'] += 1
                before = tuple(counts[key] for key in MECHANICAL)
                try:
                    value = delegate(*values, **keywords)
                except BaseException:
                    checkpoint()
                    raise
                counts[kind + '_completed'] += 1
                if kind in ('save', 'summary'):
                    assert before == tuple(counts[key] for key in MECHANICAL)
                    receipt[kind + '_extra_force_tangent_calls'] = 0
                checkpoint()
                return value
            return call

        def child(argv, cwd, name, seconds, env=None):
            checkpoint()
            counts[name + '_started'] += 1
            start, child_stop = perf_counter(), None
            with (run / (name + '_stdout.log')).open('xb') as output:
                child_process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
                while child_process.poll() is None:
                    try:
                        checkpoint()
                        if perf_counter() - start > seconds:
                            raise RuntimeError(name + '_elapsed_limit')
                    except RuntimeError as exception:
                        child_stop = child_stop or str(exception)
                        if not (stage / 'stop_requested.txt').exists():
                            (stage / 'stop_requested.txt').write_text(child_stop, encoding='utf-8')
                    sleep(.1)  # Wait for the child's pinned cooperative checkpoints; no force.
            elapsed = perf_counter() - start
            if elapsed > seconds:
                child_stop = child_stop or name + '_elapsed_limit'
            receipt[name + '_terminal'] = dict(exit_code=child_process.returncode,
                elapsed_seconds=elapsed, stop_reason=child_stop,
                limit_seconds=seconds, cleanup='Waited for real child termination; no force')
            if child_process.returncode != 0 or child_stop is not None:
                raise RuntimeError(name + '_terminal_non_success')
            counts[name + '_completed'] += 1
            checkpoint()

        checkpoint()
        original_modules = {'src/hf_eval/' + path.name for path in (root / 'hf_repo/src/hf_eval').glob('*.py')}
        assert len(original_modules) == 51
        assert {name for name in protocol['source_package']['files'] if name.startswith('src/hf_eval/')} == original_modules | {'src/hf_eval/native_resume.py'}
        assert 'resume_focused_budget.py' in protocol['source_package']['files']
        package = {}
        for name, spec in protocol['source_package']['files'].items():
            destination = (source / name).resolve()
            destination.relative_to(source.resolve())
            assert spec['sha256'] == pins[spec['path']] == sha(root / spec['path'])
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as output:
                output.write((root / spec['path']).read_bytes())
            package[destination.relative_to(root).as_posix()] = sha(destination)
            assert package[destination.relative_to(root).as_posix()] == spec['sha256']
        receipt['executed_source_package_SHA256'] = package
        receipt['source_package_scope'] = 'Copied pinned original package plus reviewed overlay; formal hf_repo core unchanged. Result mechanics_source keys are package-relative labels; this receipt binds actual runtime paths.'
        test_env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg',
            HF_RESUME_SOURCE_ROOT=str(source), HF_RESUME_STAGE_STOP=str(stage / 'stop_requested.txt'),
            HF_RESUME_TEST_SECONDS='120', HF_RESUME_TEST_RECEIPT=str(run / 'focused_test_receipt.json'),
            HF_RESUME_TEST_NODEIDS=json.dumps(protocol['focused_test_nodeids']))
        child([sys.executable, '-B', '-m', 'pytest', '-q', '-x', '-p', 'resume_focused_budget', *protocol['focused_test_nodeids']],
            source, 'focused_tests', min(120, limits['helper_seconds'] - (perf_counter() - STARTED)), test_env)
        tests = read(run / 'focused_test_receipt.json')
        assert tests['status'] == 'pass' and tests['collected_nodeids'] == protocol['focused_test_nodeids']
        receipt['focused_test_receipt'] = (run / 'focused_test_receipt.json').relative_to(root).as_posix()
        sys.path.insert(0, str(source / 'src'))
        from hf_eval import native_evaluate, native_mean
        from hf_eval.displacement import DisplacementSettings
        assert Path(native_mean.__file__).resolve() == source / 'src/hf_eval/native_mean.py'
        assert Path(native_evaluate.__file__).resolve() == source / 'src/hf_eval/native_evaluate.py'
        native_mean._assemble_mechanical_force = observed(native_mean._assemble_mechanical_force, 'force')
        native_mean._tangent_chunked = observed(native_mean._tangent_chunked, 'tangent')
        original_model = native_mean.build_native_project
        def checked_model(*values, **keywords):
            project = original_model(*values, **keywords)
            assert project.task == parent_model['task'] and project.material == parent_model['material']
            assert {k:v for k,v in project.region_metadata.items() if k != 'source_geometry'} == parent_model['region_metadata']
            assert project.region_metadata['source_geometry'] == parent_model['source_geometry']
            assert counts['force_started'] == counts['tangent_started'] == 0
            receipt['same_model_task_BC_material_checked_before_first_force'] = True
            return project
        native_mean.build_native_project = observed(checked_model, 'model')
        native_evaluate.write_native_mean = observed(native_evaluate.write_native_mean, 'save')
        native_evaluate.summarize_saved_native_result = observed(native_evaluate.summarize_saved_native_result, 'summary')
        original_solve = native_evaluate.solve_native_mean
        def solve(*values, **keywords):
            def accepted(snapshot):
                row = {key:snapshot.record[key] for key in ('d', 'R_input', 'q_in', 'q_out',
                    'relative_residual', 'state_sha256', 'leg', 'original_target_index', 'is_original_target')}
                row.update(index=receipt['accepted_states'], elapsed_seconds=perf_counter() - STARTED)
                with progress.open('a', encoding='utf-8') as output:
                    output.write(json.dumps(row, allow_nan=False) + '\n')
                receipt['accepted_states'] += 1
                checkpoint()
            keywords['on_accept'] = accepted
            result = observed(original_solve, 'solve')(*values, **keywords)
            rows = [snapshot.record for snapshot in result.accepted]
            min_J = min((float(snapshot.arrays['J'].min()) for snapshot in result.accepted), default=None)
            fixed = max((abs(fsum((float(snapshot.state.lift[i]), float(snapshot.state.fluctuation[i]))))
                for snapshot in result.accepted for i in result.project.model.fixed_dofs), default=0.0)
            gates = protocol['gates']
            cached = dict(actual_accepted_states=len(rows), minimum_J=min_J,
                maximum_relative_residual=max((row['relative_residual'] for row in rows), default=0.0),
                maximum_abs_constraint_residual_mm=max((abs(row['constraint_residual']) for row in rows), default=0.0),
                native_constraint_bound_pass=all(abs(row['constraint_residual']) <= row['constraint_bound'] for row in rows),
                maximum_relative_global_force_balance=max((row['relative_global_force_balance'] for row in rows), default=0.0),
                maximum_fixed_split_sum_mm=fixed)
            cached['passed'] = bool(rows) and min_J > 0 and cached['maximum_relative_residual'] <= float(gates['production_residual']) and cached['native_constraint_bound_pass'] and cached['maximum_relative_global_force_balance'] <= float(gates['global_force_balance']) and fixed <= float(gates['fixed_displacement_mm'])
            receipt['cached_production_gates'] = cached
            return result  # Preserve ordinary typed controller failure for cached writer/API response.
        native_evaluate.solve_native_mean = solve
        response = observed(native_evaluate.evaluate_native, 'api')(None, None, candidate, repo_root=root,
            saved_result=parent_file, selected_state_index=13, targets=targets,
            settings=DisplacementSettings(**settings), **options)
        receipt['response_status'], receipt['API_failure'] = response['status'], response.get('failure')
        if response['status'] != 'success':
            raise RuntimeError('Saved-start API terminal non-success; existing partial result/typed response retained')
        result = read(candidate / 'result.json')
        N = result['accepted_states']
        assert 2 <= N <= 9 and N == len(result['states']) == receipt['accepted_states']
        assert result['status'] == 'success' and result['path_completed'] and result['unload_endpoint_reached']
        assert result['targets_mm'] == targets and result['target_origin'] == 0.0 and result['task_target_executed'] is False
        assert result['task_sha256'] == parent['task_sha256'] and result['settings'] == settings
        continuation = result['continuation']
        assert response['continuation'] == continuation
        assert continuation['parent_status'] == parent['status'] and continuation['parent_failure'] == parent['failure']
        assert continuation['parent_path_completed'] == parent['path_completed'] is False
        assert continuation['parent_task_target_executed'] == parent['task_target_executed'] is False
        assert continuation['parent_unload_endpoint_reached'] == parent['unload_endpoint_reached'] is False
        assert continuation['segment_completed'] and continuation['anchor_revalidated'] and continuation['anchor_identity_preserved']
        assert continuation['full_original_path_executed_by_child'] is False and result['full_original_path_completed'] is False
        assert result['task_target_executed'] is False and response['path']['full_original_path_completed'] is False
        assert continuation['original_target_indices'] == [13, 14]
        assert continuation['selected_state']['state_sha256'] == selected['state_sha256']
        assert (continuation['selected_state']['accepted_index'], continuation['selected_state']['original_target_index'],
            continuation['selected_state']['R_input_N'], continuation['selected_state']['d_mm']) == (13, 13, selected['R_input'], 1.2)
        originals = [row for row in result['states'] if row['is_original_target']]
        assert [row['original_target_index'] for row in originals] == [13, 14]
        assert [row['d'] for row in originals] == targets and originals[0]['state_sha256'] == selected['state_sha256']
        assert originals[0]['leg'] == 'resume_origin' and originals[1]['leg'] == 'unloading'
        assert [row['child_original_target_index'] for row in originals] == [0, 1]
        assert originals[0]['continuation_anchor'] is True and originals[1]['continuation_anchor'] is False
        assert receipt['cached_production_gates']['passed'] and all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
        assert all(counts[kind + suffix] == 1 for kind in ('api', 'model', 'solve', 'save', 'summary') for suffix in ('_started', '_completed'))
        for kind in ('force', 'tangent'):
            assert counts[kind + '_started'] == result['call_counts'][kind + '_calls']
            assert counts[kind + '_completed'] == result['call_counts'][kind + '_calls_completed']
        assert result['call_counts']['HP_calls'] == result['call_counts']['JIT_calls'] == 0
        receipt['call_counts'] = result['call_counts']
        checkpoint()
        viewer_pins = dict(protocol['pure_view_bindings'])
        assert all(pins[name] == pin for name, pin in viewer_pins.items())
        def bind_new(path, expected=None):
            pin = sha(path)
            assert expected is None or pin == expected
            viewer_pins[path.relative_to(root).as_posix()] = pin
        bind_new(candidate / 'result.json')
        model_file = candidate / result['model']['descriptor_path']
        bind_new(model_file, result['model']['descriptor_file_sha256'])
        model = read(model_file)
        bind_new(model_file.parent / model['arrays']['path'], model['arrays']['sha256'])
        for row in result['states']:
            bind_new(candidate / row['descriptor_path'], row['descriptor_file_sha256'])
            for key in ('state', 'forces'):
                bind_new(candidate / row[key]['path'], row[key]['sha256'])
        view_protocol = run / 'view_protocol.json'
        write(view_protocol, dict(bindings=viewer_pins, scope='One new saved resumed segment; pure original sources; no independent reference'))
        remaining = min(600, limits['helper_seconds'] - (perf_counter() - STARTED))
        child([sys.executable, '-B', str(root / protocol['viewer_source']), '--repo', str(root / 'hf_repo'),
            '--protocol', str(view_protocol), '--output', str(view), '--case', 'resumed_alpha_half=' + str(candidate),
            '--stop-file', str(stage / 'stop_requested.txt'), '--time-limit', str(remaining)], root, 'view_child', remaining)
        views = read(view / 'view.json')
        assert views['status'] == 'pass' and all(views[name] == N for name in ('geometry_started', 'geometry_completed', 'nodal_started', 'nodal_completed'))
        assert views['new_F_T_model_solver_HP_calls'] == 0 and views['mechanical_hooks_monitored'] is False
        assert views['contact_pressure_clamping_qualified'] is False and len(views['cases']) == 1
        assert views['cases'][0]['reference_available'] is False and views['cases'][0]['saved_accepted_states'] == N
        assert {p.relative_to(view).as_posix() for p in view.rglob('*.png')} == {'comparison.png', 'distances_forces.png', 'peak_fields.png'}
        assert (view / 'resumed_alpha_half/actual_states.gif').exists()
        receipt.update(view_actual_counts={name:views[name] for name in ('geometry_started', 'geometry_completed', 'nodal_started', 'nodal_completed')},
            view_NPZ_files=1 + 2 * N, view_decoded_fields=27 + 18 * N, actual_PNGs=3, actual_GIF_frames=N,
            production_selected_NPZ_files=2, production_selected_fields=6, source_pure_scope_separated=True,
            original_parent_full_path_still_NOT_PASS=True, new_HP_pressure_clamp_stability_HF5_qualified=False)
    except BaseException as exception:
        error = exception
        receipt['exception'] = dict(exception_class=type(exception).__name__, code=getattr(exception, 'code', None), reason=str(exception))
    finally:
        try:
            receipt['outputs'] = {path.relative_to(root).as_posix():sha(path) for path in run.rglob('*') if path.is_file() and path != receipt_file}
            receipt['all_bindings_unchanged'] = all(sha(root / name) == pin for name, pin in pins.items())
            assert receipt['all_bindings_unchanged']
            if 'executed_source_package_SHA256' in receipt:
                receipt['executed_source_package_unchanged'] = all(sha(root / name) == pin
                    for name, pin in receipt['executed_source_package_SHA256'].items())
                assert receipt['executed_source_package_unchanged']
            if 'checkpoint' in locals():
                checkpoint()
        except BaseException as exception:
            receipt['finalization_exception'] = dict(exception_class=type(exception).__name__, reason=str(exception))
            error = error or exception
        receipt.update(status='pass' if error is None else 'not_pass', elapsed_seconds=perf_counter() - STARTED,
            peak_sampled_RSS_bytes=peak, elapsed_scope='Imports, source copy, focused tests, one API, persistence, summary, pure child and final hashing; before receipt write, outer includes full exit')
        write(receipt_file, receipt)
        if error is None:
            checkpoint()  # A provisional pass receipt cannot turn a late nonzero helper/outer into success.
        print(json.dumps({k:receipt[k] for k in ('status', 'accepted_states', 'elapsed_seconds', 'peak_sampled_RSS_bytes')}), flush=True)
    if error is not None:
        raise error


if __name__ == '__main__':
    main()
