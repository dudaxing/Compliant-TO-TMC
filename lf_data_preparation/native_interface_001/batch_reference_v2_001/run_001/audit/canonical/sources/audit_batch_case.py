"""Fresh all-state batch-case reference with the original native Audit mathematics."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
import argparse
import hashlib
import shutil
import sys

parser = argparse.ArgumentParser(description=__doc__)
for name in ('repo','input','output','contract'):
    parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--case',choices=('canonical','native_fine'),required=True)
parser.add_argument('--time-limit',type=float,required=True)
ARGS=parser.parse_args()
ROOT=ARGS.repo.resolve()
resolve=lambda p:(p if p.is_absolute() else ROOT/p).resolve()
ARGS.input,ARGS.output,ARGS.contract=map(resolve,(ARGS.input,ARGS.output,ARGS.contract))
SCRIPTS=ROOT/'hf_repo/scripts'
assert hashlib.sha256((SCRIPTS/'audit_native_mean.py').read_bytes()).hexdigest()=='331eb1d5406b6d6538d838da823e214201b5ec26c8fac9f7f0bc77f23b8a1678'
sys.path[:0]=[str(Path(__file__).resolve().parent),str(SCRIPTS)]
import audit_native_mean as original_audit
original_audit.STARTED=STARTED  # Timing alias only; original run/math bytes stay unchanged.
from audit_native_mean import Audit,GATES,RSS_LIMIT
from audit_native_force import canonical_hash,npz,read,require,same_arrays,sha,verify_descriptor,verify_fields,write
from reference_case_builder import MATH_PINS,STAGE,PRODUCTION_STAGE,STRUCTURAL_PINS,gates_from_source,verify_batch_production,verify_closed_failed_reference
import numpy as np


class BatchCaseAudit(Audit):
    """Only loading, resource observations and metadata provenance are adapted."""
    def __init__(self,args):
        super().__init__(args)
        self.repo,self.control,self.label,self.contract_file=ROOT,ROOT/STAGE,args.case,ARGS.contract
        self.production_control=ROOT/PRODUCTION_STAGE
        self.check(self.stage==self.production_control/'run_001'/self.label
            and self.output==self.control/'run_001/audit'/self.label
            and self.contract_file==self.control/f'reference_contract_{self.label}.json', 'Wrong case/output reference scope')

    def checkpoint(self):
        self.peak=max(self.peak,self.process.memory_info().rss)
        require(perf_counter()-STARTED<=self.limit,'Whole-helper case reference time limit exceeded')
        require(self.peak<=RSS_LIMIT,'Case reference sampled RSS exceeds 8 GiB')
        require(not (self.control/'stop_requested.txt').exists(),'Case reference stop requested')

    def lifecycle(self,status,error=None):
        write(self.output/'lifecycle.json',dict(status=status,error=error,
            elapsed_seconds=perf_counter()-STARTED,HP_calls_started=self.hp_started,HP_calls_completed=self.hp_completed,
            checks_completed=self.checks,accepted_states_completed=len(self.rows),sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit,sampled_RSS_limit_bytes=RSS_LIMIT,
            time_scope='Whole wrapper/import/load/HP/scatter/serialization lifetime',
            stop_policy='First failure stops; no production, solve, retry or repair'))

    def load(self):
        self.bind(self.contract_file);contract=read(self.contract_file)
        self.check(contract['schema_version']=='native-batch-case-reference-contract-2.0'
            and contract['case_label']==self.label and contract['production_stage']==PRODUCTION_STAGE and contract['reference_stage']==STAGE
            and contract['case_directory']==self.stage.relative_to(self.repo).as_posix()
            and contract['reference_output']==self.output.relative_to(self.repo).as_posix()
            and contract['limits']['helper_seconds']==self.limit and contract['limits']['sampled_RSS_bytes']==RSS_LIMIT
            and contract['limits']['outer_seconds']>self.limit and contract['reference_budget_basis'].strip()
            and contract['targets_mm']==[0.,.005,.010,.025] and contract['gates']==GATES
            and contract['new_reference_status']=='not_executed','Wrong explicit fresh case reference contract')
        reference_protocol_file=self.control/f'reference_protocol_{self.label}.json'
        self.bind(reference_protocol_file);reference_protocol=read(reference_protocol_file)
        self.check(reference_protocol['schema_version']=='native-batch-case-reference-protocol-2.0'
            and reference_protocol['case_label']==self.label and reference_protocol['sampled_RSS_bytes']==RSS_LIMIT
            and reference_protocol['phases']['reference_'+self.label]['helper_seconds']==self.limit
            and reference_protocol['phases']['reference_'+self.label]['outer_seconds']==contract['limits']['outer_seconds']
            and reference_protocol['actual_accepted_states']==contract['accepted_states']
            and reference_protocol['fresh_HP_calls_required']==contract['fresh_HP_calls_required'],'Wrong actual-N reference protocol')
        for name,pin in reference_protocol['bindings'].items():self.bind(self.repo/name,pin)
        protocol,receipt,index,current,(plan,case,result)=verify_batch_production(self.repo,self.label,self.bind)
        self.check(contract['closed_failed_reference']==verify_closed_failed_reference(self.repo,self.bind),'Closed failed V1 context differs')
        self.check(contract['production_protocol_sha256']==sha(self.production_control/'production_protocol.json')
            and contract['production_receipt_sha256']==sha(self.production_control/'run_001/execution_receipt.json')
            and contract['production_launch_sha256']==sha(self.production_control/'production_launch.json')
            and contract['batch_index_sha256']==sha(self.production_control/'run_001/batch/index.json')
            and contract['production_result_sha256']==case['result_sha256'] and contract['production_response_sha256']==case['response_sha256']
            and contract['current_sources']==current and contract['baseline_commit']==protocol['baseline_commit']
            and contract['expected_counts']==protocol['expected_counts'][self.label],'New complete batch/case identity differs')
        required=dict(current,**{'hf_repo/scripts/'+n:p for n,p in MATH_PINS.items()},
            **{Path(__file__).with_name(n).relative_to(self.repo).as_posix():sha(Path(__file__).with_name(n))
                for n in ('audit_batch_case.py','reference_case_builder.py')})
        self.check(contract['reference_sources']==required
            and len(required)==len({Path(n).name for n in required})==35,'Reference source closure differs')
        for name,pin in required.items():
            self.bind(self.repo/name,pin);destination=self.output/'sources'/Path(name).name
            shutil.copyfile(self.repo/name,destination);self.bind(destination,pin);self.sources[name]=pin
        self.check(gates_from_source(SCRIPTS/'run_split_average_demo.py')==GATES==protocol['gates'],'Original gates changed')
        legacy_file=self.repo/contract['legacy_inventory'];self.bind(legacy_file,protocol['bindings'][contract['legacy_inventory']])
        prior=read(legacy_file)['case'];structural={k:prior[k] for k in STRUCTURAL_PINS}
        self.check(structural==contract['structural_inputs'] and plan['geometry']==prior['geometry_file']
            and plan['task']==prior['prior_task_file'],'Prior structural input identities differ')
        for key,name in structural.items():self.bind(self.repo/name,prior[STRUCTURAL_PINS[key]])
        self.origin,self.result_file=self.stage,self.stage/'result.json'
        verify_descriptor(result)
        self.check(result['schema_version']=='hf-native-mean-result-1.0' and result['status']=='success'
            and all(result[k] is True for k in ('production_converged','target_reached','task_target_executed','lift_origin_zero','lift_shape_zero'))
            and result['targets_mm']==contract['targets_mm'] and result['task_target_mm']==.025 and result['target_origin']==0.
            and result['backend']=='numpy' and result['matrix_units']=='N/mm' and result['k_out_N_per_mm']==0.
            and result['force_scale_per_length']==20. and result['failure'] is None
            and all(result[k] is False for k in ('equilibrium_qualified','independent_HP_qualified','HF_qualified'))
            and 'response_mode' not in result and 'tangent_execution' not in result and 'initial_guess' not in result,
            'Default complete/full/tangent task or producer qualification differs')
        model_file,model_json=(self.origin/result['model'][k] for k in ('arrays_path','descriptor_path'))
        self.bind(model_file,result['model']['arrays_sha256']);self.bind(model_json,result['model']['descriptor_file_sha256'])
        model,metadata=npz(model_file),read(model_json)
        verify_descriptor(metadata);verify_fields(model,metadata['arrays']['fields'])
        same_arrays(model,npz(self.repo/prior['prior_model_file']),'Prior intrinsic arrays only; no inherited qualification')
        task=read(self.repo/plan['task'])
        self.check(task==read(self.repo/prior['prior_task_file']) and task['case_family']=='gripper'
            and task['workpiece'] is None and 'path' not in task and task['input']['target_mm']==.025,'Explicit task physics differs')
        self.check(len(model)==23 and metadata['schema_version']=='hf-native-project-model-1.0'
            and metadata['descriptor_sha256']==result['model']['descriptor_sha256']
            and metadata['arrays']['sha256']==sha(model_file) and metadata['task']==task
            and metadata['task_sha256']==canonical_hash(task)==result['task_sha256'],'Ordinary model/task declaration differs')
        source=metadata['source_geometry'];expected_source=dict(source,snapshot={k:'model/'+p for k,p in source['snapshot'].items()})
        self.check(result['source_geometry']==expected_source and source['geometry_id']==prior['geometry_id']
            and source['descriptor_file_sha256']==prior['geometry_file_sha256'] and source['arrays_sha256']==prior['geometry_npz_sha256']
            and source['descriptor_sha256']==read(self.repo/plan['geometry'])['descriptor_sha256'],'Source geometry identity differs')
        for key,pin in (('descriptor','geometry_file_sha256'),('arrays','geometry_npz_sha256')):
            self.bind(self.origin/expected_source['snapshot'][key],prior[pin])
        counts=contract['expected_counts'];ndof=counts['dofs']
        edofs=(2*model['connectivity'][:,:,None]+np.arange(2)).reshape(-1,8)
        self.check(np.array_equal(edofs,model['edofs']) and len(edofs)==counts['cells']
            and len(model['coordinates'])==counts['nodes'] and len(model['b_in'])==ndof
            and np.array_equal(np.setdiff1d(np.arange(ndof),model['fixed_dofs']),model['free_dofs'])
            and len(model['fixed_dofs'])==counts['fixed_dofs'] and len(model['free_dofs'])==counts['free_dofs'],
            'Actual case element/fixed/free indexing differs')
        direction_arrays,lifting=npz(self.repo/prior['direction_file']),npz(self.repo/prior['lifting_file'])
        direction=model['b_in']/np.max(abs(model['b_in']));direction[model['fixed_dofs']]=0.
        self.check(direction_arrays.keys()=={'direction','multiplier_direction'}
            and direction_arrays['direction'].dtype==np.dtype('float64') and direction_arrays['direction'].shape==(ndof,)
            and direction_arrays['direction'].tobytes()==direction.tobytes()
            and hashlib.sha256(direction.tobytes()).hexdigest()==prior['direction_array_sha256']
            and float(direction_arrays['multiplier_direction'])==0. and lifting.keys()=={'lift_origin','lift_shape'}
            and all(v.dtype==np.dtype('float64') and v.shape==(ndof,) and np.count_nonzero(v)==0 for v in lifting.values()),
            'Actual port direction/zero-lift structural comparison differs')
        states=result['states']
        self.check(len(states)==contract['accepted_states']==result['accepted_states']
            and contract['fresh_HP_calls_required']==2*len(states)
            and contract['state_sha256']==[s['state_sha256'] for s in states]
            and [s['d'] for s in states if s['is_original_target']]==contract['targets_mm']
            and states[0]['d']==0. and states[-1]['d']==.025 and all(a['d']<b['d'] for a,b in zip(states,states[1:]))
            and all(s['target_origin']==0. and s['physical_mean_target_mm']==s['d'] for s in states),
            'All actual accepted-state path coverage differs')
        self.model,self.edofs,self.direction=model,edofs,direction
        self.inventory,self.receipt,self.result=protocol,receipt,result
        self.contract,self.plan,self.alias=contract,plan,prior['alias']
        self.checkpoint()


def main():
    audit=BatchCaseAudit(ARGS)
    try:
        audit.run()  # Original raw run/all-N loop/run_state/HP80-120/scatter/GATES.
        original_file=audit.output/'summary.json';original=read(original_file)
        qualified=dict(original,alias=audit.alias,qualification=audit.contract['qualification_scope'],
            case_label=audit.label,audited_targets_mm=audit.contract['targets_mm'],task_target_mm=.025,
            original_summary=dict(path='summary.json',sha256=sha(original_file)),
            metadata_adaptation='Original summary raw preserved; alias/task scope only. All states/math/checks/HP/gates copied unchanged.')
        qualified_file=audit.output/'qualified_summary.json';write(qualified_file,qualified)
        require(all(sha(p)==pin for p,pin in audit.bindings.items()),'Reference bindings changed at final closure')
        audit.checkpoint()
        write(audit.output/'execution_receipt.json',dict(schema_version='native-batch-case-reference-execution-2.0',status='pass',
            case_label=audit.label,accepted_states=len(audit.rows),HP_calls_started=audit.hp_started,HP_calls_completed=audit.hp_completed,
            checks_completed=audit.checks,result_sha256=sha(audit.result_file),summary_sha256=sha(original_file),
            qualified_summary_sha256=sha(qualified_file),contract_sha256=sha(audit.contract_file),
            protocol_sha256=sha(audit.control/f'reference_protocol_{audit.label}.json'),all_bindings_unchanged=True,
            elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=audit.peak,time_limit_seconds=audit.limit,
            sampled_RSS_limit_bytes=RSS_LIMIT,candidate_force_calls=0,candidate_tangent_calls=0,solver_calls=0,model_constructions=0,
            qualification_scope=audit.contract['qualification_scope']))
        audit.checkpoint()
    except Exception as error:
        audit.lifecycle('not_pass',repr(error))
        failure=dict(schema_version='native-batch-case-reference-execution-2.0',status='not_pass',case_label=audit.label,
            error=repr(error),accepted_states=len(audit.rows),HP_calls_started=audit.hp_started,HP_calls_completed=audit.hp_completed,
            checks_completed=audit.checks,elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=audit.peak)
        write(audit.output/'execution_receipt.json',failure)
        # Preserve any original summary; a failure receipt never upgrades a qualified summary.
        raise


if __name__=='__main__':main()
