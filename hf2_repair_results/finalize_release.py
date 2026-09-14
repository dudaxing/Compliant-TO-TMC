"""Verify and package HF-2 repair evidence; never solve mechanics.

Run ``verify`` after all monitored jobs and detached acceptance have finished.
It snapshots compact evidence into the HF repository for the root to commit.
Run ``package`` only after that repository is clean. Original releases and
source data are read-only inputs; the old release is never overwritten.
"""
from pathlib import Path, PurePosixPath
import argparse
from datetime import datetime
from decimal import Decimal
from email.parser import BytesParser
import hashlib
import json
import math
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT/'hf_repo'
DATA = ROOT/'geometry_dataset'
RESULTS = ROOT/'hf2_repair_results'
RECORDS = REPO/'validation/hf2_repair/records'
WHEEL = REPO/'dist/independent_hf_evaluator-0.2.1-py3-none-any.whl'
OLD_WHEEL = REPO/'dist/independent_hf_evaluator-0.2.0-py3-none-any.whl'
BASE_ZIP = ROOT/'deliverables/HF2_independent_evaluator_and_evidence.zip'
OUTPUT_ZIP = ROOT/'deliverables/HF2_repaired_evaluator_and_evidence.zip'
EXPECTED_RUNTIME = '3eeee09c781fc1509d54156bf696f0dd6ed5e2e52df1a19bbbacc59338dfe3b1'
SPEC = REPO/'validation/hf2_repair/precision_spec.json'
SPEC_SHA = 'ba4909b19d369890b79af8db8dfa58b01672e904fe68e8dc3175c408e23ad663'
FIXTURE = REPO/'validation/hf2_repair/strong_inputs.npz'
FIXTURE_SHA = '60832407c9b8c1c91e79e89d993e6f77c4e3c7a87f60c585c737217c49698f60'
AMENDMENT = RESULTS/'resource_amendment_001.json'
HP_INITIAL = RESULTS/'full_precision_audit_001'
HP_FINAL = RESULTS/'full_precision_audit_resumed_001'
LAUNCH_FAILURE_NAME = 'full_precision_audit_resume_f9e2d6ad.json'
LAUNCH_FAILURE_SHA = '3cc9f6cf591b7efe7f8fd9b0561cda258f57c555c9890afaaa96ff3e670fe007'
RESPONSE_KEYS = ('U_pass', 'loaded_displacements_pass', 'support_reaction_pass',
                 'solid_material_energy_pass', 'medium_material_energy_pass',
                 'J_field_pass', 'min_J_pass')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def workspace_path(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT/str(value).replace('\\', '/')


def hash_bindings(records):
    for record in records:
        path = workspace_path(record['path'])
        require(path.is_file(), f'Missing evidence: {path}')
        require(digest(path) == record['sha256'], f'Evidence hash changed: {path}')
        if 'bytes' in record:
            require(path.stat().st_size == record['bytes'], f'Evidence size changed: {path}')


def passing_rows(rows, count, label):
    require(len(rows) == count, f'{label}: expected {count} rows, found {len(rows)}')
    require(all(row['status'] == 'pass' for row in rows), f'{label}: nonpassing row')


def inspect_budget():
    amendment = read(AMENDMENT)
    require(amendment['schema_version'] == 'hf2-resource-amendment-1.0'
            and amendment['original_precision_spec_sha256'] == SPEC_SHA,
            'Scheduling amendment changed the scientific specification')
    require(amendment['original_postprocess_cumulative_seconds'] == 600
            and amendment['amended_postprocess_cumulative_seconds'] == 720
            and amendment['continuation_process_seconds'] == 120
            and amendment['total_numerical_seconds'] == 3000
            and amendment['small_cumulative_seconds'] == 1200
            and amendment['corrected_python_path_attempts'] == 1
            and amendment['continuation_job_name'] == 'full_precision_audit_resume',
            'Resource amendment differs from the authorized bounded continuation')
    hash_bindings([amendment['preserved_failure'], amendment['preserved_monitor']])
    amendment_time = datetime.fromisoformat(amendment['created_utc'])
    require(amendment_time.utcoffset() is not None, 'Amendment timestamp must include its UTC offset')
    amendment_sha = digest(AMENDMENT)
    paths = sorted((RESULTS/'resource_jobs').glob('*.json'))
    jobs = [read(path) for path in paths]
    launch_failures = [(path, job) for path, job in zip(paths, jobs) if job.get('process_started') is False]
    require(len(launch_failures) == 1 and launch_failures[0][0].name == LAUNCH_FAILURE_NAME
            and digest(launch_failures[0][0]) == LAUNCH_FAILURE_SHA,
            'Only the specifically preserved pre-child Windows launch failure is permitted')
    required_names = {'freeze_inputs', 'full_regression', 'small_reference', 'strong_precision',
                      'corrected_cshape', 'response_comparison', 'full_precision_audit',
                      'full_precision_audit_resume', 'hf2_repair_detached'}
    require(required_names <= {job['name'] for job in jobs}, 'Required monitored numerical job receipt missing')
    full = [job for job in jobs if job['category'] == 'python_cshape']
    require(len(full) == 1, 'Exactly one corrected full Python path attempt is allowed')
    post_jobs = [job for job in jobs if job['category'] == 'postprocess' and job.get('process_started') is not False]
    require(sorted(job['name'] for job in post_jobs)
            == ['full_precision_audit', 'full_precision_audit_resume', 'response_comparison'],
            'Only the original audit, historical comparison and single named continuation are allowed')
    expected_nonzero = []
    expected_timeout = []
    for path, job in zip(paths, jobs):
        launch_failed = path.name == LAUNCH_FAILURE_NAME
        require(job['status'] in ({'launch_failed'} if launch_failed else {'complete', 'failed'}) and 'wall_seconds' in job,
                f'Numerical job unfinished: {path.name}')
        require(job.get('stop_reason') == ('launch_error' if launch_failed else None),
                f'Unexpected numerical stop reason: {path.name}')
        elapsed = job['wall_seconds']
        require(math.isfinite(elapsed) and elapsed >= 0, f'Invalid job timing: {path.name}')
        peak = job.get('sampled_peak_tree_rss_bytes')
        require(isinstance(peak, (int, float)) and (peak == 0 if launch_failed else 0 < peak < 4*1024**3),
                f'Missing or exceeded sampled memory evidence: {path.name}')
        require((path.parent/job['log']).is_file(), f'Job log missing: {path.name}')
        started = datetime.fromisoformat(job['started_utc'])
        require(started.utcoffset() is not None, f'Job timestamp lacks UTC offset: {path.name}')
        if started >= amendment_time:
            require(job.get('resource_amendment_sha256') == amendment_sha,
                    f'Post-amendment receipt does not bind the frozen amendment: {path.name}')
        if launch_failed:
            require(job['process_started'] is False and job['returncode'] == 1
                    and job['exception_type'] == 'FileNotFoundError' and job['windows_error'] == 2
                    and job['memory_samples'] == 0 and elapsed == 3.8126554,
                    'Pre-child launch failure fields differ from the reviewed receipt')
        elif job['name'] == 'response_comparison':
            # compare_cshape intentionally retains old MATLAB equilibrium failures.
            require(job['returncode'] == 1 and job['status'] == 'failed',
                    'Historical comparison exit must faithfully retain its not_pass result')
            expected_nonzero.append(path.name)
        elif job['name'] == 'full_precision_audit':
            require(job['returncode'] == 1 and job['status'] == 'failed'
                    and started < amendment_time and elapsed <= job['reserved_limit_seconds'] <= 600,
                    'Initial offline timeout must retain its original failed receipt and original budget')
            expected_timeout.append(path.name)
        else:
            require(job['returncode'] == 0 and job['status'] == 'complete',
                    f'Unexpected failed numerical job: {path.name}')
        if job['name'] == 'full_precision_audit_resume' and not launch_failed:
            require(started >= amendment_time and elapsed <= job['reserved_limit_seconds'] <= 120,
                    'Continuation started before its amendment or exceeded its 120-second cap')
    total = sum(job['wall_seconds'] for job in jobs)
    small = sum(job['wall_seconds'] for job in jobs if job['category'] in {'small', 'compile', 'isolated'})
    post = sum(job['wall_seconds'] for job in jobs if job['category'] == 'postprocess')
    require(total <= 3000 and small <= 1200 and post <= 720, 'Amended cumulative numerical budget exceeded')
    require(full[0]['wall_seconds'] <= 1200, 'Corrected full path exceeded its 1200-second budget')
    return {'jobs': len(jobs), 'total_seconds': total, 'small_compile_isolated_seconds': small,
            'postprocess_seconds': post, 'python_cshape_attempts': 1,
            'postprocess_original_cap_seconds': 600, 'postprocess_amended_cap_seconds': 720,
            'continuation_process_cap_seconds': 120, 'resource_amendment_sha256': amendment_sha,
            'resource_amendment_created_utc': amendment['created_utc'],
            'max_sampled_tree_rss_bytes': max(job['sampled_peak_tree_rss_bytes'] for job in jobs),
            'expected_nonzero_response_comparison_receipts': expected_nonzero,
            'preserved_incomplete_initial_HP_receipts': expected_timeout,
            'preserved_pre_child_launch_failure': {'path': LAUNCH_FAILURE_NAME,
                'sha256': LAUNCH_FAILURE_SHA, 'process_started': False,
                'wall_seconds_counted_in_total_and_postprocess': 3.8126554},
            'receipts': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path)} for path in paths]}


