"""Freeze a case reference only after the complete new real batch passes."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import shutil

STAGE = 'lf_data_preparation/native_interface_001/batch_forward_001'
LABELS = ('canonical', 'native_fine')
LEGACY = dict(canonical='native_gripper_task_025_001', native_fine='native_fine_task_025_001')
RSS = 8 * 1024**3
STRUCTURAL_PINS = dict(prior_model_file='prior_model_sha256', prior_task_file='prior_task_sha256',
                       direction_file='direction_file_sha256', lifting_file='lifting_file_sha256')
MATH_PINS = {
    'audit_native_mean.py': '331eb1d5406b6d6538d838da823e214201b5ec26c8fac9f7f0bc77f23b8a1678',
    'audit_native_force.py': 'cd317914cba2e3ad2f5ec5bf5b857804c3406313ab6a433bd1d7b395872ee8bb',
    'hf4_split_precision_reference.py': '308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2',
    'hf2_precision_reference.py': '97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55',
    'run_split_average_demo.py': 'e949cece3fddfb03a51d4c2fdd6788f65dfbbf66df31e16e57c0b9c6bd8609cb',
}
SCALARS = ('state_sha256', 'd', 'R_input', 'q_in', 'q_out', 'minimum_J',
           'relative_residual', 'constraint_residual', 'constraint_bound', 'relative_global_force_balance')
ONCE = ('evaluate_native', 'native_solve', 'project_builder', 'constructor',
        'controller', 'cached_writer', 'formatter', 'response_writer')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def gates_from_source(path):
    values = [n.value for n in ast.parse(path.read_bytes()).body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'GATES' for t in n.targets)]
    assert len(values) == 1
    return {item.arg: ast.literal_eval(item.value) for item in values[0].keywords}


def verify_batch_production(root, label, bind):
    """JSON/raw hashes only; do not turn a partial batch into reference eligibility."""
    assert label in LABELS
    control, run = root/STAGE, root/STAGE/'run_001'
    protocol_file, receipt_file = control/'production_protocol.json', run/'execution_receipt.json'
    launch_file, index_file = control/'production_launch.json', run/'batch/index.json'
    for path in (protocol_file, receipt_file, launch_file, index_file):
        bind(path)
    protocol, receipt, launch, index = map(read, (protocol_file, receipt_file, launch_file, index_file))
    assert protocol['schema_version'] == 'native-real-batch-protocol-1.0'
    assert protocol['run_directory'] == STAGE+'/run_001' and protocol['batch_directory'] == STAGE+'/run_001/batch'
    assert protocol['targets_mm'] == [0., .005, .010, .025] and protocol['expected_model_fields'] == 23
    assert protocol['options'] == dict(targets=protocol['targets_mm'], minimum_increment=.0000625,
        time_limit_seconds=1800, response_mode='complete', tangent_mode='full', initial_guess='tangent')
    assert protocol['sampled_RSS_bytes'] == RSS
    assert protocol['phases']['production']['helper_seconds'] == 2400 and protocol['phases']['production']['outer_seconds'] == 2460
    assert receipt['schema_version'] == 'native-real-batch-execution-1.0'
    assert receipt['status'] == launch['status'] == 'pass' and index['status'] == 'success'
    assert receipt['batch_invocations'] == launch['invocations'] == 1 and launch['exit_code'] == 0 and launch['stop_reason'] is None
    assert receipt['all_bindings_unchanged'] and launch['all_bindings_unchanged']
    assert receipt['protocol_sha256'] == launch['protocol_sha256'] == sha(protocol_file)
    assert receipt['bindings'] == launch['bindings'] == protocol['bindings']
    assert receipt['baseline_commit'] == protocol['baseline_commit'] and receipt['production_gates'] == protocol['gates']
    assert receipt['seconds_limit'] == 2400 and receipt['outer_seconds'] == launch['outer_seconds'] == 2460
    assert receipt['elapsed_seconds'] <= 2400 and launch['elapsed_seconds'] <= 2460
    assert receipt['sampled_RSS_limit_bytes'] == launch['sampled_RSS_limit_bytes'] == RSS
    assert receipt['peak_sampled_RSS_bytes'] <= RSS and launch['peak_sampled_tree_RSS_bytes'] <= RSS
    assert not any(receipt.get(k) for k in ('exception', 'finalization_exception', 'stop_reason'))
    assert receipt['batch_returned'] == index and receipt['batch_index_file'] == STAGE+'/run_001/batch/index.json'
    assert index['failure_case'] is None and index['HF5_qualified'] is index['ranking_qualified'] is False
    assert receipt['options'] == protocol['options'] and index['options'] == dict(protocol['options'], settings=None)
    for name, pin in protocol['bindings'].items():
        bind(root/name, pin)
    for name, pin in receipt['outputs'].items():
        bind(root/name, pin)
    manifest = read(root/protocol['manifest_file'])
    assert receipt['manifest_file'] == protocol['manifest_file'] and receipt['manifest_sha256'] == sha(root/protocol['manifest_file'])
    assert manifest['options'] == protocol['options'] and [c['label'] for c in manifest['cases']] == list(LABELS)
    assert [c['label'] for c in index['cases']] == list(LABELS) and set(receipt['cases']) == set(LABELS)
    current = {name: pin for name, pin in protocol['bindings'].items() if name.startswith('hf_repo/src/hf_eval/')}
    assert len(current) == len({Path(name).name for name in current}) == 28
    selected = None
    for plan, entry in zip(manifest['cases'], index['cases'], strict=True):
        case = receipt['cases'][plan['label']]
        assert plan['output'] == STAGE+'/run_001/'+plan['label'] == case['output'] == entry['output']['path']
        assert case['attempted'] and case['status'] == entry['status'] == 'success' and case['production_pass']
        assert all(case['counts'][name]['started'] == case['counts'][name]['completed'] == 1 for name in ONCE)
        assert not case.get('exception') and case['cached_write_F_T_delta'] == dict(force_calls=0, tangent_calls=0)
        assert case['result_file'] == plan['output']+'/result.json' and case['response_file'] == plan['output']+'/response.json'
        result_file, response_file = root/case['result_file'], root/case['response_file']
        bind(result_file, case['result_sha256']); bind(response_file, case['response_sha256'])
        result, response = read(result_file), read(response_file)
        assert response == case['returned_response'] and response['status'] == result['status'] == 'success'
        assert entry['response']['path'] == case['response_file'] and entry['response']['sha256'] == case['response_sha256']
        assert response['identity']['result']['sha256'] == case['result_sha256']
        assert result['failure'] is None and result['targets_mm'] == protocol['targets_mm'] and result['task_target_mm'] == .025
        assert result['settings'] == response['invocation']['settings'] == protocol['settings']
        assert result['counts'] == protocol['expected_counts'][plan['label']]
        assert all(current.get(name) == pin for name, pin in result['mechanics_source_sha256'].items())
        counts = result['call_counts']
        assert counts == entry['call_counts'] == case['original_result_metadata']['call_counts']
        assert counts['solver_invocations'] == 1 and counts['HP_calls'] == counts['JIT_calls'] == 0
        assert counts['force_calls'] == counts['force_calls_completed'] and counts['tangent_calls'] == counts['tangent_calls_completed']
        assert case['observed_F_T'] == {key: counts[key] for key in case['observed_F_T']}
        assert result['save_force_calls'] == result['save_tangent_calls'] == 0
        states = result['states']; n = len(states)
        assert n == result['accepted_states'] == len(case['accepted_scalar_prefix']) == response['path']['accepted_states']
        assert case['counts']['accepted_callback']['started'] == case['counts']['accepted_callback']['completed'] == n
        assert n >= len(protocol['targets_mm']) and response['path']['completed'] and response['path']['task_target_executed']
        assert result['task_target_executed'] and case['production_gate_status'] == 'checked' and len(case['production_gate_rows']) == n
        for i, (row, observed, gate) in enumerate(zip(states, case['accepted_scalar_prefix'], case['production_gate_rows'], strict=True)):
            assert observed['case_index'] == i and all(observed[k] == gate[k] == row[k] for k in SCALARS)
            assert all(gate[k] for k in ('positive_J', 'production_residual_pass', 'native_constraint_bound_pass',
                                         'global_force_balance_pass', 'fixed_displacement_pass'))
            assert gate['fixed_max_abs_displacement_mm'] <= float(protocol['gates']['fixed_displacement_mm'])
        assert response['target_response']['d_mm'] == response['requested_endpoint_response']['d_mm'] == .025
        assert response['target_response']['workpiece'] is None and all(v is False for v in response['producer_flags'].values())
        assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
        assert all(v is False for k, v in response['independent_reference'].items() if k.endswith('_pass') or k.endswith('_qualified'))
        assert response['views']['manifest'] is None and not response['views']['links']
        assert all(response['options'][k]['value'] == protocol['options'][k] for k in ('response_mode','tangent_mode','initial_guess'))
        if plan['label'] == label:
            selected = plan, case, result
    return protocol, receipt, index, current, selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--case', choices=LABELS, required=True)
    parser.add_argument('--time-limit', type=float, required=True)
    parser.add_argument('--outer-seconds', type=float, required=True)
    parser.add_argument('--budget-basis', required=True)
    parser.add_argument('--root-review', type=Path, required=True)
    parser.add_argument('--peer-review', type=Path, required=True)
    args = parser.parse_args()
    root, author, label = args.repo.resolve(), Path(__file__).resolve().parent, args.case
    control = root/STAGE
    assert math.isfinite(args.time_limit) and args.time_limit > 0 and math.isfinite(args.outer_seconds) and args.outer_seconds > args.time_limit
    assert args.budget_basis.strip() and not (control/'stop_requested.txt').exists()
    contract_file, protocol_file = control/f'reference_contract_{label}.json', control/f'reference_protocol_{label}.json'
    output = control/'run_001/audit'/label
    assert not contract_file.exists() and not protocol_file.exists() and not output.exists()
    bindings = {}
    def bind(path, expected=None):
        actual = sha(path); assert expected is None or actual == expected
        name = path.relative_to(root).as_posix(); assert name not in bindings or bindings[name] == actual
        bindings[name] = actual
        return actual
    protocol, receipt, index, current, (plan, case, result) = verify_batch_production(root, label, bind)
    legacy_file = root/'lf_data_preparation'/LEGACY[label]/'input_inventory.json'
    bind(legacy_file, protocol['bindings'][legacy_file.relative_to(root).as_posix()])
    prior = read(legacy_file)['case']
    assert plan['geometry'] == prior['geometry_file'] and plan['task'] == prior['prior_task_file']
    structural = {key: prior[key] for key in STRUCTURAL_PINS}
    for key, name in structural.items():
        bind(root/name, prior[STRUCTURAL_PINS[key]])
    for name, pin in MATH_PINS.items():
        bind(root/'hf_repo/scripts'/name, pin)
    assert gates_from_source(root/'hf_repo/scripts/audit_native_mean.py') == gates_from_source(root/'hf_repo/scripts/run_split_average_demo.py') == protocol['gates']
    reports = [args.root_review.resolve(), args.peer_review.resolve()]
    for file in reports:
        report = read(file); assert report['status'] == 'pass_static_only' and not report['blocking_findings']
        for name in ('audit_batch_case.py', 'reference_case_builder.py'):
            matched = {pin for key, pin in report['source_sha256'].items() if Path(key.replace('\\','/')).name == name}
            assert matched == {sha(author/name)}
    target = control/'reference_author'
    files = ['audit_batch_case.py','reference_case_builder.py','README.md','author_note.json','author_checks.json','source_additions.diff']
    if not target.exists():
        target.mkdir()
        for name in files:
            shutil.copyfile(author/name, target/name)
        for name, file in zip(('root_review.json','peer_review.json'), reports, strict=True):
            shutil.copyfile(file, target/name)
    for name in files:
        bind(target/name, sha(author/name))
    for name, file in zip(('root_review.json','peer_review.json'), reports, strict=True):
        bind(target/name, sha(file))
    ref_sources = dict(current, **{'hf_repo/scripts/'+n:p for n,p in MATH_PINS.items()},
                       **{(target/n).relative_to(root).as_posix():sha(target/n) for n in ('audit_batch_case.py','reference_case_builder.py')})
    assert len(ref_sources) == len({Path(name).name for name in ref_sources}) == 35
    contract = dict(schema_version='native-batch-case-reference-contract-1.0', case_label=label,
        production_stage=STAGE, case_directory=plan['output'], reference_output=output.relative_to(root).as_posix(),
        baseline_commit=protocol['baseline_commit'], production_protocol_sha256=sha(control/'production_protocol.json'),
        production_receipt_sha256=sha(control/'run_001/execution_receipt.json'), production_launch_sha256=sha(control/'production_launch.json'),
        batch_index_sha256=sha(control/'run_001/batch/index.json'), production_result_sha256=case['result_sha256'],
        production_response_sha256=case['response_sha256'], current_sources=current, reference_sources=ref_sources,
        accepted_states=len(result['states']), state_sha256=[r['state_sha256'] for r in result['states']],
        fresh_HP_calls_required=2*len(result['states']), targets_mm=protocol['targets_mm'], gates=protocol['gates'],
        expected_counts=protocol['expected_counts'][label], limits=dict(helper_seconds=args.time_limit,
            outer_seconds=args.outer_seconds,sampled_RSS_bytes=RSS), reference_budget_basis=args.budget_basis,
        legacy_inventory=legacy_file.relative_to(root).as_posix(), structural_inputs=structural,
        structural_comparison_scope='Prior intrinsic model/task/direction/lift only; no prior production/HP qualification.',
        new_reference_status='not_executed', qualified_summary='qualified_summary.json',
        qualification_scope='Fresh complete 0.025mm no-workpiece all accepted-state mechanical TEST; no energy/pressure/contact/all-tangent-columns/HF5/ranking/mesh-convergence upgrade.')
    write(contract_file,contract);bind(contract_file)
    argv=[STAGE+'/reference_author/audit_batch_case.py','--repo','.', '--case',label,
        '--input',plan['output'],'--output',output.relative_to(root).as_posix(), '--contract',contract_file.relative_to(root).as_posix(),
        '--time-limit',str(args.time_limit)]
    write(protocol_file,dict(schema_version='native-batch-case-reference-protocol-1.0',case_label=label,
        baseline_commit=protocol['baseline_commit'],bindings=bindings,sampled_RSS_bytes=RSS,
        phases={f'reference_{label}':dict(helper_seconds=args.time_limit,outer_seconds=args.outer_seconds,argv=argv)},
        actual_accepted_states=len(result['states']),fresh_HP_calls_required=2*len(result['states']),
        scope=contract['qualification_scope'],stop_policy='One fresh all-state case reference; first error stops, no production, retry or repair.'))
    assert all(sha(root/name)==pin for name,pin in bindings.items())
    print(json.dumps(dict(status='reference_frozen_not_executed',case=label,actual_states=len(result['states']),fresh_HP=2*len(result['states']))))


if __name__ == '__main__':
    main()
