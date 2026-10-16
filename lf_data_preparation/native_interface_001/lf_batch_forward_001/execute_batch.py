"""Run one native batch, observe its accepted cache, then display saved results."""
from time import perf_counter, monotonic
STARTED = perf_counter()
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from math import fsum
import importlib.util
import json
from pathlib import Path
import sys
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
CARD = 'L-BFWD1'


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


def main():
    protocol_file = STAGE / 'protocol.json'
    protocol = read(protocol_file)
    auth_file = STAGE / 'author/authorization.json'
    auth = read(auth_file)
    assert protocol['card'] == auth['card'] == CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is auth['one_invocation'] is True
    assert auth['direct_human_answer'] == '批准按 L-BFWD1 卡实施并执行'
    assert auth['protocol_sha256'] == sha256(protocol_file.read_bytes()).hexdigest()
    assert auth['authorized_execution_source_commit'] == protocol['source_baseline_commit']
    assert (protocol['controller_seconds_per_case'], protocol['viewer_seconds'],
            protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (1800, 600, 4500, 4560, 8*1024**3)
    run = ROOT / protocol['output_directory']
    stop = STAGE / 'stop_requested.txt'
    assert not run.exists() and not stop.exists()
    run.mkdir(parents=True, exist_ok=False)
    receipt_file = run / 'execution_receipt.json'
    progress = run / 'accepted_progress.jsonl'
    calls, events, binding_reads = Counter(), Counter(), Counter()
    cases = {}
    process, peak, TMCErrorClass = psutil.Process(), 0, None
    phase, outputs, seal_scope = 'bootstrap', {}, 'not_complete'
    receipt = dict(card=CARD, status='running', protocol_sha256=auth['protocol_sha256'],
        authorization_sha256=sha256(auth_file.read_bytes()).hexdigest(),
        source_baseline_commit=protocol['source_baseline_commit'],
        new_sources_pinned_individually=True, accepted_progress_rows=0,
        zero_start=True, saved_parent_or_state_used=False, extend_path=False,
        new_tests=0, default_installations=0, HP_calls_by_wrapper=0,
        mechanical_hooks_monitored=False,
        mechanical_hook_scope='Only original batch evaluate alias and API solve/on_accept observed; F/T counts come from original returned cache metadata, not universal hooks',
        result_objects_retained_by_observer=False,
        qualification_scope='Only two new0/.25/.50 load-only batch paths; no original25 cycle, HP, pressure, effective clamp, release, stability, labels, ranking or HF5 qualification')

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
        checkpoint()
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

    write(receipt_file, receipt)
    try:
        checkpoint()
        phase = 'bindings_and_task_contract'
        bindings()
        manifest_file = ROOT / protocol['manifest_file']
        manifest = read(manifest_file)
        assert manifest['schema_version'] == 'hf-native-batch-manifest-1.0'
        assert len(manifest['cases']) == len(protocol['original_task_files']) == 2
        assert [case['label'] for case in manifest['cases']] == ['gripper_native_fine', 'gripper_wave_fine']
        assert manifest['options'] == dict(protocol['options'], settings=protocol['settings'])
        assert protocol['options'] == dict(response_mode='mechanical', tangent_mode='chunk256', initial_guess='port_projection')
        assert protocol['settings']['time_limit_seconds'] == 1800.
        assert protocol['settings']['constraint_tolerance'] == float(protocol['gates']['average_constraint'])
        assert protocol['targets_mm'] == [0., .25, .5]
        assert set(protocol['task_metadata']) == {'task_id', 'purpose', 'parameter_origin', 'description'}
        assert protocol['gates'] == read(ROOT/protocol['gates_source_protocol'])['gates']
        outputs_to_labels = {}
        task_contracts = []
        for ordinal, (case, parent_file) in enumerate(zip(manifest['cases'], protocol['original_task_files'])):
            parent, task = read(ROOT/parent_file), read(ROOT/case['task'])
            expected = deepcopy(parent)
            expected['input']['target_mm'] = .5
            expected['path'] = dict(kind='load_only', targets_mm=[0., .25, .5])
            expected.update(protocol['task_metadata'])
            assert task == expected
            assert parent['path']['kind'] == 'ordered_cycle' and len(parent['path']['targets_mm']) == 25
            assert parent['input']['target_mm'] == 1.2
            output = (ROOT/case['output']).resolve()
            assert output == run/'cases'/f'{ordinal:03d}'
            outputs_to_labels[output] = case['label']
            task_contracts.append({k:v for k,v in task.items() if k != 'geometry'})
            cases[case['label']] = dict(label=case['label'], api_started=0, api_completed=0,
                solve_started=0, solve_completed=0, accepted_states=0,
                API_status=None, API_failure=None, cached_production_gates=None,
                production_call_counts=None)
        assert task_contracts[0] == task_contracts[1]
        sys.path.insert(0, str(ROOT/'hf_repo/src'))
        from hf_eval import native_batch, native_evaluate
        from hf_eval.tmc import TMCError
        TMCErrorClass = TMCError
        for module in (native_batch, native_evaluate):
            assert Path(module.__file__).resolve().parent == ROOT/'hf_repo/src/hf_eval'
        original_solve = native_evaluate.solve_native_mean
        original_api = native_batch.evaluate_native
        assert original_api is native_evaluate.evaluate_native
        active_label = None

        def solve(*values, **keywords):
            label = active_label
            assert label is not None
            case = cases[label]
            calls['solve_started'] += 1
            case['solve_started'] += 1
            previous_callback = keywords.get('on_accept')

            def accepted(snapshot):
                record = snapshot.record
                fields = ('d', 'R_input', 'q_in', 'q_out', 'relative_residual', 'constraint_residual',
                    'constraint_bound', 'minimum_J', 'relative_global_force_balance', 'newton_checks',
                    'bisection_depth', 'state_sha256', 'leg', 'original_target_index', 'is_original_target')
                row = {key: record[key] for key in fields}
                body = record['workpiece']['force_on_lower_body_N']
                row.update(label=label, accepted_index=case['accepted_states'],
                    global_progress_index=receipt['accepted_progress_rows'], elapsed_seconds=perf_counter()-STARTED,
                    workpiece_total_Fy_N=body['total'][1], workpiece_material_Fy_N=body['material'][1],
                    workpiece_Hu_Fy_N=body['regularization'][1])
                with progress.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(row, allow_nan=False)+'\n')
                case['accepted_states'] += 1
                receipt['accepted_progress_rows'] += 1
                if previous_callback is not None:
                    previous_callback(snapshot)
                checkpoint('accepted_state')

            keywords['on_accept'] = accepted
            result = original_solve(*values, **keywords)
            calls['solve_completed'] += 1
            case['solve_completed'] += 1
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
            case['cached_production_gates'] = cached
            case['production_call_counts'] = deepcopy(result.metadata['call_counts'])
            case['actual_settings'] = deepcopy(result.metadata['settings'])
            return result

        def evaluate(*values, **keywords):
            nonlocal active_label
            checkpoint()
            label = outputs_to_labels[Path(values[2]).resolve()]
            case = cases[label]
            active_label = label
            calls['api_started'] += 1
            case['api_started'] += 1
            print(json.dumps(dict(event='case_started', label=label)), flush=True)
            try:
                response = original_api(*values, **keywords)
                calls['api_completed'] += 1
                case['api_completed'] += 1
                case['API_status'], case['API_failure'] = response['status'], deepcopy(response.get('failure'))
                # Preserve the original non-success response before observer IO/checks.
                if response['status'] != 'success':
                    return response
                if not (case['cached_production_gates'] or {}).get('passed', False):
                    raise TMCError('Original API saved success but cached production gates failed', code='production_cache_gate_failed')
                write(receipt_file, receipt | dict(cases=list(cases.values()), call_counts=dict(calls)))
                print(json.dumps(dict(event='case_completed', label=label, status=response['status'],
                    accepted_states=case['accepted_states'])), flush=True)
                checkpoint()
                return response
            finally:
                active_label = None

        phase = 'production_batch'
        native_evaluate.solve_native_mean = solve
        native_batch.evaluate_native = evaluate
        try:
            checkpoint()
            calls['batch_started'] += 1
            index = native_batch.evaluate_native_batch(manifest_file, run/'batch', repo_root=ROOT)
            calls['batch_completed'] += 1
        finally:
            native_evaluate.solve_native_mean = original_solve
            native_batch.evaluate_native = original_api
        receipt['batch_status'] = index['status']
        receipt['batch_failure_case'] = index['failure_case']
        if index['status'] != 'success':
            raise RuntimeError('Original batch non-success; actual partial and not_run retained; no display')
        for entry in index['cases']:
            case = cases[entry['label']]
            assert entry['status'] == 'success' and case['cached_production_gates']['passed']
            assert case['api_started'] == case['api_completed'] == case['solve_started'] == case['solve_completed'] == 1
            assert case['accepted_states'] == case['cached_production_gates']['actual_accepted_states'] >= 3
            assert case['actual_settings'] == protocol['settings']
            assert entry['path']['completed'] and entry['path']['requested_targets_mm'] == protocol['targets_mm']
            assert entry['invocation']['targets_mm'] == protocol['targets_mm']
            assert all(value is False for value in entry['producer_flags'].values())
            assert entry['independent_reference']['status'] == entry['views']['status'] == 'not_provided'
            assert case['production_call_counts']['HP_calls'] == case['production_call_counts']['JIT_calls'] == 0
        checkpoint()
        phase = 'saved_display'
        runtime_protocol = dict(protocol, runtime_helper_deadline=monotonic()+protocol['helper_seconds']-(perf_counter()-STARTED))
        spec = importlib.util.spec_from_file_location('_batch_saved_display', ROOT/protocol['display_source'])
        display = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(display)
        calls['display_started'] += 1
        receipt['display'] = display.run_display(ROOT, STAGE, runtime_protocol, index, checkpoint)
        calls['display_completed'] += 1
        assert receipt['display']['status'] == 'pass'
        assert len(receipt['display']['PNG_files']) == 5 and len(receipt['display']['GIF_files']) == 2
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
    receipt.update(phase=phase, cases=list(cases.values()), call_counts=dict(calls), events=dict(events),
        outputs=outputs, output_identity_seal=seal_scope,
        wrapper_binding_file_reads=dict(binding_reads),
        binding_read_scope='Each streamed SHA pass counts one file read; API/model snapshots/viewer reads are delegated, not universal file-open hooks',
        elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak,
        helper_seconds=protocol['helper_seconds'], sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()), completed_utc=datetime.now(timezone.utc).isoformat(),
        old_records_rewritten=False, new_mechanical_kernels=0, new_tests=0,
        forced_GC_calls=0, external_retries=0, source_bindings=protocol['source_bindings'])
    write(receipt_file, receipt)
    print(json.dumps(dict(status=receipt['status'], phase=phase, call_counts=dict(calls),
        accepted_progress_rows=receipt['accepted_progress_rows'], error=receipt.get('error'))), flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('L-BFWD1 closed not_pass; no retry or following phase')


if __name__ == '__main__':
    main()
