"""Saved JSON/gzip-JSON and ordinary byte hashes only; no scientific modules or NPZ opening."""
import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path(__file__).resolve().parent
PROD=ROOT/'lf_data_preparation/native_interface_001/batch_forward_001'
REF=ROOT/'lf_data_preparation/native_interface_001/batch_reference_v2_001'
read=lambda p:json.loads(p.read_bytes())
pins_checked={}

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()

def bind(path,pin):
    actual=sha(path);assert actual==pin,(str(path),actual,pin)
    name=path.relative_to(ROOT).as_posix()
    assert name not in pins_checked or pins_checked[name]==actual
    pins_checked[name]=actual

def check_gate(gate):
    assert gate['pass_gate'] is True
    value,limit=Decimal(gate['normalized_error']),Decimal(gate['limit'])
    assert value.is_finite() and value<=limit
    if 'hp80_hp120_error' in gate:
        difference,agreement=Decimal(gate['hp80_hp120_error']),Decimal(gate['reference_limit'])
        assert difference.is_finite() and difference<=agreement

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--labels',nargs='+',choices=('canonical','native_fine'),default=['canonical'])
    args=parser.parse_args()
    assert args.labels in (['canonical'],['canonical','native_fine'])
    prod_protocol=read(PROD/'production_protocol.json');prod_receipt=read(PROD/'run_001/execution_receipt.json')
    bind(PROD/'production_protocol.json','5a0a7253bf7a6f8c44c9d53f744e545d61c0809474fb783d3716075deb305e28')
    bind(PROD/'run_001/execution_receipt.json','0abff20ada48d4c91a8bcba74f31e39d075c1f266d9e6d69bda5eee70289971e')
    assert len(prod_protocol['bindings'])==52 and len(prod_receipt['outputs'])==54
    for name,pin in prod_protocol['bindings'].items():bind(ROOT/name,pin)
    for name,pin in prod_receipt['outputs'].items():bind(ROOT/name,pin)
    old_failed_file=PROD/'run_001/audit/canonical/execution_receipt.json'
    bind(old_failed_file,'f08ceb3050c8ad6a404ad34b7afb0d25eb40423e00e336104de48b863a68f39d')
    old_failed=read(old_failed_file)
    assert old_failed['status']=='not_pass' and old_failed['error']=="KeyError('coords')"
    assert old_failed['accepted_states']==old_failed['HP_calls_started']==old_failed['HP_calls_completed']==0
    cases={}
    for label in args.labels:
        protocol_file=REF/f'reference_protocol_{label}.json';contract_file=REF/f'reference_contract_{label}.json'
        launch_file=REF/f'reference_{label}_launch.json';directory=REF/'run_001/audit'/label
        receipt_file=directory/'execution_receipt.json';raw_file=directory/'summary.json';qualified_file=directory/'qualified_summary.json'
        protocol,contract,launch,receipt,raw,qualified,lifecycle=map(read,
            (protocol_file,contract_file,launch_file,receipt_file,raw_file,qualified_file,directory/'lifecycle.json'))
        n=4;hp=8;helper,outer=(240,270) if label=='canonical' else (900,960)
        assert protocol['schema_version']=='native-batch-case-reference-protocol-2.0'
        assert contract['schema_version']=='native-batch-case-reference-contract-2.0'
        assert receipt['schema_version']=='native-batch-case-reference-execution-2.0'
        assert protocol['case_label']==contract['case_label']==receipt['case_label']==label
        assert launch['phase']=='reference_'+label and launch['status']==receipt['status']==lifecycle['status']==raw['status']==qualified['status']=='pass'
        assert launch['invocations']==1 and launch['exit_code']==0 and launch['stop_reason'] is None
        assert launch['all_bindings_unchanged'] is receipt['all_bindings_unchanged'] is True
        assert launch['protocol_sha256']==receipt['protocol_sha256']==sha(protocol_file)
        assert launch['bindings']==protocol['bindings'] and len(protocol['bindings'])==134
        phase=protocol['phases']['reference_'+label]
        assert phase['helper_seconds']==contract['limits']['helper_seconds']==receipt['time_limit_seconds']==helper
        assert phase['outer_seconds']==contract['limits']['outer_seconds']==launch['outer_seconds']==outer
        assert receipt['elapsed_seconds']<=helper and launch['elapsed_seconds']<=outer
        assert protocol['sampled_RSS_bytes']==receipt['sampled_RSS_limit_bytes']==launch['sampled_RSS_limit_bytes']==8589934592
        assert receipt['peak_sampled_RSS_bytes']<=8589934592 and launch['peak_sampled_tree_RSS_bytes']<=8589934592
        assert lifecycle['error'] is None and lifecycle['elapsed_seconds']<=receipt['elapsed_seconds']
        assert not any(receipt.get(k) for k in ('error','exception','stop_reason','finalization_exception'))
        assert contract['production_stage']==PROD.relative_to(ROOT).as_posix() and contract['reference_stage']==REF.relative_to(ROOT).as_posix()
        assert protocol['actual_accepted_states']==contract['accepted_states']==receipt['accepted_states']==raw['accepted_states']==qualified['accepted_states']==lifecycle['accepted_states_completed']==n
        assert protocol['fresh_HP_calls_required']==contract['fresh_HP_calls_required']==hp
        for record in (receipt,raw,qualified,lifecycle):assert record['HP_calls_started']==record['HP_calls_completed']==hp
        assert receipt['checks_completed']==raw['checks_completed']==qualified['checks_completed']==lifecycle['checks_completed']
        assert receipt['summary_sha256']==sha(raw_file)==qualified['original_summary']['sha256']
        assert qualified['original_summary']['path']=='summary.json'
        assert receipt['qualified_summary_sha256']==sha(qualified_file) and receipt['contract_sha256']==sha(contract_file)
        assert all(qualified[k]==v for k,v in raw.items() if k not in ('alias','qualification'))
        assert set(qualified)-set(raw)=={'case_label','audited_targets_mm','task_target_mm','original_summary','metadata_adaptation'}
        assert qualified['case_label']==label and qualified['audited_targets_mm']==[0.0,0.005,0.01,0.025] and qualified['task_target_mm']==0.025
        for name,pin in protocol['bindings'].items():bind(ROOT/name,pin)
        for group in (raw['input_bindings'],raw['source_bindings']):
            for name,pin in group.items():bind(ROOT/name,pin)
        assert len(raw['source_bindings'])==35
        assert len([name for name in raw['source_bindings'] if name.startswith('hf_repo/src/hf_eval/')])==28
        assert raw['source_bindings']==contract['reference_sources']
        assert raw['HP_matrix_columns_exhaustively_checked'] is False and raw['full_element_and_DOF_coverage'] is True
        assert raw['gates']==contract['gates']==prod_protocol['gates']
        assert all(receipt[k]==0 for k in ('candidate_force_calls','candidate_tangent_calls','solver_calls','model_constructions'))
        result_file=PROD/'run_001'/label/'result.json';result=read(result_file)
        assert sha(result_file)==receipt['result_sha256']==raw['result_sha256']==contract['production_result_sha256']
        assert raw['input_bindings'][result_file.relative_to(ROOT).as_posix()]==sha(result_file)
        assert contract['state_sha256']==[r['state_sha256'] for r in result['states']]
        assert len(raw['states'])==n and result['accepted_states']==n
        ne,ndof=result['counts']['cells'],result['counts']['dofs']
        state_reports=[]
        for index,(row,original) in enumerate(zip(raw['states'],result['states'],strict=True)):
            assert row['index']==index and row['status']=='pass' and row['HP_calls']==2
            assert row['state_sha256']==original['state_sha256'] and row['target_mm']==original['d']
            assert row['elements_compared']==ne and row['global_DOFs_compared']==ndof
            assert row['local_force_entries_compared']==row['local_tangent_entries_compared']==ne*8*3
            assert row['full_matrix_entries_assembly_checked']==ne*64
            state_directory=directory/f'accepted_{index:03d}'
            assert read(state_directory/'summary.json')==row
            for item in row['checks']:check_gate(item)
            for key in ('force_checks','tangent_checks','augmented_checks'):
                for gate in row[key].values():check_gate(gate)
            check_gate(row['CSC_total_action_check'])
            for key in ('local_force_worst','local_tangent_worst'):
                for gate in row[key]:check_gate(gate)
            assert Decimal(row['metrics']['minimum_J'])>0
            assert len(row['references'])==2
            payloads=[*row['references'],*[row[key] for key in ('raw_fixture','global_references','exact_element_gates',
                'global_differences','equations','actions','rounded_kinematics','independent_total_matrix')]]
            for artifact in payloads:bind(directory/artifact['path'],artifact['sha256'])
            with gzip.open(directory/row['exact_element_gates']['path'],'rt',encoding='utf-8') as stream:
                gates=json.load(stream)
            count=0
            for kind in ('force','tangent'):
                assert gates[kind]['component_order']==['total','material','regularization']
                components=gates[kind]['per_element'];assert len(components)==3
                for entries in components:
                    assert len(entries)==ne
                    for gate in entries:check_gate(gate);count+=1
            assert count==ne*6
            state_reports.append(dict(index=index,d_mm=original['d'],state_sha256=original['state_sha256'],HP_calls=2,
                cells=ne,DOFs=ndof,actual_saved_per_element_gates=count,saved_scalar_gate_count=len(row['checks']),
                no_numeric_re_evaluation=True))
        cases[label]=dict(status='pass_saved_only',actual_N=n,new_HP_started=hp,new_HP_completed=hp,
            checks_completed=receipt['checks_completed'],helper_seconds=receipt['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
            lifecycle_seconds=lifecycle['elapsed_seconds'],summary_serialization_seconds=raw['elapsed_seconds'],
            helper_RSS_bytes=receipt['peak_sampled_RSS_bytes'],outer_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
            protocol_sha256=sha(protocol_file),contract_sha256=sha(contract_file),launch_sha256=sha(launch_file),receipt_sha256=sha(receipt_file),
            raw_summary_sha256=sha(raw_file),qualified_summary_sha256=sha(qualified_file),lifecycle_sha256=sha(directory/'lifecycle.json'),
            result_sha256=sha(result_file),response_sha256=sha(PROD/'run_001'/label/'response.json'),
            protocol_bindings=134,source_closure=35,raw_qualified_mathematical_records_identical=True,states=state_reports)
    report=dict(schema_version='native-batch-reference-v2-saved-closure-review-1.0',status='pass_saved_only',blocking_findings=[],
        reviewed_utc=datetime.now(timezone.utc).isoformat(),labels_actually_reviewed=args.labels,cases=cases,
        production_unchanged=dict(bound_inputs=52,saved_outputs=54,source_count=28,V1_failed_HP=0,V1_failed_receipt_sha256=sha(old_failed_file)),
        unique_raw_files_checked=len(pins_checked),raw_identity_sha256=pins_checked,
        review_recipe_sha256=sha(Path(__file__)),both_case_reference_closure=len(args.labels)==2,
        runtime_scope='Actual saved records/JSON/gzip-JSON gate comparisons and ordinary file hashes; no reference/core imported and no HP or array re-evaluation',
        qualifications=['Fresh recorded all-state/full-elements/real-DOFs mechanical force and declared PORT-direction tangent reference only',
            'No all-column HP, energy qualification, contact/clamp/pressure, mesh convergence/ranking or whole HF5 qualification',
            'Original production responses remain unchanged and still have no reference/view supplied; qualified export and views require separate actual future phase'],
        activities=dict(candidate_imports=0,HF_imports=0,NPZ_loads=0,scientific_array_calculations=0,F=0,T=0,solver=0,HP=0,
            model_constructions=0,tests=0,plots=0,formal_writes=0,phase_invocations=0))
    target=OUT/('dual_saved_review.json' if len(args.labels)==2 else 'canonical_saved_review.json')
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(path=str(target),sha256=sha(target),status=report['status'],labels=args.labels,unique_files=len(pins_checked))))

if __name__=='__main__':main()
