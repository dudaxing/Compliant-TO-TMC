"""Verify ordinary HF3 artifacts, snapshot compact records, then package a clean Git tree."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPO, OUT = ROOT/'hf_repo', ROOT/'hf3_results'
WHEEL = REPO/'dist/independent_hf_evaluator-0.3.0-py3-none-any.whl'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def verify():
    baseline = read(OUT/'baseline_manifest.json')
    current = {p.relative_to(ROOT/'geometry_dataset').as_posix():sha(p) for p in (ROOT/'geometry_dataset').rglob('*') if p.is_file()}
    assert current == baseline['original_dataset_files'] and len(current) == 395
    for item in baseline['files']:
        assert sha(ROOT/item['path']) == item['sha256']
    for name, digest in baseline['frozen_configs'].items():
        assert sha(REPO/'configs/hf3'/name) == digest
    assert sha(OUT/'baseline/tmc_kernel_0_2_1.py') == baseline['kernel_copy_sha256']
    freeze = read(OUT/'production_source_freeze.json')
    assert set(freeze['files']) == {p.name for p in (REPO/'src/hf_eval').glob('*.py')}
    for name, digest in freeze['files'].items(): assert sha(REPO/'src/hf_eval'/name) == digest
    with zipfile.ZipFile(WHEEL) as z:
        for name in freeze['files']:
            assert z.read('hf_eval/'+name) == (REPO/'src/hf_eval'/name).read_bytes()
    assert sha(WHEEL) == read(OUT/'detached_receipt.json')['wheel_sha256']
    checks = {}
    for folder in ('small_kernel_v3_001', 'strong_kernel_v3_001', 'near_zero_v3_final_001', 'bridge_001', 'bridge_hp_001', 'full_path_hp_001', 'detached'):
        summary = read(OUT/folder/'summary.json')
        assert summary['status'] == 'pass', folder
        checks[folder] = dict(status='pass', summary_sha256=sha(OUT/folder/'summary.json'))
    for folder, n in [('small_kernel_v3_001',976), ('strong_kernel_v3_001',192), ('bridge_001',39), ('detached',39)]:
        assert len(read(OUT/folder/'summary.json')['checks']) == n
        checks[folder]['checks'] = n
    suite = ET.parse(OUT/'regression_final.xml').getroot().find('testsuite')
    assert int(suite.attrib['failures']) == int(suite.attrib['errors']) == 0
    assert int(suite.attrib['tests']) == 312 and int(suite.attrib['skipped']) == 1
    bridge_hp, full_hp = read(OUT/'bridge_hp_001/summary.json'), read(OUT/'full_path_hp_001/summary.json')
    assert bridge_hp['completed_states'] == bridge_hp['expected_states'] == 6
    assert full_hp['completed_states'] == full_hp['expected_states'] == 80
    cross, full_metrics = [], {}
    for folder in ('bridge_hp_001', 'full_path_hp_001'):
        summary = read(OUT/folder/'summary.json')
        for committed in summary['committed_states']:
            path = OUT/folder/committed['decision_file']
            assert sha(path) == committed['decision_file_sha256']
            row = read(path)
            assert row['numerical_status'] == 'pass' and all(row['checks'].values())
            assert sha(OUT/folder/row['reference50_file']) == row['reference50_sha256']
            if row['precision_crosscheck']['status'] == 'pass':
                c = row['precision_crosscheck']
                assert sha(OUT/folder/c['reference80_file']) == c['reference80_sha256']
                cross.append(float(c['full_relative_error_decimal']))
    assert len(cross) == 8
    plots = read(OUT/'plots_002/evidence_manifest.json')
    assert plots['status'] == 'complete' and plots['sources_unchanged']
    for artifact in plots['files']:
        assert sha(OUT/'plots_002'/artifact['path']) == artifact['sha256']
    spec = read(REPO/'configs/hf3/validation_spec.json')
    for index, family in enumerate(('inverter','gripper'),1):
        folder = OUT/(family+'_path_001')
        result = read(folder/'result.json')
        assert result['implementation']['source_sha256'] == freeze['source_sha256']
        assert result['numerics']['status'] == 'success' and result['numerics']['target_reached']
        assert result['solver_config'] == read(REPO/'configs/hf3/full_path_solver_v1.json')
        state_index = read(folder/'steps/index.json')
        assert len(state_index['steps']) == 40
        with np.load(folder/'path.npz',allow_pickle=False) as z:
            assert np.array_equal(z['d'],spec['full_path_targets_mm']) and np.all(z['is_original_target'])
            for position, record in enumerate(state_index['steps']):
                assert sha(folder/record['arrays_file']) == record['arrays_sha256']
                with np.load(folder/record['arrays_file'],allow_pickle=False) as single:
                    for key in single.files:
                        assert np.array_equal(z[key][position],single[key]),(family,key,position)
            m = dict(result['metrics_at_target'])
            m.update(path_minimum_J=float(z['J'].min()), maximum_production_relative_residual=float(z['relative_residual'].max()),
                maximum_relative_global_force_balance=float(z['relative_global_force_balance'].max()),
                original_targets=40, accepted_states=40,
                rejected_trials=sum(not t['accepted'] for t in result['solver_trace']['trials']),
                failed_attempts=len(result['solver_trace']['failed_attempts']))
        rows = [read(p) for p in (OUT/'full_path_hp_001'/f'run_{index:03d}').glob('state_????.json')]
        m.update(maximum_HP_relative_residual=max(float(r['metrics']['relative_residual_decimal']) for r in rows),
            maximum_HP_force_evaluation_error=max(float(r['evaluation_error']['full_relative_error_decimal']) for r in rows),
            maximum_HP_relative_force_balance=max(float(r['metrics']['relative_force_balance_decimal']) for r in rows))
        full_metrics[family] = m
    jobs = [read(p) for p in (OUT/'resource_jobs').glob('*.json')]
    assert all(j['status'] in {'complete','failed'} for j in jobs)
    allowed_failures = {'regression_a','monitor_bootstrap_failure','evidence_plots'}
    assert {j['name'] for j in jobs if j['status']=='failed'} == allowed_failures
    category = {name:sum(j['wall_seconds'] for j in jobs if j['category']==name) for name in spec['resource_limits']['category_seconds']}
    assert all(value <= spec['resource_limits']['category_seconds'][key] for key,value in category.items())
    assert sum(category.values()) <= spec['resource_limits']['total_seconds']
    for family in ('inverter','gripper'):
        assert sum(j['category']==family+'_path' and j['process_started'] for j in jobs)==1
    peaks = [j['sampled_peak_tree_rss_bytes'] for j in jobs if j.get('sampled_peak_tree_rss_bytes') is not None]
    assert max(peaks) < spec['resource_limits']['memory_soft_limit_bytes']
    result = dict(status='pass', scope='HF3 numerical implementation, project bridge, two 40-target free-output pilot paths and independent deployment',
        source_sha256=freeze['source_sha256'], wheel_sha256=sha(WHEEL), original_geometry_files_unchanged=395,
        old_HF2_release_and_wheel_unchanged=True, frozen_scientific_thresholds_unchanged=True,
        regression=dict(passed=311, skipped=1, preserved_initial_test_failure=True), checks=checks,
        high_precision=dict(bridge_states=6, full_path_states=80, cross50_80_states=8, max_cross_force_difference=max(cross),
            full_path_maxima=full_hp['maxima'], bridge_maxima=bridge_hp['maxima']), full_paths=full_metrics,
        resources=dict(category_seconds=category, total_seconds=sum(category.values()), allowed_total_seconds=2400,
            maximum_sampled_tree_rss_bytes=max(peaks), jobs=len(jobs), preserved_failed_jobs=sorted(allowed_failures),
            retrospective_startup_accounting_seconds=4.1104776, installation_seconds=read(OUT/'detached_receipt.json')['installation_seconds'],
            note='Sampling is a soft process-tree RSS observation. The failed monitor bootstrap had no mechanics child and no RSS sample. Its tool elapsed time is conservatively charged; early immutable receipts predate that retrospective ledger addition.'),
        limitations=dict(qualification='pending', functionality='not_evaluated', contact_accuracy='not_validated',
            stability='not_validated', mesh_material_medium_regularization_sensitivity='not_validated', HF4_executed=False))
    write(OUT/'acceptance_summary.json',result)
    records = REPO/'validation/hf3/records'
    records.mkdir(parents=True,exist_ok=True)
    copies = {'acceptance_summary.json':OUT/'acceptance_summary.json','source_freeze.json':OUT/'production_source_freeze.json',
        'full_path_gate.json':OUT/'full_path_gate.json','bridge_summary.json':OUT/'bridge_001/summary.json',
        'bridge_HP_summary.json':OUT/'bridge_hp_001/summary.json','full_path_HP_summary.json':OUT/'full_path_hp_001/summary.json',
        'independent_installation_summary.json':OUT/'detached/summary.json','regression_final.xml':OUT/'regression_final.xml'}
    for name,path in copies.items(): shutil.copy2(path,records/name)
    print(json.dumps(dict(status='pass', full_paths=full_metrics,resources=result['resources']),indent=2))
    return result
def package():
    verdict = read(OUT/'acceptance_summary.json'); assert verdict['status']=='pass'
    git = lambda *args:subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
    assert git('status','--porcelain') == ''
    commit = git('rev-parse','HEAD')
    zip_path = ROOT/'deliverables/HF3_evaluator_and_evidence.zip'; assert not zip_path.exists()
    tracked = git('ls-files','-z').split('\0')
    paths = [REPO/p for p in tracked if p]
    paths += [WHEEL]
    for directory in ('geometry_dataset','docs','hf3_results'):
        paths += [p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.tmp']
    paths += [ROOT/'README.md',ROOT/'HF3_EVIDENCE_README.md']
    # Keep the previous repaired distribution intact as a separate historical
    # evidence layer. No LF/MATLAB execution dependency is added to the wheel.
    paths += [ROOT/'deliverables/HF2_repaired_evaluator_and_evidence.zip',ROOT/'deliverables/HF2_repair_release_manifest.json']
    paths = sorted(set(paths))
    manifest = dict(schema_version='hf3-release-1.0',created_utc=datetime.now(timezone.utc).isoformat(),git_commit=commit,
        source_sha256=verdict['source_sha256'],wheel_sha256=sha(WHEEL),acceptance_summary_sha256=sha(OUT/'acceptance_summary.json'),
        status='HF3 specified numerical gates passed; research qualification pending and contact accuracy unvalidated',
        files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in paths])
    write(ROOT/'HF3_CONTENT_MANIFEST.json',manifest)
    with zipfile.ZipFile(zip_path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths:
            compression=zipfile.ZIP_STORED if p.suffix in {'.zip','.whl'} else zipfile.ZIP_DEFLATED
            z.write(p,p.relative_to(ROOT).as_posix(),compress_type=compression)
        z.writestr('HF3_CONTENT_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        for item in manifest['files']:
            with z.open(item['path']) as stream:
                assert hashlib.file_digest(stream,'sha256').hexdigest()==item['sha256']
    final=dict(schema_version='hf3-release-manifest-1.0',git_commit=commit,source_sha256=verdict['source_sha256'],wheel_sha256=sha(WHEEL),
        zip_path=zip_path.relative_to(ROOT).as_posix(),zip_sha256=sha(zip_path),zip_bytes=zip_path.stat().st_size,
        entries=len(paths)+1,all_member_hashes_verified=True,geometry_files_unchanged=395,
        accepted_HP_states=86,regression_passed=311,regression_skipped=1,qualification='pending',HF4_executed=False)
    write(ROOT/'deliverables/HF3_release_manifest.json',final)
    write(OUT/'release_integrity.json',final)
    print(json.dumps(final,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['verify','package']);a=p.parse_args()
    verify() if a.mode=='verify' else package()
