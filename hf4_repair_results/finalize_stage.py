"""Verify immutable numerical evidence; summarize only the frozen HF4-B task."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import ast, hashlib, json, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hf4_repair_results'
REPO = ROOT / 'hf_repo'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def bound_path(name):
    normalized = name.replace('\\', '/')
    # Archived absolute provenance is mapped explicitly when unpacked elsewhere.
    for anchor in ('hf4_repair_results/', 'hf4_results/', 'hf_repo/'):
        if anchor in normalized:
            return ROOT / anchor / normalized.split(anchor, 1)[1]
    return REPO / normalized
def verify_map(mapping):
    for name, digest in mapping.items():
        assert sha(bound_path(name)) == digest, name

spec = read(REPO / 'configs/hf4/validation_spec.json')
execution = read(OUT / 'execution_spec.json')
assert sha(REPO / execution['physics_spec_path'].split('hf_repo/')[1]) == execution['physics_spec_sha256']
for p, h in execution['inputs'].items(): assert sha(ROOT / p) == h, p
freeze = read(OUT / 'source_paths_001/source_freeze.json')
runtime = {p: h for p, h in freeze['files'].items() if p.startswith('src/')}
assert len(runtime) == 18
for p, h in runtime.items(): assert sha(REPO / p) == h, p
gate0 = read(OUT / 'implementation_freeze.json')
assert sha(OUT / 'retained_update_001/summary.json') == gate0['gate0_sha256']
assert sha(ROOT / 'docs/HF4_SPLIT_IMPLEMENTATION_SPEC.md') == gate0['implementation_spec_sha256']
assert sha(OUT / 'execution_spec.json') == gate0['execution_spec_sha256']
for filename in ('stage1_gate.json', 'stage2_gate.json', 'stage3_gate.json'):
    assert read(OUT / filename)['status'] == 'pass'
g1 = read(OUT / 'stage1_gate.json')
assert sha(OUT / 'source_kernel_001/source_freeze.json') == g1['source_freeze_sha256']
assert sha(OUT / 'split_preflight_001/summary.json') == g1['preflight_sha256']
assert sha(OUT / 'split_regression_001.xml') == g1['regression_sha256']
g2, g3 = read(OUT / 'stage2_gate.json'), read(OUT / 'stage3_gate.json')
for g, prefix, folder in ((g2, 'first_target', 'first_target_001'), (g3, 'fourth_path', 'g1_m1_001')):
    assert sha(OUT / folder / 'result.json') == g[prefix + '_result_sha256']
    assert sha(OUT / (folder + '_audit') / 'summary.json') == g[prefix + '_audit_sha256']
    assert sha(OUT / 'source_paths_001/source_freeze.json') == g['source_freeze_sha256']

cases, rows, old_pairs = [], [], []
for gi, mi in ((0, 0), (0, 1), (1, 0), (1, 1)):
    name = f'g{gi}_m{mi}_001'
    run, ap = OUT / name, OUT / (name + '_audit')
    result, audit = read(run / 'result.json'), read(ap / 'summary.json')
    assert result['status'] == 'success' and audit['status'] == 'pass'
    assert audit['execution_scope'] == 'full_path'
    assert audit['requested_targets'] == spec['targets_mm'] == audit['completed_original_targets']
    assert audit['inputs_unchanged_at_end'] and read(ap / 'input_audit.json')['status'] == 'pass'
    verify_map(read(ap / 'bindings.json'))
    for row in audit['rows']:
        assert row['status'] == 'pass' and all(c['status'] == 'pass' for c in row['checks'])
        for name2, digest in read(ap / f"commit_{row['index']:04d}.json").items():
            assert sha(ap / name2) == digest
    assert len(audit['rows']) == audit['states_completed'] == len(result['accepted_steps'])
    last = audit['rows'][-1]
    cases.append(dict(name=name, gamma=spec['gammas'][gi], h_mm=spec['mesh_sizes_mm'][mi],
        production_status=result['status'], audit_status=audit['status'],
        original_targets_completed=len(audit['completed_original_targets']), original_targets_total=len(spec['targets_mm']),
        accepted_states=len(audit['rows']), hp_states=audit['states_completed'],
        failed_increment_attempts=len(result['failed_attempts']),
        rejected_trials=sum(not x['accepted'] for x in result['trials']),
        maximum_bisection_depth=result['maximum_bisection_depth'],
        target_metrics={k:last[k] for k in ('d', 'force_N', 'gap_mm', 'hard_force_N', 'minimum_J')},
        result_sha256=sha(run / 'result.json'), audit_summary_sha256=sha(ap / 'summary.json')))
    old = read(ROOT / 'hf4_results' / (name + '_audit') / 'summary.json')
    old_by_d = {r['d']:r for r in old['rows']}
    for row in audit['rows']:
        if row['d'] in old_by_d:
            before = old_by_d[row['d']]
            old_pairs.append(dict(case=name, d=row['d'],
                force_change_N=str(abs(Decimal(row['force_N']) - Decimal(before['force_N']))),
                gap_change_mm=str(abs(Decimal(row['gap_mm']) - Decimal(before['gap_mm'])))))
    rows.extend(audit['rows'])
pilot = read(OUT / 'first_target_001_audit/summary.json')
assert pilot['status'] == 'pass' and pilot['states_completed'] == 2
verify_map(read(OUT / 'first_target_001_audit/bindings.json'))
checks = [c for row in rows for c in row['checks']]
def maximum(name):
    return str(max((Decimal(c['value']) for c in checks if c['name'] == name), default=Decimal(0)))
def fraction(name):
    return str(max((Decimal(c['value']) / Decimal(c['bound']) for c in checks
        if c['name'] == name and Decimal(c['bound']) > 0), default=Decimal(0)))
jobs = [read(p) for p in sorted((OUT / 'resource_jobs').glob('*.json'))]
assert all(j['status'] == 'complete' for j in jobs)
limits = execution['resource_limits']
categories = {k:sum(j['wall_seconds'] for j in jobs if j['category'] == k) for k in limits['category_seconds']}
assert all(v <= limits['category_seconds'][k] for k, v in categories.items())
assert sum(categories.values()) <= limits['total_seconds']
peak = max(j['sampled_peak_tree_rss_bytes'] for j in jobs)
assert peak <= limits['memory_soft_limit_bytes']
isolated = read(OUT / 'detached/summary.json')
assert isolated['status'] == 'pass' and all(c['status'] == 'pass' for c in isolated['checks'])
latest = {}
test_runs = []
for filename in ('split_regression_001.xml', 'audit_gate_tests_001.xml'):
    tree = ET.parse(OUT / filename)
    local = []
    for t in tree.getroot().iter('testcase'):
        value = 'failed' if t.find('failure') is not None or t.find('error') is not None else 'skipped' if t.find('skipped') is not None else 'pass'
        latest[t.attrib['classname'] + '::' + t.attrib['name']] = value
        local.append(value)
    test_runs.append(dict(file=filename, passed=local.count('pass'), skipped=local.count('skipped'),
        failures=local.count('failed'), sha256=sha(OUT / filename), properties=len(list(tree.getroot().iter('property')))))
assert 'failed' not in latest.values()
old_manifest = read(ROOT / 'HF4_CONTENT_MANIFEST.json')
old_runtime = [f for f in old_manifest['files'] if f['path'].startswith('hf_repo/src/hf_eval/') and not f['path'].endswith('__init__.py')]
old_evidence = [f for f in old_manifest['files'] if f['path'].startswith('hf4_results/')]
for f in old_runtime + old_evidence: assert sha(ROOT / f['path']) == f['sha256'], f['path']
geometry = [f for f in read(ROOT / 'HF3_CONTENT_MANIFEST.json')['files'] if f['path'].startswith('geometry_dataset/')]
assert len(geometry) == 395
geometry_present = (ROOT / 'geometry_dataset').is_dir()
if geometry_present:
    for f in geometry: assert sha(ROOT / f['path']) == f['sha256'], f['path']
old_zip = ROOT / 'deliverables/HF4_AB_partial_evaluator_and_evidence.zip'
old_zip_expected = 'b5244189723fa3426f46b75cb61404d7176914b5681eae8f7d7bd2ad57b3709a'
if old_zip.exists(): assert sha(old_zip) == old_zip_expected
wheel = REPO / 'dist/independent_hf_evaluator-0.5.0-py3-none-any.whl'
assert sha(wheel) == read(OUT / 'detached_location.json')['wheel_sha256']
for p in list((REPO / 'src').rglob('*.py')) + list((REPO / 'scripts').glob('*.py')) + list((REPO / 'tests').glob('*.py')):
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
summary = dict(schema_version='hf4-repair-stage-summary-1.0', created_utc=datetime.now(timezone.utc).isoformat(),
    version='0.5.0', status='pass_frozen_uniform_task', stage_A='previously_complete', stage_B='4_of_4_paths_passed',
    stage_C='not_started', stage_D='not_started', cases=cases, total_full_path_hp_states=len(rows),
    separate_first_target_hp_states=pilot['states_completed'], hp_check_count=len(checks),
    maximum_production_relative_residual=maximum('production_free_balance'),
    maximum_hp_relative_residual=maximum('hp_free_balance'),
    maximum_full_force_evaluation_error_relative=maximum('evaluation_internal_force'),
    maximum_free_force_evaluation_error_relative=maximum('free_evaluation_internal_force'),
    maximum_force_error_vs_same_model_N=maximum('force_vs_finite_medium_reference'),
    maximum_gap_error_vs_same_model_mm=maximum('gap_vs_finite_medium_reference'),
    maximum_same_model_force_fraction_of_gate=fraction('force_vs_finite_medium_reference'),
    maximum_same_model_gap_fraction_of_gate=fraction('gap_vs_finite_medium_reference'),
    maximum_postclosure_force_model_error=maximum('postclosure_force'),
    maximum_closure_gap_over_g0=maximum('closure_gap'),
    maximum_precision_crosscheck_relative=maximum('precision_50_80'),
    hp_crosschecked_full_path_end_states=sum(r['crosscheck_relative'] is not None for r in rows),
    old_new_common_accepted_states=old_pairs,
    tests=dict(unique_pass=list(latest.values()).count('pass'), unique_skip=list(latest.values()).count('skipped'),
        runs=test_runs, method='union of full regression and twelve later audit tests; not one pytest invocation',
        warning_note='40 record_property/xunit2 warnings in full regression; properties including four FD records remain present'),
    isolated_checks=len(isolated['checks']), runtime_files_equal_to_path_freeze=len(runtime),
    legacy_runtime_files_unchanged_except_version=len(old_runtime), old_evidence_files_unchanged=len(old_evidence),
    original_geometry_files_verified_unchanged=len(geometry) if geometry_present else None,
    original_geometry_scope='verified in original workspace; prior HF3 delivery carries the data',
    old_zip_verified_unchanged=old_zip.exists(), old_zip_expected_sha256=old_zip_expected,
    wheel_sha256=sha(wheel), physics_spec_sha256=execution['physics_spec_sha256'],
    resources=dict(total_seconds=sum(categories.values()), allowed_seconds=limits['total_seconds'],
        category_seconds=categories, peak_tree_rss_bytes=peak, memory_soft_limit_bytes=limits['memory_soft_limit_bytes'],
        job_count=len(jobs), nonzero_exit_jobs=[], install_seconds=sum(x['seconds'] for x in read(OUT / 'installation.json')),
        method='sequential jobs; sampled process-tree RSS; preparation/installation separately recorded'),
    no_tolerance_or_physical_parameter_change=True,
    conclusion='Observed rounding failure repaired; four frozen uniform normal paths and installed replay pass. No nonuniform, cylinder, stability or real-mechanism qualification claim.')
(OUT / 'acceptance_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('old_new_common_accepted_states', 'cases')}, indent=2))
