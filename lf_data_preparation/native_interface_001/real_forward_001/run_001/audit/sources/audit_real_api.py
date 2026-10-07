"""Fresh saved-state reference after one real native API call; original math reused."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
import argparse
import hashlib
import shutil
import sys

parser = argparse.ArgumentParser(description=__doc__)
for name in ('repo', 'input', 'output', 'contract'):
    parser.add_argument('--'+name, type=Path, required=True)
parser.add_argument('--time-limit', type=float, required=True)
ARGS = parser.parse_args()
ROOT = ARGS.repo.resolve()
resolve = lambda path: (path if path.is_absolute() else ROOT/path).resolve()
ARGS.input, ARGS.output, ARGS.contract = map(resolve, (ARGS.input, ARGS.output, ARGS.contract))
SCRIPTS = ROOT/'hf_repo/scripts'
AUDIT_PIN = '331eb1d5406b6d6538d838da823e214201b5ec26c8fac9f7f0bc77f23b8a1678'
assert hashlib.sha256((SCRIPTS/'audit_native_mean.py').read_bytes()).hexdigest() == AUDIT_PIN
sys.path[:0] = [str(Path(__file__).resolve().parent), str(SCRIPTS)]
import audit_native_mean as original_audit
original_audit.STARTED = STARTED  # Timing alias only: inherited summary/stdout cover the whole wrapper.
from audit_native_mean import Audit, GATES, RSS_LIMIT
from audit_native_force import canonical_hash, npz, read, require, same_arrays, sha, verify_descriptor, verify_fields, write
from reference_card_builder import BASE, MATH_PINS, STAGE, STRUCTURAL_PINS, gates_from_source, verify_production
import numpy as np


class RealAPIAudit(Audit):
    """Only task/source loading and whole-helper resource observations are adapted."""
    def __init__(self, args):
        super().__init__(args)
        self.repo = ROOT
        self.control = self.stage.parent
        self.contract_file = ARGS.contract
        self.check(self.limit == 180. and self.stage == ROOT/STAGE/'run_001'
            and self.output == self.stage/'audit' and self.contract_file == self.control/'reference_contract.json',
            'Wrong new real API reference scope')

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, 'Whole-helper independent API reference time limit exceeded')
        require(self.peak <= RSS_LIMIT, 'Independent API reference sampled RSS exceeds 8 GiB')
        require(not (self.control/'stop_requested.txt').exists(), 'Independent API reference stop requested')

    def lifecycle(self, status, error=None):
        write(self.output/'lifecycle.json', dict(status=status, error=error,
            elapsed_seconds=perf_counter()-STARTED, HP_calls_started=self.hp_started,
            HP_calls_completed=self.hp_completed, checks_completed=self.checks,
            accepted_states_completed=len(self.rows), sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            time_scope='Whole wrapper/import/load/HP/scatter/serialization lifetime',
            stop_policy='First failure stops; no production evaluation, solve, retry or repair'))

    def load(self):
        self.bind(self.contract_file)
        contract = read(self.contract_file)
        self.check(contract['schema_version'] == 'native-real-api-reference-contract-1.0'
            and contract['production_stage'] == STAGE+'/run_001'
            and contract['limits'] == dict(helper_seconds=self.limit, outer_seconds=210, sampled_RSS_bytes=RSS_LIMIT)
            and contract['targets_mm'] == [0., .001] and contract['gates'] == GATES
            and contract['new_reference_status'] == 'not_executed' and contract['reference_budget_basis'].strip(),
            'Wrong explicit new reference contract')
        reference_protocol_file = self.control/'reference_protocol.json'
        self.bind(reference_protocol_file)
        reference_protocol = read(reference_protocol_file)
        self.check(reference_protocol['schema_version'] == 'native-real-api-reference-protocol-1.0'
            and reference_protocol['sampled_RSS_bytes'] == RSS_LIMIT
            and reference_protocol['phases']['reference']['helper_seconds'] == self.limit
            and reference_protocol['phases']['reference']['outer_seconds'] == 210
            and reference_protocol['actual_accepted_states'] == contract['accepted_states']
            and reference_protocol['fresh_HP_calls_required'] == contract['fresh_HP_calls_required'], 'Wrong actual reference protocol')
        for name, pin in reference_protocol['bindings'].items():
            self.bind(self.repo/name, pin)
        protocol, receipt, result, current = verify_production(self.repo, self.bind)
        self.check(contract['production_protocol_sha256'] == sha(self.control/'production_protocol.json')
            and contract['production_receipt_sha256'] == sha(self.stage/'execution_receipt.json')
            and contract['production_launch_sha256'] == sha(self.control/'production_launch.json')
            and contract['production_result_sha256'] == receipt['result_sha256']
            and contract['current_sources'] == current and contract['baseline_commit'] == protocol['baseline_commit'],
            'Actual new complete production identity differs')
        reference_sources = contract['reference_sources']
        required = dict(current, **{'hf_repo/scripts/'+name: pin for name, pin in MATH_PINS.items()},
            **{(Path(__file__).with_name(name)).relative_to(self.repo).as_posix(): sha(Path(__file__).with_name(name))
               for name in ('audit_real_api.py', 'reference_card_builder.py')})
        self.check(reference_sources == required and len(required) == len({Path(name).name for name in required}) == 34,
            'Reference source closure differs')
        for name, pin in reference_sources.items():
            self.bind(self.repo/name, pin)
            destination = self.output/'sources'/Path(name).name
            shutil.copyfile(self.repo/name, destination); self.bind(destination, pin)
            self.sources[name] = pin
        self.check(gates_from_source(SCRIPTS/'run_split_average_demo.py') == GATES == protocol['gates'], 'Original gates changed')
        for path in (self.contract_file, self.control/'production_protocol.json', self.stage/'execution_receipt.json'):
            shutil.copyfile(path, self.output/path.name)
        baseline_file = self.repo/BASE/'input_inventory.json'
        self.bind(baseline_file, 'e0b5ccd8defb0f1c8d8d6cb7d8501844e8639ccc010b58f7d362e7f2dbca0b6b')
        row = read(baseline_file)['case']
        structural = {key: row[key] for key in STRUCTURAL_PINS}
        self.check(structural == contract['structural_inputs'] and protocol['geometry_file'] == row['geometry_file']
            and protocol['task_file'] == row['task_file'] and protocol['settings'] == read(baseline_file)['settings'],
            'Original explicit no-workpiece physics or structural inputs changed')
        for key, name in structural.items():
            self.bind(self.repo/name, row[STRUCTURAL_PINS[key]])
        self.origin, self.result_file = self.stage/'result', self.stage/'result/result.json'
        verify_descriptor(result)
        self.check(result['schema_version'] == 'hf-native-mean-result-1.0' and result['status'] == 'success'
            and all(result[key] is True for key in ('production_converged', 'target_reached', 'task_target_executed', 'lift_origin_zero', 'lift_shape_zero'))
            and result['targets_mm'] == [0., .001] and result['task_target_mm'] == .001 and result['target_origin'] == 0.
            and result['backend'] == 'numpy' and result['matrix_units'] == 'N/mm' and result['k_out_N_per_mm'] == 0.
            and result['force_scale_per_length'] == 20. and result['failure'] is None
            and all(result[key] is False for key in ('equilibrium_qualified', 'independent_HP_qualified', 'HF_qualified'))
            and 'response_mode' not in result and 'tangent_execution' not in result and 'initial_guess' not in result,
            'Default complete/full/tangent path or producer qualification changed')
        model_file = self.origin/result['model']['arrays_path']
        model_json = self.origin/result['model']['descriptor_path']
        self.bind(model_file, result['model']['arrays_sha256']); self.bind(model_json, result['model']['descriptor_file_sha256'])
        model, metadata = npz(model_file), read(model_json)
        verify_descriptor(metadata); verify_fields(model, metadata['arrays']['fields'])
        same_arrays(model, npz(self.repo/row['prior_model_file']), 'Prior intrinsic arrays only; no inherited qualification')
        task, prior_task = read(self.repo/protocol['task_file']), read(self.repo/row['prior_task_file'])
        physical = set(prior_task)-{'task_id', 'purpose', 'parameter_origin', 'description', 'input'}
        self.check(all(task[key] == prior_task[key] for key in physical)
            and task['input'] == dict(prior_task['input'], target_mm=.001) and task['case_family'] == 'gripper'
            and task['workpiece'] is None and 'path' not in task, 'Explicit prior task physics changed')
        self.check(len(model) == 23 and metadata['schema_version'] == 'hf-native-project-model-1.0'
            and metadata['descriptor_sha256'] == result['model']['descriptor_sha256']
            and metadata['arrays']['sha256'] == sha(model_file) and metadata['task'] == task
            and metadata['task_sha256'] == canonical_hash(task) == result['task_sha256'], 'Ordinary model/task declaration differs')
        source = metadata['source_geometry']
        expected_source = dict(source, snapshot={key: 'model/'+path for key, path in source['snapshot'].items()})
        self.check(result['source_geometry'] == expected_source and source['geometry_id'] == row['geometry_id']
            and source['descriptor_file_sha256'] == row['geometry_file_sha256']
            and source['arrays_sha256'] == row['geometry_npz_sha256']
            and source['descriptor_sha256'] == read(self.repo/row['geometry_file'])['descriptor_sha256'], 'Source geometry identity differs')
        for key, pin in (('descriptor', 'geometry_file_sha256'), ('arrays', 'geometry_npz_sha256')):
            self.bind(self.origin/expected_source['snapshot'][key], row[pin])
        edofs = (2*model['connectivity'][:, :, None]+np.arange(2)).reshape(-1, 8)
        self.check(np.array_equal(edofs, model['edofs']) and len(edofs) == 3200
            and np.array_equal(np.setdiff1d(np.arange(6642), model['fixed_dofs']), model['free_dofs'])
            and len(model['fixed_dofs']) == 87 and len(model['free_dofs']) == 6555, 'Real element/fixed/free indexing differs')
        direction_arrays, lifting = npz(self.repo/row['direction_file']), npz(self.repo/row['lifting_file'])
        direction = model['b_in']/np.max(abs(model['b_in'])); direction[model['fixed_dofs']] = 0.
        self.check(direction_arrays.keys() == {'direction', 'multiplier_direction'}
            and direction_arrays['direction'].dtype == np.dtype('float64') and direction_arrays['direction'].shape == (6642,)
            and direction_arrays['direction'].tobytes() == direction.tobytes()
            and hashlib.sha256(direction.tobytes()).hexdigest() == row['direction_array_sha256']
            and float(direction_arrays['multiplier_direction']) == 0. and lifting.keys() == {'lift_origin', 'lift_shape'}
            and all(value.dtype == np.dtype('float64') and value.shape == (6642,) and np.count_nonzero(value) == 0 for value in lifting.values()),
            'Prior direction/zero-lift structural comparison differs from the new saved model')
        states = result['states']
        self.check(len(states) == contract['accepted_states'] == result['accepted_states'] == receipt['accepted_states']
            and contract['fresh_HP_calls_required'] == 2*len(states)
            and contract['state_sha256'] == [item['state_sha256'] for item in states]
            and [item['d'] for item in states if item['is_original_target']] == [0., .001]
            and states[0]['d'] == 0. and states[-1]['d'] == .001
            and all(a['d'] < b['d'] for a, b in zip(states, states[1:]))
            and all(item['target_origin'] == 0. and item['physical_mean_target_mm'] == item['d'] for item in states),
            'Actual accepted-state path coverage differs')
        self.model, self.edofs, self.direction = model, edofs, direction
        self.inventory, self.receipt, self.result = protocol, receipt, result
        self.checkpoint()


def main():
    audit = RealAPIAudit(ARGS)
    try:
        audit.run()  # Original all-N loop, HP80/120, scatter, run_state, GATES and summary.
        require(all(sha(path) == pin for path, pin in audit.bindings.items()), 'Reference bindings changed at final closure')
        audit.checkpoint()
        write(audit.output/'execution_receipt.json', dict(schema_version='native-real-api-reference-execution-1.0',
            status='pass', accepted_states=len(audit.rows), HP_calls_started=audit.hp_started, HP_calls_completed=audit.hp_completed,
            checks_completed=audit.checks, result_sha256=sha(audit.result_file), summary_sha256=sha(audit.output/'summary.json'),
            contract_sha256=sha(audit.contract_file), protocol_sha256=sha(audit.control/'reference_protocol.json'),
            all_bindings_unchanged=True, elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=audit.peak,
            time_limit_seconds=audit.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            candidate_force_calls=0, candidate_tangent_calls=0, solver_calls=0, model_constructions=0,
            qualification_scope='Fresh all actual accepted-state original force/tangent-action/equilibrium gates; no pressure/contact/all-columns/HF5 upgrade.'))
        audit.checkpoint()
    except Exception as error:
        audit.lifecycle('not_pass', repr(error))
        write(audit.output/'summary.json', dict(schema_version='native-mean-independent-audit-1.0', status='not_pass',
            error=repr(error), states=audit.rows, accepted_states=len(audit.rows), checks_completed=audit.checks,
            HP_calls_started=audit.hp_started, HP_calls_completed=audit.hp_completed,
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=audit.peak))
        write(audit.output/'execution_receipt.json', dict(schema_version='native-real-api-reference-execution-1.0', status='not_pass',
            error=repr(error), accepted_states=len(audit.rows), HP_calls_started=audit.hp_started, HP_calls_completed=audit.hp_completed,
            checks_completed=audit.checks, elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=audit.peak))
        raise


if __name__ == '__main__':
    main()
