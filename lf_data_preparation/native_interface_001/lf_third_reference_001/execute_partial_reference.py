"""L-TREF1: independent HP reference of new LF loading1.20 and unloading1.15 saved states.

B850 run_state and aa86 workpiece_checks are inherited unchanged. Only the
bound selected-state loader, protocol-authorized resource window, provenance and index metadata
are new. This helper neither evaluates production mechanics nor solves.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
for name in ('repo', 'input', 'output', 'protocol'):
    parser.add_argument('--'+name, type=Path, required=True)
parser.add_argument('--time-limit', type=float, required=True)
ARGS = parser.parse_args()
ROOT, PROTOCOL_FILE = ARGS.repo.resolve(), ARGS.protocol.resolve()
STAGE = PROTOCOL_FILE.parent
read_json = lambda path: json.loads(path.read_bytes())


def raw_sha(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


CONTRACT = read_json(PROTOCOL_FILE)
HELPER_LIMIT = CONTRACT['phases']['reference']['helper_seconds']
OUTER_LIMIT = CONTRACT['phases']['reference']['outer_seconds']
authorization = read_json(STAGE/'author/authorization.json')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
if not (CONTRACT['schema_version'] == 'partial-saved-state-independent-reference-card-1.0'
        and CONTRACT['card'] == authorization['card'] == 'L-TREF1'
        and CONTRACT['prepared'] is True and CONTRACT['authorized'] is CONTRACT['executed'] is False
        and authorization['authorized'] is True
        and authorization['authorization_from_direct_human_request'] is True
        and authorization['protocol_sha256'] == raw_sha(PROTOCOL_FILE)
        and authorization['source_baseline_commit'] == CONTRACT['source_baseline_commit'] == head
        and authorization['one_invocation'] is True
        and authorization['helper_seconds'] == HELPER_LIMIT == 900
        and authorization['outer_seconds'] == OUTER_LIMIT == 960
        and authorization['sampled_RSS_bytes'] == CONTRACT['sampled_RSS_bytes'] == 8*1024**3
        and authorization['direct_human_request'].strip()):
    raise ValueError('L-TREF1 requires its actual direct human request and frozen source protocol')
CORE_PATH = 'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference_author/core_audit_mechanical.py'
BODY_PATH = 'hf_repo/scripts/audit_native_workpiece_cycle.py'
CORE_PIN = 'b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5'
BODY_PIN = 'aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938'
if CONTRACT['reference_sources'].get(CORE_PATH) != CORE_PIN or CONTRACT['reference_sources'].get(BODY_PATH) != BODY_PIN:
    raise ValueError('Frozen B850/aa86 composition differs')
if len(CONTRACT['reference_sources']) != 11 or len({Path(name).name for name in CONTRACT['reference_sources']}) != 11:
    raise ValueError('Reference capsule requires eleven distinct dependency basenames')
for name, pin in CONTRACT['reference_sources'].items():
    if raw_sha(ROOT/name) != pin:
        raise ValueError('Reference source changed before import: '+name)
sys.path[:0] = [str((ROOT/CORE_PATH).parent), str(ROOT/'hf_repo/scripts'), str(ROOT/'hf_repo/src')]
from core_audit_mechanical import Audit as CoreAudit, GATES, RSS_LIMIT, MECHANICAL_AVAILABILITY
from audit_native_workpiece_cycle import WorkpieceCycleAudit, GATES as BODY_GATES
from audit_native_force import canonical_hash, npz, read, require, sha, verify_descriptor, verify_fields, write
import numpy as np


class PartialStateAudit(CoreAudit, WorkpieceCycleAudit):
    def __init__(self, args):
        super().__init__(args)
        self.repo, self.workpiece_completed = ROOT, 0
        self.plot_started = self.plot_completed = 0

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, 'L-TREF1 helper time limit exceeded')
        require(self.peak <= RSS_LIMIT, 'L-TREF1 sampled RSS exceeds 8 GiB')
        require(not (STAGE/'stop_requested.txt').exists(), 'L-TREF1 stop requested')

    def bind(self, path, expected=None):
        self.checkpoint()
        pin = super().bind(path,expected)
        self.checkpoint()
        return pin

    def lifecycle(self, status, error=None):
        write(self.output/'lifecycle.json', dict(status=status, error=error,
            elapsed_seconds=perf_counter()-STARTED, HP_calls_started=self.hp_started, HP_calls_completed=self.hp_completed,
            checks_completed=self.checks, accepted_mechanical_states_completed=len(self.rows),
            workpiece_states_completed=self.workpiece_completed,JAX_module_loaded=('jax' in sys.modules),AD_or_JIT_calls_by_wrapper=0, plot_started=self.plot_started,
            plot_completed=self.plot_completed, plot_mechanical_hooks_monitored=False,
            plot_zero_mechanics_basis='Pinned pure source module; existing reference JSON only, no dynamic mechanics hooks',
            sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            stop_policy='One approved window; first error stops, no repair, retry, extension, production evaluation or force'))

    def load(self):
        c = CONTRACT
        self.check(self.stage == self.repo/c['production_stage'] and self.output == self.repo/c['reference_output']
            and self.limit == HELPER_LIMIT > 0.
            and c['phases']['reference']['outer_seconds'] == OUTER_LIMIT >= HELPER_LIMIT and c['sampled_RSS_bytes'] == RSS_LIMIT
            and c['expected_accepted_states'] == 2 and c['expected_new_HP_calls'] == 4
            and c['selected_accepted_indices'] == [13,14] and c['targets_mm'] == [1.2,1.15]
            and c['original_target_indices'] == [13,14] and c['production_accepted_states'] == 25
            and c['gates'] == GATES == BODY_GATES, 'L-TREF1 scope/resource/original gates differ')
        self.bind(PROTOCOL_FILE)
        for name, pin in c['bindings'].items():
            self.bind(self.repo/name, pin)
        for name, pin in c['reference_sources'].items():
            destination = self.output/'sources'/Path(name).name
            shutil.copyfile(self.repo/name, destination)
            self.bind(destination, pin)
            self.sources[name] = pin
        own = Path(__file__).resolve().relative_to(self.repo).as_posix()
        self.sources[own] = self.bind(Path(__file__).resolve(), c['bindings'][own])
        own_copy = self.output/'sources'/Path(own).name
        shutil.copyfile(Path(__file__).resolve(), own_copy)
        self.bind(own_copy,c['bindings'][own])
        plot_source = self.repo/c['plot_source']
        plot_pin = c['bindings'][c['plot_source']]
        self.sources[c['plot_source']] = self.bind(plot_source,plot_pin)
        plot_copy = self.output/'sources'/plot_source.name
        shutil.copyfile(plot_source,plot_copy)
        self.bind(plot_copy,plot_pin)
        self.plot_source, self.plot_source_pin = plot_source, plot_pin
        shutil.copyfile(PROTOCOL_FILE, self.output/'protocol.json')
        receipt = read(self.stage/'execution_receipt.json')
        launch = read(self.repo/c['production_launch_file'])
        self.check(receipt['status'] == launch['status'] == 'pass' and launch['invocations'] == 1
            and launch['exit_code'] == 0 and launch['stop_reason'] is None and launch['completed_utc']
            and receipt['last_scientific_or_display_phase'] == 'convergence' and receipt['output_identity_seal'] == 'complete_inside_original_helper_window'
            and receipt['accepted_states'] == c['production_accepted_states'] == 25
            and receipt['cached_production_gates']['passed'] is True
            and receipt['counts']['api_started'] == receipt['counts']['api_completed'] == 1
            and receipt['requested_absolute_targets_mm'] == c['production_targets_mm']
            and receipt['zero_start'] is True and receipt['saved_parent_or_state_used'] is False
            and receipt['extend_path'] is False and receipt['default_installations_by_wrapper'] == 0
            and receipt['HP_calls'] == receipt['JIT_calls'] == 0
            and launch['protocol_sha256'] == receipt['protocol_sha256'] == sha(self.repo/c['production_protocol_file']),
            'Actual closed zero-start LF producer records differ')
        self.origin = self.stage/c['production_result_dir']
        self.result_file = self.origin/'result.json'
        result, response = read(self.result_file), read(self.origin/'response.json')
        verify_descriptor(result)
        self.check(result['schema_version'] == 'hf-native-mean-result-1.2' and result['status'] == 'success'
            and result['scope'] == 'native_explicit_mean_displacement_path'
            and result['targets_mm'] == c['production_targets_mm'] and result['accepted_states'] == 25
            and result['target_origin'] == 0. and result['lift_origin_zero'] is result['lift_shape_zero'] is True
            and result['path_kind'] == 'ordered_cycle' and 'continuation' not in result
            and result['backend'] == 'numpy' and result['matrix_units'] == 'N/mm'
            and result['force_scale_per_length'] == 20. and result['k_out_N_per_mm'] == 0.
            and result['settings'] == c['production_settings'] and result['initial_guess'] == 'port_projection'
            and result['tangent_execution'] == dict(mode='chunk256',element_block_size=256,global_selector_scope='full_batch')
            and all(result[key] == value for key,value in MECHANICAL_AVAILABILITY.items())
            and result['failure'] is None
            and result['path_completed'] is result['loading_peak_reached'] is result['unload_endpoint_reached'] is result['task_target_executed'] is True
            and all(result[key] is False for key in ('equilibrium_qualified','independent_HP_qualified','HF_qualified'))
            and response['status'] == 'success' and response['identity']['result']['sha256'] == sha(self.result_file)
            and response['path']['completed'] is response['path']['task_target_executed'] is True
            and response['path']['requested_targets_mm'] == c['production_targets_mm']
            and 'continuation' not in response, 'Actual zero-start LF result/path identity differs')
        self.check(result['call_counts']['force_calls'] == receipt['counts']['force_started']
            and result['call_counts']['force_calls_completed'] == receipt['counts']['force_completed']
            and result['call_counts']['tangent_calls'] == receipt['counts']['tangent_started']
            and result['call_counts']['tangent_calls_completed'] == receipt['counts']['tangent_completed']
            and result['save_force_calls'] == result['save_tangent_calls'] == 0,
            'Original accepted cache/counters differ; normal rejected trials are not completion equality gates')
        self.check(result['mechanics_source_sha256'] == c['producer_mechanics_source_sha256'], 'Actual producer source epoch differs')
        for name,pin in result['mechanics_source_sha256'].items():
            self.check(sha(self.repo/name) == c['bindings'][name] == pin, 'Saved mechanics source differs from current source')
        model_file, metadata_file = (self.origin/result['model'][key] for key in ('arrays_path','descriptor_path'))
        model, metadata = npz(model_file), read(metadata_file)
        verify_descriptor(metadata); verify_fields(model, metadata['arrays']['fields'])
        task, geometry = read(self.repo/c['task_file']), read(self.origin/'model/source_geometry/geometry.json')
        verify_descriptor(geometry)
        self.check(len(model) == 27 and metadata['schema_version'] == 'hf-native-project-model-1.1'
            and metadata['descriptor_sha256'] == result['model']['descriptor_sha256']
            and metadata['arrays']['sha256'] == result['model']['arrays_sha256'] == sha(model_file)
            and metadata['task'] == task and metadata['task_sha256'] == result['task_sha256'] == canonical_hash(task)
            and task['path'] == dict(kind='ordered_cycle',targets_mm=c['original_targets_mm'])
            and metadata['grid'] == result['grid'] == geometry['grid'] == c['grid']
            and metadata['material'] == c['material'] and task['workpiece'] == c['workpiece']
            and metadata['region_metadata']['counts'] == result['counts'] == c['expected_counts'],
            'Bound LF model/explicit task/material identity differs')
        source = metadata['source_geometry']
        self.check(source['descriptor_sha256'] == geometry['descriptor_sha256'] == task['geometry']['descriptor_sha256']
            and source['geometry_id'] == geometry['geometry_id'] == task['geometry']['geometry_id']
            and source['descriptor_file_sha256'] == sha(self.origin/'model/source_geometry/geometry.json')
            and source['arrays_sha256'] == sha(self.origin/'model/source_geometry/geometry.npz')
            and result['source_geometry'] == dict(source,snapshot={key:'model/'+path for key,path in source['snapshot'].items()}),
            'Saved source geometry identity differs')
        counts = c['expected_counts']
        conn = model['connectivity']
        edofs = (2*conn[:,:,None]+np.arange(2)).reshape(-1,8)
        fixed = model['fixed_dofs']
        self.check(conn.shape == (counts['cells'],4) and model['coordinates'].shape == (counts['nodes'],2)
            and np.array_equal(edofs,model['edofs'])
            and np.array_equal(np.setdiff1d(np.arange(counts['dofs']),fixed),model['free_dofs'])
            and len(fixed) == counts['fixed_dofs'], 'Saved real element/fixed/free indexing differs')
        regions, body = metadata['region_metadata'], metadata['region_metadata']['workpiece']
        self.check(body['definition'] == c['workpiece'] and np.array_equal(model['workpiece_dofs'],body['dofs'])
            and np.array_equal(model['workpiece_cells'],body['cells']) and np.array_equal(model['workpiece_nodes'],body['nodes'])
            and np.array_equal(model['workpiece_background_symmetry_overlap_dofs'],body['background_symmetry_overlap_dofs'])
            and regions['fixed_dofs'] == fixed.tolist(), 'Saved fixed workpiece overlay differs')
        direction = model['b_in']/max(abs(model['b_in']))
        direction[fixed] = 0.
        self.check(direction.dtype == np.dtype('float64') and direction.shape == (c['direction']['length'],)
            and c['direction']['length'] == counts['dofs'] and c['direction']['multiplier_direction'] == 0.
            and model['b_in'][np.flatnonzero(model['b_in'])].tolist() == c['direction']['expected_port_weights']
            and np.count_nonzero(direction[fixed]) == 0, 'Actual fixed-compatible PORT direction differs')
        states = result['states']
        self.check(len(states) == c['production_accepted_states'] == 25
            and [row['d'] for row in states] == c['production_targets_mm']
            and [row['original_target_index'] for row in states] == c['production_original_target_indices']
            and [row['leg'] for row in states] == ['origin']+['loading']*13+['unloading']*11
            and all(row['is_original_target'] and row['target_origin'] == 0. and row['physical_mean_target_mm'] == row['d'] for row in states),
            'Actual 25-state zero-start LF producer identity differs')
        self.selected_states = [states[index] for index in c['selected_accepted_indices']]
        self.check([row['d'] for row in self.selected_states] == c['targets_mm']
            and [row['original_target_index'] for row in self.selected_states] == [13,14]
            and [row['state_sha256'] for row in self.selected_states] == c['selected_state_sha256']
            and [row['leg'] for row in self.selected_states] == ['loading','unloading'],
            'Only LF accepted13/14 loading1.20/unloading1.15 may be referenced')
        for file in [self.result_file, metadata_file, model_file]+[self.origin/row[key]['path'] for row in self.selected_states for key in ('state','forces','tangents','matrix')]+[self.origin/row['descriptor_path'] for row in self.selected_states]:
            name = file.relative_to(self.repo).as_posix()
            self.check(receipt['outputs'][name]['sha256'] == c['bindings'][name] == self.bindings[file]
                and receipt['outputs'][name]['bytes'] == file.stat().st_size, 'Saved input differs from actual closed producer seal')
        self.model, self.edofs, self.direction = model, edofs, direction
        self.result, self.metadata, self.receipt = result, metadata, receipt
        self.workpiece_dofs = model['workpiece_dofs']
        self.groups = {name:regions[name]['dofs'] for name in ('support','entity_symmetry','background_symmetry')}
        self.checkpoint()

    def summary_rows(self):
        # Raw reports and top summary both retain actual accepted/original13/14.
        return [dict(deepcopy(record),source_accepted_index=CONTRACT['selected_accepted_indices'][index],
            reference_execution_index=record['index'],original_target_index=row['original_target_index'],leg=row['leg'],
            descriptor_file_sha256=row['descriptor_file_sha256'])
            for index,(record,row) in enumerate(zip(self.rows,self.selected_states))]

    def run(self):
        self.checkpoint(); self.load()
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        self.reference_class = DecimalSplitQ1Reference
        for row in self.selected_states:
            index = row['original_target_index']
            self.run_state(index,row)
            self.workpiece_checks(index,row)
            self.workpiece_completed += 1
        self.check(self.hp_started == self.hp_completed == 4 and len(self.rows) == self.workpiece_completed == 2,
            'Fresh selected endpoint HP/body coverage differs')
        for path,pin in self.bindings.items():
            self.checkpoint()
            self.check(sha(path) == pin, 'Bound source/input changed: '+str(path))
        self.checkpoint()
        self.plot_started = 1
        spec = importlib.util.spec_from_file_location('saved_endpoint_reference_observation',self.plot_source)
        plot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plot)
        self.check(Path(plot.__file__).resolve() == self.plot_source.resolve()
            and sha(self.plot_source) == self.plot_source_pin, 'Bound pure plot module origin differs')
        observation = plot.render_partial_reference_observation(self.output,self.selected_states,CONTRACT['selected_accepted_indices'],self.checkpoint)
        self.plot_completed = 1
        self.checkpoint()
        self.check([row['original_target_index'] for row in observation['states']] == [13,14]
            and [row['accepted_source_index'] for row in observation['states']] == [13,14]
            and [row['state_sha256'] for row in observation['states']] == [row['state_sha256'] for row in self.selected_states], 'Two-state observation identity differs')
        plot_outputs = {name:sha(self.output/name) for name in ('reference_observations.png','reference_observations.json')}
        summary = dict(schema_version='native-workpiece-cycle-independent-audit-1.0',status='pass',
            alias='lf_third_peak_first_unload_reference',case_family='gripper',accepted_states=2,states=self.summary_rows(),
            audited_targets_mm=CONTRACT['targets_mm'],path_kind='ordered_cycle',workpiece=CONTRACT['workpiece'],
            result_sha256=sha(self.result_file),checks_completed=self.checks,HP_calls_started=self.hp_started,HP_calls_completed=self.hp_completed,
            gates=GATES,global_scatter_precision=3000,global_scatter_inexact_trap=True,
            HP_matrix_columns_exhaustively_checked=False,full_element_and_DOF_coverage=True,
            reference_scope='Only new LF accepted13/loading1.20 and14/unloading1.15,13440 elements/27378 DOFs; actual PORT direction,deltaR=0; signed body/holding projections',
            qualification='Only these two selected source states and declared direction. Original15 gates; no full25 LF production path/all columns/stress-energy/pressure/effective clamp/stability/HF5 qualification',
            selected_accepted_indices=[13,14],production_accepted_states=25,
            production_path_completed=self.result['path_completed'],production_task_target_executed=self.result['task_target_executed'],
            production_geometry=deepcopy(self.result['source_geometry']),production_task_sha256=self.result['task_sha256'],
            full_production_path_reference_pass=False,public_API_association_performed=False,
            full_original_path_reference_pass=False,
            contact_qualified=False,clamp_qualified=False,pressure_qualified=False,HF5_qualified=False,
            **MECHANICAL_AVAILABILITY,analytic_HP_energy_scope='Archived independent analytic energy only; no candidate energy comparison',
            private_run_state_source_sha256=CORE_PIN,inherited_workpiece_checker_sha256=BODY_PIN,
            tangent_execution=self.result['tangent_execution'],direction=CONTRACT['direction'],
            direction_array_sha256=hashlib.sha256(self.direction.tobytes()).hexdigest(),
            source_bindings=self.sources,input_bindings={p.relative_to(self.repo).as_posix():pin for p,pin in self.bindings.items()},
            observation_outputs=plot_outputs,plot_started=self.plot_started,plot_completed=self.plot_completed,
            plot_module_origin=self.plot_source.relative_to(self.repo).as_posix(),plot_module_sha256=self.plot_source_pin,
            plot_mechanical_hooks_monitored=False,
            plot_zero_mechanics_basis='Pinned pure module reading only new accepted013/014 summaries; no dynamic hook monitoring',
            independent_reference_contract_sha256=sha(PROTOCOL_FILE),production_response_unchanged=True,
            candidate_force_calls=0,tangent_calls=0,solver_calls=0,model_constructions=0,JIT_calls=0,LF_calls=0,
            producer_mechanics_source_sha256=deepcopy(self.result['mechanics_source_sha256']),
            JAX_module_loaded=('jax' in sys.modules),AD_or_JIT_calls_by_wrapper=0,JAX_scope='Inherited dependencies import/register JAX; no wrapper AD/JIT execution or dynamic hook claim',
            elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=self.peak,time_limit_seconds=self.limit,sampled_RSS_limit_bytes=RSS_LIMIT)
        write(self.output/'summary.json',summary)
        self.checkpoint(); self.lifecycle('pass'); self.checkpoint()
        # Overall terminal status is printed after the one output identity seal.


def main():
    require(ARGS.time_limit == HELPER_LIMIT == 900., 'L-TREF1 requires its explicit protocol/authorization window')
    audit = PartialStateAudit(ARGS)
    error, outputs, complete = None, {}, False
    def failed(exc):
        audit.lifecycle('not_pass',repr(exc))
        write(audit.output/'summary.json',dict(status='not_pass',error=repr(exc),
            states=audit.summary_rows() if hasattr(audit,'result') else [],accepted_states=len(audit.rows),
            workpiece_states_completed=audit.workpiece_completed,HP_calls_started=audit.hp_started,HP_calls_completed=audit.hp_completed,
            plot_started=audit.plot_started,plot_completed=audit.plot_completed,checks_completed=audit.checks,
            full_production_path_reference_pass=False,
            full_original_path_reference_pass=False,
            contact_qualified=False,clamp_qualified=False,pressure_qualified=False,HF5_qualified=False))
    try:
        audit.run()
    except BaseException as exc:
        error = exc; failed(exc)
    try:
        audit.checkpoint()
        for path in audit.output.rglob('*'):
            if path.is_file():
                audit.checkpoint()
                pin = raw_sha(path)
                audit.checkpoint()
                outputs[path.relative_to(ROOT).as_posix()] = dict(sha256=pin,bytes=path.stat().st_size)
        audit.checkpoint(); complete = True
    except BaseException as exc:
        error = error or exc; failed(error)
        for name in ('summary.json','lifecycle.json'):
            outputs.pop((audit.output/name).relative_to(ROOT).as_posix(),None)
    receipt = dict(status='pass' if error is None else 'not_pass',card='L-TREF1',error=repr(error) if error else None,
        protocol_sha256=raw_sha(PROTOCOL_FILE),source_baseline_commit=head,
        selected_accepted_indices=[13,14],original_target_indices=[13,14],HP_calls_started=audit.hp_started,HP_calls_completed=audit.hp_completed,
        accepted_mechanical_states_completed=len(audit.rows),workpiece_states_completed=audit.workpiece_completed,
        plot_started=audit.plot_started,plot_completed=audit.plot_completed,outputs=outputs,
        output_identity_seal='complete_inside_original_helper_window' if complete else 'incomplete_or_skipped_no_closed_window_scientific_hash_retry',
        elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=audit.peak,
        production_F_T_solver_tests_API_calls=0,full25_LF_path_reference_qualified=False)
    write(audit.output/'execution_receipt.json',receipt)
    try:
        audit.checkpoint()
    except BaseException as exc:
        error = error or exc; receipt.update(status='not_pass',final_write_stop=repr(exc),elapsed_seconds=perf_counter()-STARTED)
        write(audit.output/'execution_receipt.json',receipt)
    print(dict(status=receipt['status'],accepted_states=len(audit.rows),HP_calls=audit.hp_completed,checks_completed=audit.checks),flush=True)
    if error is not None: raise error


if __name__ == '__main__':
    main()
