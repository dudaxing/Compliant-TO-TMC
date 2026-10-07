"""Terminal-only JSON and ordinary byte identities; no HF, arrays or mechanics."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT / 'lf_data_preparation/native_interface_001/batch_forward_001'
OUTPUT = Path(__file__).resolve().with_name('batch_forward_closure_review.json')
ONCE = ('evaluate_native','native_solve','project_builder','constructor','controller','cached_writer','formatter','response_writer')
SCALARS = ('state_sha256','d','R_input','q_in','q_out','minimum_J','relative_residual','constraint_residual','constraint_bound','relative_global_force_balance')
F_T = ('force_calls','force_calls_completed','tangent_calls','tangent_calls_completed')
COPIED_RESPONSE_FIELDS = ('identity','options','invocation','evaluation_elapsed_scope','qualification_scope','path','target_response','requested_endpoint_response','maximum_loading_stroke','last_accepted','call_counts','timing_seconds','evaluation_elapsed_seconds','failure','producer_flags','independent_reference','views')

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def canonical(value):
    if isinstance(value,dict):
        return {k:canonical(v) for k,v in value.items()}
    if isinstance(value,list):
        return [canonical(v) for v in value]
    if isinstance(value,float):
        assert math.isfinite(value)
        return (0. if value == 0. else value).hex()
    return value

def canonical_hash(value):
    raw = json.dumps(canonical(value),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def descriptor(record):
    assert canonical_hash({k:v for k,v in record.items() if k != 'descriptor_sha256'}) == record['descriptor_sha256']

def point_matches(point,index,row):
    names = {'state_sha256':'state_sha256','d_mm':'d','R_input_N':'R_input','q_in_mm':'q_in','q_out_mm':'q_out','minimum_J':'minimum_J','relative_residual':'relative_residual','relative_global_force_balance':'relative_global_force_balance','constraint_residual_mm':'constraint_residual','max_abs_Hu_per_mm':'max_abs_Hu_per_mm'}
    assert point['index'] == index and all(point[name] == row[source] for name,source in names.items())
    assert point['workpiece'] is None

def main():
    protocol_file = STAGE / 'production_protocol.json'
    protocol = read(protocol_file)
    launch = read(STAGE / 'production_launch.json')
    receipt_file = ROOT / protocol['run_directory'] / 'execution_receipt.json'
    receipt = read(receipt_file)
    # A live prefix is not a terminal result. Do not run this recipe before root confirms closure.
    assert launch['status'] in ('pass','not_pass') and 'completed_utc' in launch
    assert receipt['status'] in ('pass','failed') and 'completed_utc' in receipt
    protocol_pin = sha(protocol_file)
    assert launch['protocol_sha256'] == receipt['protocol_sha256'] == protocol_pin
    assert launch['bindings'] == receipt['bindings'] == protocol['bindings']
    assert len(protocol['bindings']) == 52
    assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
    run = ROOT / protocol['run_directory']
    raw_outputs = {path.relative_to(ROOT).as_posix():sha(path) for path in run.rglob('*') if path.is_file() and path != receipt_file}
    assert raw_outputs == receipt['outputs']
    manifest = read(ROOT / protocol['manifest_file'])
    assert sha(ROOT / protocol['manifest_file']) == receipt['manifest_sha256']
    assert manifest['options'] == protocol['options'] == receipt['options']
    expected_pass = launch['status'] == 'pass' and receipt['status'] == 'pass'
    report = dict(schema_version='native-real-batch-saved-closure-review-1.0',
        status='pass_saved_only' if expected_pass else 'closed_failed_saved_only',
        blocking_findings=[], reviewed_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=protocol_pin, launch_sha256=sha(STAGE/'production_launch.json'),
        execution_receipt_sha256=sha(receipt_file), bindings_verified=52,
        current_runtime_sources_unchanged=sum(name.startswith('hf_repo/src/') for name in protocol['bindings']),
        saved_output_files_verified=len(raw_outputs), production_status=dict(launch=launch['status'],worker=receipt['status'],exit_code=launch['exit_code'],stop_reason=launch['stop_reason']),
        resources=dict(helper_elapsed_seconds=receipt['elapsed_seconds'],outer_elapsed_seconds=launch['elapsed_seconds'],helper_peak_sampled_RSS_bytes=receipt['peak_sampled_RSS_bytes'],outer_peak_sampled_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],helper_limit_seconds=protocol['phases']['production']['helper_seconds'],outer_limit_seconds=protocol['phases']['production']['outer_seconds'],sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],controller_seconds_per_case=protocol['options']['time_limit_seconds'],helper_elapsed_scope=receipt['elapsed_scope']),
        cases={}, scope='Saved production transport and original gates only; no new HP/reference/view/pressure/mesh/ranking/HF5 qualification',
        activity=dict(HF_imports=0,NPZ_loads=0,array_or_geometry_observations=0,constructors=0,F=0,T=0,solver=0,HP=0,tests=0,renders=0,formal_writes=0),
        ordinary_byte_scope='Compressed array files are streamed solely for raw SHA verification; no archive opening, decompression or array values.',
        cache_release_scope='Per-case recorded singleton GC of unreachable closure cycles; no assertion that OS RSS immediately fell.')
    if not expected_pass:
        report.update(original_exception=receipt.get('exception'),finalization_exception=receipt.get('finalization_exception'),accepted_case_records=receipt['cases'],batch_index_file=receipt['batch_index_file'])
        report['blocking_findings'] = ['Production did not pass; retain original failure/prefix and no full-path qualification.']
    else:
        assert launch['invocations'] == 1 and receipt['batch_invocations'] == 1
        assert launch['exit_code'] == 0 and launch['stop_reason'] is None
        assert launch['all_bindings_unchanged'] is receipt['all_bindings_unchanged'] is True
        assert 'exception' not in receipt and 'finalization_exception' not in receipt
        assert receipt['elapsed_seconds'] <= protocol['phases']['production']['helper_seconds'] == 2400
        assert launch['elapsed_seconds'] <= protocol['phases']['production']['outer_seconds'] == 2460
        assert max(receipt['peak_sampled_RSS_bytes'],launch['peak_sampled_tree_RSS_bytes']) <= protocol['sampled_RSS_bytes'] == 8589934592
        assert protocol['options']['time_limit_seconds'] == 1800
        index_file = ROOT / protocol['batch_directory'] / 'index.json'
        index = read(index_file)
        assert index == receipt['batch_returned'] and index['status'] == 'success'
        assert not index['HF5_qualified'] and not index['ranking_qualified']
        assert index['manifest']['sha256'] == receipt['manifest_sha256']
        assert index['options'] == dict(protocol['options'],settings=None)
        progress_file = run / 'accepted_progress.jsonl'
        progress = [json.loads(line) for line in progress_file.read_text(encoding='utf-8').splitlines() if line]
        assert progress == [row for case in receipt['cases'].values() for row in case['accepted_scalar_prefix']]
        for plan, entry in zip(manifest['cases'],index['cases']):
            label = plan['label']
            case = receipt['cases'][label]
            assert entry['label'] == label and case['attempted'] and case['status'] == entry['status'] == 'success'
            assert all(case['counts'][name]['started'] == case['counts'][name]['completed'] == 1 for name in ONCE)
            output = ROOT / plan['output']
            result_file, response_file = output/'result.json', output/'response.json'
            result, response = read(result_file), read(response_file)
            assert response == case['returned_response'] and response['status'] == result['status'] == 'success'
            assert sha(result_file) == case['result_sha256'] == response['identity']['result']['sha256']
            assert sha(response_file) == case['response_sha256'] == entry['response']['sha256']
            assert entry['response']['path'] == response_file.relative_to(ROOT).as_posix()
            assert all(entry[name] == response.get(name) for name in COPIED_RESPONSE_FIELDS)
            assert all(result[name] == value for name,value in case['original_result_metadata'].items())
            descriptor(result)
            model_file = output/result['model']['descriptor_path']
            model = read(model_file)
            descriptor(model)
            task = read(ROOT/plan['task'])
            assert model['task'] == task and canonical_hash(task) == result['task_sha256'] == model['task_sha256']
            assert response['identity']['task_sha256'] == result['task_sha256']
            assert sha(model_file) == result['model']['descriptor_file_sha256'] == response['identity']['model']['sha256']
            assert model['arrays']['sha256'] == result['model']['arrays_sha256']
            assert len(model['arrays']['fields']) == protocol['expected_model_fields'] == 23
            assert result['counts'] == protocol['expected_counts'][label]
            assert result['settings'] == response['invocation']['settings'] == protocol['settings']
            assert response['invocation']['targets_mm'] == result['targets_mm'] == protocol['targets_mm']
            assert result['lift_origin_zero'] and result['lift_shape_zero'] and result['task_target_executed']
            assert response['path']['completed'] and response['path']['task_target_executed']
            assert all(response['options'][name]['value'] == protocol['options'][name] for name in ('response_mode','tangent_mode','initial_guess'))
            counts = result['call_counts']
            assert counts == response['call_counts']
            assert case['observed_F_T'] == {name:counts[name] for name in F_T}
            assert counts['force_calls'] == counts['force_calls_completed'] and counts['tangent_calls'] == counts['tangent_calls_completed']
            assert counts['solver_invocations'] == 1 and counts['JIT_calls'] == counts['HP_calls'] == 0
            assert result['save_force_calls'] == result['save_tangent_calls'] == 0
            assert case['cached_write_F_T_delta'] == dict(force_calls=0,tangent_calls=0)
            states, prefix, gates = result['states'], case['accepted_scalar_prefix'], case['production_gate_rows']
            assert len(states) == result['accepted_states'] == len(prefix) == len(gates)
            assert case['counts']['accepted_callback']['started'] == case['counts']['accepted_callback']['completed'] == len(states)
            assert case['production_pass'] and case['production_gate_status'] == 'checked'
            for i,(row,scalar,gate) in enumerate(zip(states,prefix,gates)):
                assert scalar['label'] == label and scalar['case_index'] == i
                assert all(scalar[name] == gate[name] == row[name] for name in SCALARS)
                assert row['minimum_J'] > 0 and row['relative_residual'] <= float(protocol['gates']['production_residual'])
                assert abs(row['constraint_residual']) <= row['constraint_bound']
                assert row['relative_global_force_balance'] <= float(protocol['gates']['global_force_balance'])
                assert gate['fixed_max_abs_displacement_mm'] <= float(protocol['gates']['fixed_displacement_mm'])
                assert all(gate[name] for name in ('positive_J','production_residual_pass','native_constraint_bound_pass','global_force_balance_pass','fixed_displacement_pass'))
                state_file = output/row['descriptor_path']
                saved_state = read(state_file)
                descriptor(saved_state)
                assert saved_state == {k:v for k,v in row.items() if k not in ('descriptor_path','descriptor_file_sha256')}
                assert sha(state_file) == row['descriptor_file_sha256']
                for name in ('state','forces','tangents','matrix'):
                    assert sha(output/row[name]['path']) == row[name]['sha256']
            assert all(any(row['is_original_target'] and row['d'] == target for row in states) for target in protocol['targets_mm'])
            point_matches(response['last_accepted'],len(states)-1,states[-1])
            task_index = next(i for i,row in enumerate(states) if row['is_original_target'] and row['d'] == result['task_target_mm'])
            point_matches(response['target_response'],task_index,states[task_index])
            point_matches(response['requested_endpoint_response'],len(states)-1,states[-1])
            assert response['target_response']['d_mm'] == response['requested_endpoint_response']['d_mm'] == .025
            assert all(value is False for value in response['producer_flags'].values())
            reference = response['independent_reference']
            assert reference['status'] == 'not_provided' and all(value is False for name,value in reference.items() if name.endswith('_pass') or name.endswith('_qualified'))
            assert response['views']['status'] == 'not_provided' and response['views']['manifest'] is None and not response['views']['links']
            assert case['cache_release']['invocations'] == 1 and case['cache_release']['elapsed_seconds'] >= 0
            report['cases'][label] = dict(accepted_states=len(states), original_targets=protocol['targets_mm'], extra_bisection_states=sum(not row['is_original_target'] for row in states), call_counts=counts, once_delegate_counts={name:case['counts'][name] for name in ONCE},cache_release=case['cache_release'],result_sha256=sha(result_file),response_sha256=sha(response_file),model_sha256=sha(model_file),last_accepted=response['last_accepted'],target_response=response['target_response'],requested_endpoint_response=response['requested_endpoint_response'],producer_flags=response['producer_flags'],independent_reference=reference,views=response['views'],maximum_relative_residual=max(row['relative_residual'] for row in states),minimum_J=min(row['minimum_J'] for row in states),maximum_relative_global_force_balance=max(row['relative_global_force_balance'] for row in states),maximum_fixed_displacement_mm=max(row['fixed_max_abs_displacement_mm'] for row in gates))
        report['batch_index_sha256'] = sha(index_file)
        report['accepted_progress_sha256'] = sha(progress_file)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],path=str(OUTPUT),sha256=sha(OUTPUT))))

if __name__ == '__main__':
    main()
