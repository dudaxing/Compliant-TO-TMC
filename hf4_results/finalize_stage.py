"""Verify recorded evidence and write an explicit PARTIAL HF4 stage summary."""
from pathlib import Path
from decimal import Decimal
import hashlib,json
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1];out=root/'hf4_results';repo=root/'hf_repo'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
spec=read(repo/'configs/hf4/validation_spec.json');freeze=read(out/'production_source_freeze.json')
assert all(sha(repo/p)==h for p,h in freeze['files'].items())
assert sha(repo/'configs/hf4/validation_spec.json')==read(out/'input_freeze.json')['files']['hf_repo/configs/hf4/validation_spec.json']
cases=[];rows=[]
for gi,mi in [(0,0),(0,1),(1,0),(1,1)]:
    name=f'g{gi}_m{mi}_001';run=out/name;ap=out/(name+'_audit')
    result,meta,audit=read(run/'result.json'),read(run/'metadata.json'),read(ap/'summary.json')
    assert read(ap/'input_audit.json')['status']=='pass'
    for key,digest in read(ap/'bindings.json').items():
        path=Path(key)
        if not path.is_absolute():path=repo/path
        assert sha(path)==digest
    for row in audit['rows']:
        for key,digest in read(ap/f"commit_{row['index']:04d}.json").items():assert sha(ap/key)==digest
    expected='failed' if (gi,mi)==(1,1) else 'success'
    assert result['status']==expected
    assert audit['status']==('not_pass' if expected=='failed' else 'pass')
    assert all(r['status']=='pass' for r in audit['rows'])
    case=dict(name=name,gamma=spec['gammas'][gi],h_mm=spec['mesh_sizes_mm'][mi],
        production_status=result['status'],audit_status=audit['status'],
        original_targets_completed=sum(s['is_original_target'] for s in result['accepted_steps']),
        original_targets_total=len(spec['targets_mm']),accepted_states=len(result['accepted_steps']),
        hp_states=audit['states_completed'],reached_d_mm=result['reached_displacement'],
        failed_attempts=len(result['failed_attempts']),rejected_trials=sum(not x['accepted'] for x in result['trials']),
        maximum_bisection_depth=result['maximum_bisection_depth'],target_metrics=result['target_metrics'],
        metadata_sha256=sha(run/'metadata.json'),audit_summary_sha256=sha(ap/'summary.json'))
    if case['target_metrics'] is not None:
        # Keep a concise public target, not duplicated field arrays.
        last=audit['rows'][-1]
        case['target_metrics']={k:last[k] for k in ('d','force_N','gap_mm','hard_force_N','minimum_J')}
    cases.append(case);rows.extend(audit['rows'])
checks=[c for r in rows for c in r['checks']]
max_value=lambda name:max((Decimal(c['value']) for c in checks if c['name']==name),default=Decimal(0))
jobs=[read(p) for p in sorted((out/'resource_jobs').glob('*.json'))]
assert all(j['status'] in ('complete','failed') for j in jobs)
categories={k:sum(j['wall_seconds'] for j in jobs if j['category']==k) for k in spec['resource_limits']['category_seconds']}
assert all(v<=spec['resource_limits']['category_seconds'][k] for k,v in categories.items())
assert sum(categories.values())<=spec['resource_limits']['total_seconds']
assert max(j['sampled_peak_tree_rss_bytes'] for j in jobs)<=spec['resource_limits']['memory_soft_limit_bytes']
isolated=read(out/'detached/summary.json');assert isolated['status']=='pass'
latest={}
for filename in ('regression_001.xml','input_audit_tests_001.xml'):
    for t in ET.parse(out/filename).getroot().iter('testcase'):
        latest[t.attrib['classname']+'::'+t.attrib['name']]='failed' if t.find('failure') is not None or t.find('error') is not None else 'skipped' if t.find('skipped') is not None else 'pass'
assert 'failed' not in latest.values()
old=read(root/'HF3_CONTENT_MANIFEST.json')
datafiles=[f for f in old['files'] if f['path'].startswith('geometry_dataset/')]
assert len(datafiles)==395
assert all(sha(root/f['path'])==f['sha256'] for f in datafiles)
runtime_old=[f for f in old['files'] if f['path'].startswith('hf_repo/src/hf_eval/') and not f['path'].endswith('__init__.py')]
assert all(sha(root/f['path'])==f['sha256'] for f in runtime_old)
summary=dict(schema_version='hf4-ab-stage-summary-1.0',status='partial',stage_A='implemented_and_verified',stage_B='3_of_4_paths_passed',
    stage_C='not_started_precision_gate',stage_D='not_started',version='0.4.0',cases=cases,
    total_accepted_states=len(rows),total_hp_checked_states=len(rows),hp_check_count=len(checks),
    maximum_hp_relative_residual=str(max_value('hp_free_balance')),
    maximum_force_evaluation_error_relative=str(max_value('evaluation_internal_force')),
    maximum_force_error_vs_same_model_N=str(max_value('force_vs_finite_medium_reference')),
    maximum_postclosure_force_model_error=str(max_value('postclosure_force')),
    maximum_closure_gap_over_g0=str(max_value('closure_gap')),
    maximum_precision_crosscheck_relative=str(max_value('precision_50_80')),
    hp_crosschecked_end_states=sum(r['crosscheck_relative'] is not None for r in rows),
    tests=dict(unique_pass=sum(v=='pass' for v in latest.values()),unique_skip=sum(v=='skipped' for v in latest.values()),
               method='union of complete regression and subsequently added input-audit/inventory tests, not one pytest invocation',
               complete_regression='449 passed, 1 skipped',supplement='67 passed, including repeated inventory tests'),
    isolated_checks=len(isolated['checks']),original_geometry_files_unchanged=len(datafiles),
    legacy_runtime_files_unchanged_except_version=len(runtime_old),
    resources=dict(total_seconds=sum(categories.values()),allowed_seconds=1800,category_seconds=categories,
                   peak_tree_rss_bytes=max(j['sampled_peak_tree_rss_bytes'] for j in jobs),
                   install_seconds=sum(x['seconds'] for x in read(out/'installation.json'))),
    preserved_nonzero_exit_jobs=[dict(name=j['name'],category=j['category'],returncode=j['returncode']) for j in jobs if j['status']=='failed'],
    precision_investigation='fixed_state_probe_001/summary.json',update_investigation='fixed_update_probe_001/summary.json',
    no_tolerance_or_physical_parameter_change=True,conclusion='A complete; B partial due to current absolute binary64 displacement/update floor. No general 2D or cylinder contact claim.')
write(out/'acceptance_summary.json',summary)
print(json.dumps({k:summary[k] for k in ('status','stage_A','stage_B','total_hp_checked_states','maximum_hp_relative_residual','tests','resources')},indent=2))