def verify(snapshot=True):
    import numpy as np  # Ordinary array inspection only; no HF import or solve.
    require(digest(SPEC) == SPEC_SHA and digest(FIXTURE) == FIXTURE_SHA, 'Frozen repair input changed')
    frozen = read(RESULTS/'frozen_inputs.json')
    hash_bindings(frozen['files'])
    gate = read(RESULTS/'full_path_gate.json')
    require(gate['status'] == 'pass' and gate['runtime_source_sha256'] == EXPECTED_RUNTIME,
            'Full-path local gate/runtime identity mismatch')
    require(gate['precision_spec_sha256'] == SPEC_SHA, 'Gate used a different precision specification')
    hash_bindings([{'path': name, 'sha256': value} for name, value in gate['evidence'].items()])

    runtime = hashlib.sha256()
    core = sorted((REPO/'src/hf_eval').glob('*.py'))
    require(len(core) == 10, 'Expected exactly ten core Python source files')
    source_names = {path.relative_to(REPO/'src').as_posix() for path in core}
    with zipfile.ZipFile(WHEEL) as wheel:
        require(wheel.testzip() is None, 'New wheel CRC failure')
        require({name for name in wheel.namelist() if name.startswith('hf_eval/') and name.endswith('.py')} == source_names,
                'Wheel/source core file set differs')
        metadata = [name for name in wheel.namelist() if name.endswith('.dist-info/METADATA')]
        require(len(metadata) == 1 and BytesParser().parsebytes(wheel.read(metadata[0]))['Version'] == '0.2.1',
                'New wheel version must be 0.2.1')
        for path in core:
            content = path.read_bytes()
            require(wheel.read(path.relative_to(REPO/'src').as_posix()) == content, f'Wheel/source differs: {path.name}')
            require(digest(path) == gate['source_files_sha256'][path.relative_to(REPO).as_posix()],
                    f'Core changed since full-path gate: {path.name}')
            runtime.update(path.name.encode('utf-8')+b'\0'+content)
    require(runtime.hexdigest() == EXPECTED_RUNTIME, 'Core runtime identity differs from frozen full-path run')

    path_result = read(RESULTS/'cshape_python_001/result.json')
    require(path_result['source_code_sha256'] == EXPECTED_RUNTIME and path_result['status'] == 'success', 'New path/version not successful')
    require(path_result['target_reached'] and path_result['reached_lambda'] == path_result['target_lambda'] == 1,
            'Corrected path did not reach the frozen endpoint')
    require(path_result['original_targets_reached'] == 100 and path_result['failure'] is None, 'New original targets incomplete')
    config = path_result['benchmark_config']
    require(config['kernel_version'] == 'p26_q1_direct_piola_huhu_v2' and config['solver_profile'] == 'hf2_precision_v2',
            'Wrong corrected kernel/profile')
    require(config['solver']['tolerance'] == config['internal_newton_tolerance'] == 1e-9
            and config['external_free_residual_tolerance'] == 1e-8, 'Internal/external tolerance changed')
    with np.load(RESULTS/'cshape_python_001/cshape_path.npz', allow_pickle=False) as arrays, np.load(FIXTURE, allow_pickle=False) as fixture:
        levels, original = arrays['lambda'], arrays['original_target'].astype(bool)
        count = len(levels)
        require(count == path_result['accepted_step_count'] and count >= 100, 'New accepted count disagrees')
        require(np.all(np.diff(levels) > 0) and np.array_equal(levels[original], fixture['targets']), 'New targets differ or are duplicated')
        require(arrays['internal_force'].shape == arrays['U'].shape == (count, 3906), 'New force/U path arrays incomplete')

    tree = ET.parse(RESULTS/'full_regression.xml').getroot()
    suites = [tree] if tree.tag == 'testsuite' else list(tree.iter('testsuite'))
    junit = {name: sum(int(s.attrib.get(name, 0)) for s in suites) for name in ('tests', 'failures', 'errors', 'skipped')}
    require(junit == {'tests': 200, 'failures': 0, 'errors': 0, 'skipped': 1}, f'Regression count/status mismatch: {junit}')
    small = read(RESULTS/'small_reference_001/summary.json')
    require(small['status'] == 'pass' and small['completed_cases'] == 16, 'Small reference incomplete')
    passing_rows(small['checks'], 976, 'Small reference')
    strong = read(RESULTS/'strong_precision_001/summary.json')
    require(strong['status'] == 'pass', 'Strong-state precision failed')
    passing_rows(strong['checks'], 192, 'Strong-state precision')
    hash_bindings([{'path': name, 'sha256': value} for name, value in strong['inputs_sha256'].items()])

    comparison = read(RESULTS/'response_comparison_001/summary.json')
    require(comparison['full_benchmark_status'] == 'not_pass', 'Historical comparison status must not be rewritten')
    require(comparison['common_original_targets'] == 100, 'Response comparison is not all 100 original targets')
    require(all(row['status'] == 'pass' for row in comparison['setup_checks']), 'Response comparison setup mismatch')
    response_rows = comparison['per_target_errors']
    require(len(response_rows) == 100 and all(all(row[key] for key in RESPONSE_KEYS) for row in response_rows),
            'One of seven frozen response metrics failed')
    require(not comparison.get('exceptions', []) and not comparison.get('failures', []), 'Response comparison execution exception')

    initial_failure = read(HP_INITIAL/'validation_failure.json')
    require(initial_failure['validation_status'] == 'incomplete'
            and initial_failure['exception_type'] == 'TimeoutError'
            and initial_failure['repaired_python_numerical_closure_status'] == 'not_pass',
            'Initial partial HP attempt must remain an explicit timeout, not a passed audit')
    initial_rows = [json.loads(line) for line in (HP_INITIAL/'state_progress.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    require(len(initial_rows) == 299 and not any('exception_type' in row for row in initial_rows),
            'Initial 299 evaluated states are missing or altered into exceptions')
    require({side: sum(row['side'] == side for row in initial_rows) for side in ('new_python', 'old_python', 'matlab')}
            == {'new_python': 100, 'old_python': 100, 'matlab': 99},
            'Initial timeout coverage differs from the preserved 100+100+99 states')
    hp_folder = HP_FINAL
    hp = read(hp_folder/'summary.json')
    progress = read(hp_folder/'progress.json')
    require(progress['status'] == 'complete', 'Full precision audit unfinished')
    require(hp['repaired_python_numerical_closure_status'] == hp['response_agreement_status'] == 'pass', 'New path numerical closure failed')
    require(hp['new_python_independent_state_status'] == 'pass' and not hp['new_python_failures'], 'New HP state failed')
    require(not hp['exceptions'] and not hp['historical_reference_evaluation_exceptions'], 'HP evaluation exception')
    require(hp['new_python_original_targets'] == 100 and hp['new_python_accepted_states'] == count, 'HP new path incomplete')
    require(hp['total_evaluated_states'] == hp['successful_high_precision_evaluations'] == count+200,
            'HP must evaluate all new states and both historical 100-state paths')
    require(progress['completed_states'] == count+200, 'HP progress count disagrees')
    require(hp['original_comparison_full_benchmark_status'] == 'not_pass', 'HP summary hides old comparison failures')
    require(hp['metadata_versions']['new_python']['source_code_sha256'] == EXPECTED_RUNTIME,
            'HP audit did not evaluate the frozen repaired runtime')
    resumed = hp['resume_provenance']
    require(resumed == read(hp_folder/'resume_provenance.json') and resumed['status'] == 'pass'
            and resumed['inherited_complete_state_count'] == 290
            and resumed['recomputed_state_count'] == resumed['high_precision_evaluations_this_resume'] == 10
            and resumed['recomputed_side'] == 'matlab' and resumed['recomputed_source_indices'] == list(range(90, 100))
            and resumed['newly_completed_source_indices'] == [99]
            and resumed['overlapping_recomputed_state_count'] == 9
            and resumed['overlap_comparison_status'] == 'pass'
            and resumed['precision_high_precision_re_evaluations'] == 0
            and resumed['scientific_criteria_changed'] is False and resumed['historical_path_statuses_modified'] is False,
            'Resume differs from the authorized cache recovery and ten fixed-state evaluations')
    passing_rows(resumed['overlap_comparisons'], 9, 'Resume overlap exact checks')
    require({row['source_index'] for row in resumed['overlap_comparisons']} == set(range(90, 99))
            and all(row['original_scientific_row_sha256'] == row['recomputed_scientific_row_sha256']
                    for row in resumed['overlap_comparisons']), 'Resume overlap values changed')
    require(resumed['resource_amendment'] == read(AMENDMENT)
            and resumed['prior_receipt'] == read(RESULTS/'resource_jobs/full_precision_audit_1b4e8d13.json'),
            'Resume provenance differs from its original failure and prospective amendment')
    cache_hashes = resumed['cached_source_hashes']
    require(set(cache_hashes) == {path.name for path in HP_INITIAL.iterdir() if path.is_file()},
            'Initial partial HP cache file closure changed')
    require(all(digest(HP_INITIAL/name) == sha for name, sha in cache_hashes.items()),
            'Initial partial HP cache bytes changed after continuation')
    require(all(row['status'] == 'pass' for row in hp['setup_checks']), 'HP primitive/setup gate failed')
    passing_rows(hp['precision_crosschecks'], 3, '50/80 digit precision checks')
    require({row['original_target_index'] for row in hp['precision_crosschecks']} == {0, 49, 99}, 'Wrong 50/80 crosscheck targets')
    require(all(row['lower_digits'] == 50 and row['higher_digits'] == 80 for row in hp['precision_crosschecks']), 'Wrong reference precision')
    hash_bindings(hp['evidence'])
    rows = [json.loads(line) for line in (hp_folder/'state_progress.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    require(len(rows) == count+200 and not any('exception_type' in row for row in rows), 'HP state evidence incomplete')
    resumed_rows = {(row['side'], row['source_index']): row for row in rows}
    require(len(resumed_rows) == count+200, 'Completed HP audit duplicates a state identity')
    # All previously evaluated values are immutable evidence. This independently
    # checks both reused rows and the nine deliberately reevaluated overlaps.
    for prior in initial_rows:
        resumed = resumed_rows.get((prior['side'], prior['source_index']))
        require(resumed is not None and all(resumed.get(key) == value for key, value in prior.items() if key != 'wall_seconds'),
                f'Resumed HP values differ from preserved initial evidence: {prior["side"]}/{prior["source_index"]}')
    for side, expected in [('new_python', count), ('old_python', 100), ('matlab', 100)]:
        selected = [row for row in rows if row['side'] == side]
        audit = hp['historical_and_new_audits'][side]
        require(len(selected) == audit['evaluated_states'] == expected and audit['original_targets_evaluated'] == 100,
                f'HP side count mismatch: {side}')
        require(audit['historical_state_status_preserved'], f'Historical status not preserved: {side}')
        with np.load(hp_folder/(side+'_high_precision.npz'), allow_pickle=False) as arrays:
            require(len(arrays['source_index']) == expected, f'Combined HP array incomplete: {side}')
        if side == 'new_python':
            for row in selected:
                require(row['new_version_state_status'] == 'pass' and Decimal(row['high_precision_relative_residual']) <= Decimal('1e-8'),
                        'New HP equilibrium exceeds unchanged external tolerance')
                require(max(Decimal(row['evaluation_full_relative_error_decimal']), Decimal(row['evaluation_free_relative_error_decimal'])) <= Decimal('1e-9'),
                        'New HP expression budget exceeded')
    historical = {side: hp['historical_and_new_audits'][side] for side in ('old_python', 'matlab')}

    receipt = read(RESULTS/'detached_receipt.json')
    detached = read(RESULTS/'detached/acceptance.json')
    require(detached['status'] == 'pass' and len(detached['checks']) == 24 and all(detached['checks'].values()), 'Detached 24-check acceptance failed')
    require(detached['small_checks'] == 976 and detached['small_cases'] == 16, 'Detached small replay incomplete')
    require(detached['source_sha256'] == EXPECTED_RUNTIME, 'Detached runtime differs')
    require(detached['installed_record_files_checked'] > 0 and not detached['installed_record_failures'], 'Installed RECORD check failed')
    require(receipt['returncode'] == 0 and receipt['dataset_files_unchanged'] and receipt['dataset_file_count'] == 395, 'Detached dataset integrity failed')
    require(receipt['wheel_sha256'] == digest(WHEEL) and set(receipt['source_files_match_wheel']) == source_names, 'Detached wheel/source receipt mismatch')
    access = read(RESULTS/'detached/access_audit.json')
    require(not access['denied'] and not access['blocked_imports'], 'Detached forbidden source access attempted')

    originals = read(ROOT/'reference_inputs/manifest.json')
    require(len(originals) == 5, 'Expected five preserved user inputs')
    for record in originals:
        require(digest(Path(record['original_path_record_only'])) == record['sha256'], f'Original changed: {record["file"]}')
        require(digest(ROOT/'reference_inputs'/record['file']) == record['sha256'], f'Preserved copy changed: {record["file"]}')
    source_manifest = read(ROOT/'reference_validation/matlab/source_manifest.json')
    require(len(source_manifest['files']) == 8, 'Expected eight MATLAB source copies')
    with zipfile.ZipFile(ROOT/'reference_inputs/tmc_source.zip') as archive:
        for record in source_manifest['files']:
            path = ROOT/'reference_validation/matlab'/record['local_path']
            require(digest(path) == record['sha256'] and archive.read(record['original_member']) == path.read_bytes(), 'Original MATLAB source copy changed')
    data_manifest = read(DATA/'file_manifest.json')
    expected_data = {record['path'] for record in data_manifest['files']} | {'file_manifest.json'}
    actual_data = {path.relative_to(DATA).as_posix() for path in DATA.rglob('*') if path.is_file()}
    require(expected_data == actual_data and len(actual_data) == 395, 'Dataset file closure changed')
    for record in data_manifest['files']:
        require(digest(DATA/record['path']) == record['sha256'] and (DATA/record['path']).stat().st_size == record['bytes'], 'Dataset asset changed')
    hf1_data = read(ROOT/'hf1_results/detached_location.json')['dataset_hashes_before']
    require(len(hf1_data) == 395 and all(digest(DATA/name) == value for name, value in hf1_data.items()), 'Dataset differs from HF1')
    for stage in ('HF1', 'HF2'):
        old = read(ROOT/f'deliverables/{stage}_release_manifest.json')
        require(digest(ROOT/'deliverables'/old['file']) == old['sha256'], f'{stage} old ZIP changed')
        old_version = '0.1.0' if stage == 'HF1' else '0.2.0'
        require(digest(REPO/f'dist/independent_hf_evaluator-{old_version}-py3-none-any.whl') == old['wheel_sha256'], f'{stage} old wheel changed')
    with zipfile.ZipFile(BASE_ZIP) as archive:
        require(archive.testzip() is None, 'Old base ZIP CRC failure')
        names = {name for name in archive.namelist() if name.startswith('geometry_dataset/') and not name.endswith('/')}
        require(names == {'geometry_dataset/'+name for name in expected_data}, 'Base ZIP dataset closure differs')
        for name in expected_data:
            require(hashlib.sha256(archive.read('geometry_dataset/'+name)).hexdigest() == hf1_data[name], 'Base ZIP dataset changed')
    budget = inspect_budget()
    evidence_paths = [RESULTS/'full_path_gate.json', RESULTS/'full_regression.xml',
                      RESULTS/'small_reference_001/summary.json', RESULTS/'strong_precision_001/summary.json',
                      hp_folder/'summary.json', RESULTS/'response_comparison_001/summary.json',
                      RESULTS/'detached/acceptance.json', RESULTS/'detached_receipt.json',
                      AMENDMENT, HP_INITIAL/'validation_failure.json']
    result = {'status': 'pass', 'scope': 'Integrity and closure of the specified source-numeric HF-2 repair; no new solve',
              'repaired_version': '0.2.1', 'repaired_numerical_closure_status': 'pass',
              'runtime_source_sha256': runtime.hexdigest(), 'wheel_sha256': digest(WHEEL),
              'core_files': sorted(source_names), 'core_equals_wheel_gate_path_and_detached': True,
              'regression': junit, 'small_checks': 976, 'strong_checks': 192, 'detached_checks': 24,
              'new_original_targets': 100, 'new_accepted_states': count, 'HP_total_states': count+200,
              'HP_completed_evidence_directory': HP_FINAL.relative_to(ROOT).as_posix(),
              'initial_HP_timeout_preserved': {'directory': HP_INITIAL.relative_to(ROOT).as_posix(),
                  'evaluated_states': 299, 'status': initial_failure['validation_status'],
                  'exception_type': initial_failure['exception_type'],
                  'state_progress_sha256': digest(HP_INITIAL/'state_progress.jsonl')},
              'old_comparison_status_preserved': comparison['full_benchmark_status'], 'historical_audits': historical,
              'dataset_files': 395, 'dataset_manifest_sha256': digest(DATA/'file_manifest.json'),
              'dataset_unchanged_since_HF1_and_base_release': True, 'user_original_and_copy_files': 5,
              'unchanged_matlab_source_files': 8, 'frozen_baseline_files_checked': len(frozen['files']),
              'HF1_HF2_archives_and_wheels_preserved': True, 'budget': budget,
              'physical_contact_accuracy': 'not_validated', 'HF3_executed': False,
              'evidence': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path)} for path in evidence_paths]}
    if snapshot:
        copies = {'full_regression.xml': RESULTS/'full_regression.xml', 'full_path_gate.json': RESULTS/'full_path_gate.json',
                  'small_reference_summary.json': RESULTS/'small_reference_001/summary.json',
                  'strong_precision_summary.json': RESULTS/'strong_precision_001/summary.json',
                  'full_precision_audit_summary.json': hp_folder/'summary.json',
                  'response_comparison_summary.json': RESULTS/'response_comparison_001/summary.json',
                  'detached_acceptance.json': RESULTS/'detached/acceptance.json',
                  'detached_receipt.json': RESULTS/'detached_receipt.json',
                  'resource_amendment_001.json': AMENDMENT,
                  'initial_HP_timeout.json': HP_INITIAL/'validation_failure.json'}
        RECORDS.mkdir(parents=True, exist_ok=True)
        for name, source in copies.items():
            shutil.copy2(source, RECORDS/name)
        write(RECORDS/'record_index.json', [{'record': name, 'original_workspace_path': path.relative_to(ROOT).as_posix(),
                                           'sha256': digest(path)} for name, path in copies.items()])
        write(RECORDS/'release_integrity.json', result)
        write(RESULTS/'release_integrity.json', result)
    return result


