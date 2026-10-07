"""Freeze fresh all-state HP only after the real API production card passes."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import shutil

STAGE = 'lf_data_preparation/native_interface_001/real_forward_001'
BASE = 'lf_data_preparation/native_mean_001'
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
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def gates_from_source(path):
    syntax = ast.parse(path.read_text(encoding='utf-8'))
    values = [node.value for node in syntax.body if isinstance(node, ast.Assign)
              and any(isinstance(item, ast.Name) and item.id == 'GATES' for item in node.targets)]
    assert len(values) == 1
    return {item.arg: ast.literal_eval(item.value) for item in values[0].keywords}


def verify_production(root, bind):
    control, run = root/STAGE, root/STAGE/'run_001'
    protocol_file = control/'production_protocol.json'
    receipt_file, launch_file = run/'execution_receipt.json', control/'production_launch.json'
    for file in (protocol_file, receipt_file, launch_file, control/'installation_receipt.json'):
        bind(file)
    protocol, receipt, launch = map(read, (protocol_file, receipt_file, launch_file))
    assert protocol['schema_version'] == 'native-real-api-protocol-1.0'
    assert protocol['run_directory'] == STAGE+'/run_001' and protocol['result_directory'] == STAGE+'/run_001/result'
    assert protocol['targets_mm'] == [0., .001] and protocol['expected_model_fields'] == 23
    assert protocol['options'] == dict(response_mode='complete', tangent_mode='full', initial_guess='tangent')
    assert protocol['sampled_RSS_bytes'] == RSS
    assert protocol['phases']['production']['helper_seconds'] == 180 and protocol['phases']['production']['outer_seconds'] == 210
    assert receipt['schema_version'] == 'native-real-api-execution-1.0' and receipt['status'] == launch['status'] == 'pass'
    assert receipt['invocations'] == launch['invocations'] == 1 and launch['exit_code'] == 0 and launch['stop_reason'] is None
    assert receipt['all_bindings_unchanged'] and launch['all_bindings_unchanged']
    assert receipt['protocol_sha256'] == launch['protocol_sha256'] == sha(protocol_file)
    assert launch['bindings'] == protocol['bindings'] and receipt['baseline_commit'] == protocol['baseline_commit']
    assert receipt['seconds_limit'] == 180 and launch['outer_seconds'] == 210
    assert receipt['elapsed_seconds'] <= 180 and launch['elapsed_seconds'] <= 210
    assert receipt['sampled_RSS_limit_bytes'] == launch['sampled_RSS_limit_bytes'] == RSS
    assert receipt['peak_sampled_RSS_bytes'] <= RSS and launch['peak_sampled_tree_RSS_bytes'] <= RSS
    assert not any(receipt.get(key) for key in ('exception', 'finalization_exception', 'stop_reason', 'returned_API_failure'))
    for name, pin in protocol['bindings'].items():
        bind(root/name, pin)
    current = {name: pin for name, pin in protocol['bindings'].items() if name.startswith('hf_repo/src/')}
    assert len(current) == len({Path(name).name for name in current}) == 27
    roles = {'constructor', 'project_builder', 'controller', 'native_solve', 'cached_writer', 'formatter', 'response_writer'}
    assert receipt['counts'].keys() == roles and all(value == dict(started=1, completed=1) for value in receipt['counts'].values())
    assert receipt['cached_write_F_T_delta'] == dict(force_calls=0, tangent_calls=0)
    assert receipt['HP_calls'] == receipt['JIT_calls'] == receipt['LF_imports'] == 0
    for name, pin in receipt['outputs'].items():
        bind(root/name, pin)
    assert receipt['result_file'] == STAGE+'/run_001/result/result.json'
    assert receipt['response_file'] == STAGE+'/run_001/result/response.json'
    result_file, response_file = root/receipt['result_file'], root/receipt['response_file']
    bind(result_file, receipt['result_sha256']); bind(response_file, receipt['response_sha256'])
    result, response = read(result_file), read(response_file)
    assert result['status'] == response['status'] == 'success' and result['failure'] is None
    assert result['call_counts'] == receipt['call_counts']
    counts = result['call_counts']
    assert counts['solver_invocations'] == 1 and counts['HP_calls'] == counts['JIT_calls'] == 0
    assert counts['force_calls'] == counts['force_calls_completed'] and counts['tangent_calls'] == counts['tangent_calls_completed']
    assert receipt['observed_F_T'] == {key: counts[key] for key in receipt['observed_F_T']}
    assert result['save_force_calls'] == result['save_tangent_calls'] == 0
    assert all(current.get(name) == pin for name, pin in result['mechanics_source_sha256'].items())
    assert result['settings'] == protocol['settings'] and result['counts'] == protocol['expected_counts']
    states = result['states']; n = len(states)
    assert n == result['accepted_states'] == receipt['accepted_states'] and n >= 2
    assert len(receipt['accepted_scalar_prefix']) == n and receipt['task_target_executed'] is True
    for index, (row, observed) in enumerate(zip(states, receipt['accepted_scalar_prefix'], strict=True)):
        assert observed['index'] == index
        assert all(observed[key] == row[key] for key in ('state_sha256', 'd', 'R_input', 'q_in', 'q_out', 'minimum_J',
                   'relative_residual', 'constraint_residual', 'relative_global_force_balance'))
    assert response['identity']['result']['sha256'] == sha(result_file)
    assert response['path']['completed'] and response['path']['accepted_states'] == n
    assert response['target_response']['d_mm'] == response['requested_endpoint_response']['d_mm'] == .001
    assert response['target_response']['workpiece'] is None and all(value is False for value in response['producer_flags'].values())
    assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
    assert all(value is False for name, value in response['independent_reference'].items() if name.endswith('_pass') or name.endswith('_qualified'))
    assert response['views']['manifest'] is None and not response['views']['links']
    assert all(response['options'][name]['value'] == value for name, value in protocol['options'].items())
    return protocol, receipt, result, current


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--time-limit', type=float, required=True)
    parser.add_argument('--outer-seconds', type=float, required=True)
    parser.add_argument('--budget-basis', required=True)
    parser.add_argument('--root-review', type=Path, required=True)
    parser.add_argument('--peer-review', type=Path, required=True)
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    control = root/STAGE
    assert args.time_limit == 180 and args.outer_seconds == 210 and args.budget_basis.strip()
    assert not (control/'reference_protocol.json').exists() and not (control/'run_001/audit').exists()
    assert not (control/'reference_author').exists() and not (control/'stop_requested.txt').exists()
    bindings = {}
    def bind(path, expected=None):
        actual = sha(path); assert expected is None or actual == expected
        name = path.relative_to(root).as_posix()
        assert name not in bindings or bindings[name] == actual
        bindings[name] = actual
        return actual
    protocol, receipt, result, current = verify_production(root, bind)
    old_inventory_file = root/BASE/'input_inventory.json'
    bind(old_inventory_file, 'e0b5ccd8defb0f1c8d8d6cb7d8501844e8639ccc010b58f7d362e7f2dbca0b6b')
    baseline = read(old_inventory_file)['case']
    assert protocol['geometry_file'] == baseline['geometry_file'] and protocol['task_file'] == baseline['task_file']
    assert protocol['settings'] == read(old_inventory_file)['settings']
    structural = {key: baseline[key] for key in STRUCTURAL_PINS}
    for key, name in structural.items():
        bind(root/name, baseline[STRUCTURAL_PINS[key]])
    math = {'hf_repo/scripts/'+name: pin for name, pin in MATH_PINS.items()}
    for name, pin in math.items():
        bind(root/name, pin)
    assert gates_from_source(root/'hf_repo/scripts/audit_native_mean.py') == gates_from_source(root/'hf_repo/scripts/run_split_average_demo.py') == protocol['gates']
    reports = [args.root_review.resolve(), args.peer_review.resolve()]
    for report_file in reports:
        report = read(report_file)
        assert report['status'] == 'pass_static_only' and not report['blocking_findings']
        for source in (author/'audit_real_api.py', Path(__file__).resolve()):
            pins = {pin for name, pin in report['source_sha256'].items() if Path(name.replace('\\', '/')).name == source.name}
            assert pins == {sha(source)}
    target = control/'reference_author'; target.mkdir()
    selections = ['audit_real_api.py', 'reference_card_builder.py', 'README.md', 'author_note.json', 'author_checks.json', 'source_additions.diff']
    for name in selections:
        shutil.copyfile(author/name, target/name); bind(target/name, sha(author/name))
    for label, source in zip(('root_review.json', 'peer_review.json'), reports, strict=True):
        shutil.copyfile(source, target/label); bind(target/label, sha(source))
    ref_sources = dict(current, **math, **{(target/name).relative_to(root).as_posix(): sha(target/name)
                                      for name in ('audit_real_api.py', 'reference_card_builder.py')})
    assert len(ref_sources) == len({Path(name).name for name in ref_sources}) == 34
    contract = dict(schema_version='native-real-api-reference-contract-1.0', production_stage=STAGE+'/run_001',
        baseline_commit=protocol['baseline_commit'], production_protocol_sha256=sha(control/'production_protocol.json'),
        production_receipt_sha256=sha(control/'run_001/execution_receipt.json'), production_result_sha256=sha(root/receipt['result_file']),
        production_launch_sha256=sha(control/'production_launch.json'), current_sources=current, reference_sources=ref_sources,
        accepted_states=len(result['states']), state_sha256=[row['state_sha256'] for row in result['states']],
        fresh_HP_calls_required=2*len(result['states']), targets_mm=[0., .001], gates=protocol['gates'],
        limits=dict(helper_seconds=args.time_limit, outer_seconds=args.outer_seconds, sampled_RSS_bytes=RSS),
        reference_budget_basis=args.budget_basis, structural_inputs=structural,
        structural_comparison_scope='Prior intrinsic model/task/direction/lift arrays are structural comparisons only; no old HP or production qualification inherited.',
        new_reference_status='not_executed', qualification_scope='New complete no-workpiece accepted-state mechanical reference only; no energy/pressure/contact/all-columns/HF5 upgrade.')
    write(control/'reference_contract.json', contract); bind(control/'reference_contract.json')
    argv = [STAGE+'/reference_author/audit_real_api.py', '--repo', '.', '--input', STAGE+'/run_001',
            '--output', STAGE+'/run_001/audit', '--contract', STAGE+'/reference_contract.json', '--time-limit', str(args.time_limit)]
    reference_protocol = dict(schema_version='native-real-api-reference-protocol-1.0', baseline_commit=protocol['baseline_commit'],
        bindings=bindings, sampled_RSS_bytes=RSS, phases=dict(reference=dict(helper_seconds=args.time_limit,
            outer_seconds=args.outer_seconds, argv=argv)), actual_accepted_states=len(result['states']),
        fresh_HP_calls_required=2*len(result['states']), scope=contract['qualification_scope'],
        stop_policy='New one-shot all-state reference; first error stops, no production evaluation, repair or retry.')
    write(control/'reference_protocol.json', reference_protocol)
    assert all(sha(root/name) == pin for name, pin in bindings.items())
    print(json.dumps(dict(status='reference_frozen_not_executed', actual_states=len(result['states']), fresh_HP=2*len(result['states']))))


if __name__ == '__main__':
    main()