def safe_member(name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name,
            f'Unsafe package member: {name}')
    require(path.suffix.lower() not in {'.m', '.mat', '.zip', '.pdf', '.pyc'}, f'Forbidden package file: {name}')
    require(not any(part in {'.git', '__pycache__', '.pytest_cache', 'site-packages'} or part.startswith('.venv')
                    for part in path.parts), f'Environment/cache must not be packaged: {name}')
    require(path.parts[0] not in {'reference_inputs', 'hf0_audit', 'lf_data_preparation'},
            f'Original/source preparation material must not be packaged: {name}')
    require(not (name.startswith('geometry_dataset/') and path.suffix.lower() in {'.py', '.pyw', '.m', '.mat'}),
            f'Dataset must contain ordinary data only: {name}')


def package():
    integrity = verify(snapshot=False)
    require(integrity == read(RECORDS/'release_integrity.json'), 'Run verify and commit its current evidence snapshot before packaging')
    record_index = read(RECORDS/'record_index.json')
    require(len(record_index) == 10, 'Compact evidence index is incomplete')
    for record in record_index:
        require(digest(RECORDS/record['record']) == record['sha256']
                == digest(workspace_path(record['original_workspace_path'])),
                f'Compact record differs from its verified evidence: {record["record"]}')
    git = lambda *args: subprocess.check_output(['git', '-C', str(REPO), *args])
    require(not git('status', '--porcelain').strip(), 'Commit the HF repository before packaging')
    revision = git('rev-parse', 'HEAD').decode().strip()
    members = {}
    replaced = {'RELEASE.json', 'PACKAGE_FILES.json', 'EVIDENCE_README.md'}
    with zipfile.ZipFile(BASE_ZIP) as base:
        for item in base.infolist():
            if item.is_dir() or item.filename.startswith('hf_repo/') or item.filename in replaced:
                continue
            safe_member(item.filename)
            require(item.filename not in members, 'Duplicate member in old package')
            members[item.filename] = ('base', item.filename)

    def add(path, name=None):
        path = Path(path)
        require(path.is_file() and not path.is_symlink(), f'Package input is not a regular file: {path}')
        name = path.relative_to(ROOT).as_posix() if name is None else name
        safe_member(name)
        members[name] = ('local', path)

    tracked = []
    for entry in git('ls-files', '-s', '-z').decode('utf-8').split('\0'):
        if not entry:
            continue
        info, name = entry.split('\t', 1)
        mode, object_id, stage = info.split()
        require(mode in {'100644', '100755'} and stage == '0', f'Unsupported tracked Git entry: {name}')
        path = REPO/name
        require(path.read_bytes() == git('cat-file', 'blob', object_id), f'Tracked bytes differ from Git blob: {name}')
        require(path.name not in {'cshape_path.npz', 'new_python_high_precision.npz', 'old_python_high_precision.npz', 'matlab_high_precision.npz'},
                'Large complete path arrays must stay outside the Git repository')
        tracked.append(name)
        add(path)
    add(WHEEL)
    add(OLD_WHEEL)
    for path in sorted((ROOT/'docs').glob('*.md')):
        add(path)
    add(ROOT/'HF2_REPAIR_EVIDENCE_README.md', 'EVIDENCE_README.md')
    for path in sorted(RESULTS.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(RESULTS)
        if any(part in {'__pycache__', 'steps', '.pytest_cache'} or part.startswith('.venv') for part in relative.parts):
            continue
        # The initial partial HP checkpoints are immutable resume inputs. Keep
        # them even when the resumed output also supplies combined arrays.
        if path.suffix.lower() in {'.pyc', '.tmp'}:
            continue
        add(path)

    historical = integrity['historical_audits']
    metadata = {'stage': 'HF-2 repaired numerical closure', 'implementation_version': '0.2.1',
                'new_scientific_status': {'numerical_closure': 'pass', 'internal_tolerance': 1e-9,
                    'external_tolerance': 1e-8, 'expression_force_budget': 1e-9,
                    'original_targets': 100, 'accepted_states': integrity['new_accepted_states'],
                    'all_new_HP_states': 'pass', 'seven_original_response_metrics': 'pass', 'detached_checks': 24},
                'historical_scientific_status': {'original_HF2_stage': 'partially_complete',
                    'original_comparison': 'not_pass', 'old_results_never_overwritten': True,
                    'full_HP_reaudit': historical},
                'git_commit': revision, 'wheel_sha256': digest(WHEEL), 'legacy_wheel_sha256': digest(OLD_WHEEL),
                'runtime_source_sha256': integrity['runtime_source_sha256'], 'base_release_sha256': digest(BASE_ZIP),
                'resource_amendment_sha256': digest(AMENDMENT),
                'initial_HP_timeout_preserved': integrity['initial_HP_timeout_preserved'],
                'HP_completed_evidence_directory': integrity['HP_completed_evidence_directory'],
                'entry': 'EVIDENCE_README.md', 'HF3_executed': False, 'physical_contact_accuracy': 'not_validated',
                'scope': 'Specified discrete source-numeric code benchmark: numerical expression and equilibrium accuracy only',
                'omissions': 'No LF source, original ZIP/PDF, MATLAB .m/.mat, virtual environments or duplicate cshape steps. Initial partial HP checkpoints and the completed resume are both retained. Historical absolute paths are inert provenance.'}
    release_bytes = (json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
    records = []
    require(OUTPUT_ZIP.resolve() != BASE_ZIP.resolve(), 'New release must never overwrite the old archive')
    OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BASE_ZIP) as base, zipfile.ZipFile(OUTPUT_ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for name, (kind, source) in sorted(members.items()):
            hasher, size = hashlib.sha256(), 0
            reader = base.open(source) if kind == 'base' else source.open('rb')
            with reader, output.open(name, 'w', force_zip64=True) as destination:
                while chunk := reader.read(1024*1024):
                    destination.write(chunk)
                    hasher.update(chunk)
                    size += len(chunk)
            records.append({'path': name, 'bytes': size, 'sha256': hasher.hexdigest()})
        output.writestr('RELEASE.json', release_bytes)
        records.append({'path': 'RELEASE.json', 'bytes': len(release_bytes), 'sha256': hashlib.sha256(release_bytes).hexdigest()})
        files_payload = {'self_excluded': 'PACKAGE_FILES.json', 'files': records}
        files_bytes = (json.dumps(files_payload, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        output.writestr('PACKAGE_FILES.json', files_bytes)
    with zipfile.ZipFile(OUTPUT_ZIP) as archive:
        require(archive.testzip() is None, 'New ZIP CRC failure')
        require(len(archive.namelist()) == len(set(archive.namelist())) == len(records)+1, 'Duplicate or unindexed ZIP members')
        require(archive.read('PACKAGE_FILES.json') == files_bytes, 'Packaged member index differs from its generated bytes')
        for record in records:
            with archive.open(record['path']) as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == record['sha256'], f'Packaged hash mismatch: {record["path"]}')
            require(archive.getinfo(record['path']).file_size == record['bytes'], 'Packaged file size mismatch')
        dataset_records = {record['path'][len('geometry_dataset/'):]: record['sha256'] for record in records if record['path'].startswith('geometry_dataset/')}
        require(dataset_records == read(ROOT/'hf1_results/detached_location.json')['dataset_hashes_before'], 'Packaged dataset not identical to HF1 395 files')
    # Last check protects the originals even if packaging itself is later edited.
    hash_bindings(read(RESULTS/'frozen_inputs.json')['files'])
    release = dict(metadata, file=OUTPUT_ZIP.name, bytes=OUTPUT_ZIP.stat().st_size, sha256=digest(OUTPUT_ZIP),
                   members=len(records)+1, tracked_files=len(tracked), all_tracked_bytes_equal_git_blobs=True,
                   archive_CRC_and_each_real_file_hash='pass', dataset_files=395,
                   package_files_index_sha256=hashlib.sha256(files_bytes).hexdigest(),
                   compact_git_evidence_only=True, old_base_release_unchanged=True)
    write(ROOT/'deliverables/HF2_repair_release_manifest.json', release)
    return release


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('verify', 'package'))
    args = parser.parse_args()
    print(json.dumps(verify() if args.action == 'verify' else package(), ensure_ascii=False, indent=2, allow_nan=False))
