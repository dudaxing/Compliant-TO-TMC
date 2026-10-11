"""Audit saved ordinary terminal evidence, without NumPy/HF or integration."""
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/nested_material_volume_001'
STAGE = ROOT / REL
RUN = STAGE / 'run_001'
OUT = Path(__file__).resolve().parent
SOURCE = '7ea78ce19ba066dfce8a03892395d5604707dda6'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()
git = lambda *args: subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()

protocol = read(STAGE / 'protocol.json')
launch = read(STAGE / 'volume_launch.json')
helper = read(RUN / 'execution_receipt.json')
authorization = read(STAGE / 'author/authorization.json')
source_publication = read(STAGE / 'author/M_VOLUME1_source_publication_receipt.json')
volume = read(RUN / 'material_volume.json')
scope = read(STAGE / 'author/input_scope.json')
trace = read(ROOT / protocol['material_trace_file'])
protocol_sha = sha(STAGE / 'protocol.json')

assert git('rev-parse', 'HEAD') == SOURCE
assert git('branch', '--show-current') == 'main'
assert git('remote', 'get-url', 'origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
assert source_publication['status'] == 'published_and_incrementally_restored_pass'
assert source_publication['published_commit'] == SOURCE and source_publication['remote_main_confirmed_equal']
assert source_publication['source_and_restore_clean'] and source_publication['protocol_sha256'] == protocol_sha
assert source_publication['binding_count'] == 31 and source_publication['authorized'] is False and source_publication['executed'] is False
assert (STAGE / 'author/M_VOLUME1_source_publication_receipt.json').read_bytes() == Path('D:/hf-native-workpiece-api-author-20261009/MVOLUME1_source_prepare_001/publication_receipt.json').read_bytes()
assert authorization['status'] == 'direct_human_authorization_recorded_before_one_execution'
assert authorization['direct_human_answer'] == '批准按 M-VOLUME1 卡执行'
assert authorization['approved_source_commit'] == SOURCE
assert authorization['authorized'] is True and authorization['executed_at_record'] is False
assert authorization['protocol_sha256'] == protocol_sha and authorization['card_sha256'] == sha(ROOT / authorization['card'])
assert authorization['resource'] == dict(helper_seconds=180, outer_seconds=240, sampled_RSS_bytes=8589934592)
assert datetime.fromisoformat(source_publication['created_utc']) < datetime.fromisoformat(authorization['recorded_utc']) < datetime.fromisoformat(launch['started_utc']) < datetime.fromisoformat(launch['completed_utc'])
assert protocol['prepared'] is True and protocol['authorized'] is False and protocol['executed'] is False
assert protocol['selected_cell_ids'] == [10406, 10407]
assert protocol['selected_states'] == scope['selected_states']
assert len(protocol['bindings']) == 31
assert launch['bindings'] == protocol['bindings']
assert all(sha(ROOT / path) == pin for path, pin in protocol['bindings'].items())
for path in ('hf_repo/src/hf_eval/saved_material_volume.py', REL + '/execute_saved_material_volume.py', REL + '/launch_volume.py', REL + '/protocol.json', REL + '/M-VOLUME1_CARD.md'):
    original = subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT)
    assert original == (ROOT / path).read_bytes()
for path, pin in source_publication['peer_reviews'].items():
    assert sha(ROOT / path) == pin

assert launch['phase'] == 'volume' and launch['status'] == 'pass' and launch['invocations'] == 1
assert launch['exit_code'] == 0 and launch['stop_reason'] is None and launch['all_bindings_unchanged'] is True
assert launch['protocol_sha256'] == helper['protocol_sha256'] == protocol_sha
assert launch['outer_seconds'] == 240 and launch['sampled_RSS_limit_bytes'] == 8589934592
assert launch['argv'][1:] == ['-B', *protocol['phases']['volume']['argv']]
assert 'venv-handoff' in launch['argv'][0] and launch['argv'][0].endswith('python.exe')
assert helper['status'] == 'pass' and helper['all_bindings_unchanged'] is True
assert helper['mechanical_hooks_monitored'] is False
assert helper['calls'] == protocol['expected_calls'] == dict(NPZ_read_started=3, NPZ_read_completed=3,
    selected_array_fields=9, volume_started=2, volume_completed=2, PNG_writes=2)
assert helper['counts'] == volume['counts'] == protocol['expected_counts'] == dict(samples_total=36, depth_rows_total=12, cells_total=4)
assert 0 < helper['elapsed_seconds'] < launch['elapsed_seconds'] < 240
assert helper['elapsed_seconds'] < 180
assert 0 < helper['sampled_peak_RSS_bytes'] <= launch['peak_sampled_tree_RSS_bytes'] < 8589934592
assert not (STAGE / 'stop_requested.txt').exists()
stdout = (STAGE / 'volume_stdout.log').read_text(encoding='utf-8').splitlines()
assert len(stdout) == 1 and json.loads(stdout[0]) == dict(status='pass', calls=helper['calls'])

names = set(protocol['expected_output_files'])
assert names == {path.name for path in RUN.iterdir()}
assert len(names) == 7 and names - {'execution_receipt.json'} == set(helper['output_SHA256'])
outputs = {}
for name in sorted(names):
    path = RUN / name
    identity = dict(path=(Path(REL) / 'run_001' / name).as_posix(), bytes=path.stat().st_size, sha256=sha(path))
    if name in helper['output_SHA256']:
        assert identity['sha256'] == helper['output_SHA256'][name]
        identity['matches_helper_output_hash'] = True
    else:
        identity['separately_hashed_receipt_not_self_bound'] = True
    if name.endswith('.png'):
        header = path.read_bytes()[:24]
        assert header[:8] == b'\x89PNG\r\n\x1a\n' and header[12:16] == b'IHDR'
        identity['PNG_IHDR_dimensions'] = list(struct.unpack('>II', header[16:24]))
        assert identity['PNG_IHDR_dimensions'] == [2100, 2400]
    outputs[name] = identity


def rows(name):
    with (RUN / name).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def vectors(prefix, value):
    return {prefix + '_F' + axis + '_N': value[index] for index, axis in enumerate('xy')}


def compare(saved, expected):
    assert list(saved) == list(expected)
    for key, value in expected.items():
        if isinstance(value, list):
            actual = json.loads(saved[key])
        elif isinstance(value, int):
            actual = int(saved[key])
        elif isinstance(value, float):
            actual = float(saved[key])
        else:
            actual = saved[key]
        assert actual == value, (key, actual, value)


samples = rows('samples.csv')
depths = rows('depths.csv')
comparisons = rows('cell_comparisons.csv')
assert (len(samples), len(depths), len(comparisons)) == (36, 12, 4)
assert volume['schema_version'] == 'saved-two-state-bottom-owner-material-volume-1.0'
assert len(volume['states']) == 2
expected_sample_rows, expected_depth_rows, expected_cell_rows = [], [], []
case_checks = []
for identity, saved in zip(protocol['selected_states'], volume['states']):
    assert saved['identity'] == identity
    assert saved['counts'] == dict(samples=18, depths=6, cells=2)
    assert [cell['cell_id'] for cell in saved['cells']] == [10406, 10407]
    original_trace = next(item for item in trace['states'] if item['identity'] == identity)
    for cell in saved['cells']:
        base = dict(identity, cell_id=cell['cell_id'])
        prior = next(item for item in scope['selected_copied_existing_cell_and_edge_records']
            if item['identity'] == identity and int(item['cell_support_CSV']['cell_id']) == cell['cell_id'])
        old_support = prior['cell_support_CSV']
        old_edge = next(edge for edge in original_trace['edges'] if edge['outer_cell_id'] == cell['cell_id'])
        assert cell['node_ids'] == json.loads(old_support['node_ids']) == old_edge['outer_node_ids']
        assert cell['selected_local_indices'] == json.loads(old_support['selected_local_indices']) == [2, 3]
        assert cell['selected_body_node_ids'] == json.loads(old_support['selected_body_node_ids'])
        assert cell['saved_weak_material_on_body_N'] == [float(old_support['body_material_Fx_N']), float(old_support['body_material_Fy_N'])]
        assert cell['saved_top_material_line_on_body_N'] == old_edge['material_line_estimate_on_body_N']
        for occurrence in prior['local_occurrence_CSV']:
            local = int(occurrence['local_node_index'])
            assert cell['original_local_internal_material_force_N'][local] == [float(occurrence['original_local_internal_material_Fx_N']), float(occurrence['original_local_internal_material_Fy_N'])]
        gate = cell['same_q_term_regrouping']
        assert gate['passed'] is True and gate['bound_source'] == '8*eps*sum(abs(the same nine computed q terms)); no absolute floor'
        assert len(gate['error_N']) == len(gate['roundoff_bound_N']) == 2
        assert all(bound >= 0 and abs(error) <= bound for error, bound in zip(gate['error_N'], gate['roundoff_bound_N']))
        assert [sample['point_index'] for sample in cell['samples']] == list(range(9))
        assert [(row['eta'], row['point_indices']) for row in cell['depths']] == [(-1.0, [0, 3, 6]), (0.0, [1, 4, 7]), (1.0, [2, 5, 8])]
        for sample in cell['samples']:
            P = sample['P_normal_column_MPa']
            expected_sample_rows.append(dict(base, point_index=sample['point_index'], xi=sample['reference_point'][0], eta=sample['reference_point'][1],
                x_mm=sample['coordinates_mm'][0], y_mm=sample['coordinates_mm'][1], P_xy_MPa=P[0], P_yy_MPa=P[1],
                saved_volume_weight_mm3=sample['saved_volume_weight_mm3'],
                selected_basis_gradient_x_per_mm=sample['selected_basis_gradient_per_mm'][0],
                selected_basis_gradient_y_per_mm=sample['selected_basis_gradient_per_mm'][1],
                **vectors('rounded_P_volume_contribution', sample['rounded_P_volume_contribution_on_body_N'])))
        for original_sample in old_edge['samples']:
            sample = cell['samples'][original_sample['point_index']]
            assert sample['reference_point'] == original_sample['reference_point']
            assert sample['coordinates_mm'] == original_sample['coordinates_mm']
            assert sample['P_normal_column_MPa'] == [matrix_row[1] for matrix_row in original_sample['P_MPa']]
        for row in cell['depths']:
            expected_depth_rows.append(dict(base, eta=row['eta'], point_indices=row['point_indices'],
                **vectors('C_eta', row['C_eta_on_body_N']), **vectors('regrouped_same_q_terms', row['regrouped_same_q_terms_on_body_N']),
                **vectors('geometric_depth_contribution', row['geometric_depth_contribution_on_body_N'])))
        expected_cell = dict(base, node_ids=cell['node_ids'], selected_local_indices=cell['selected_local_indices'], selected_body_node_ids=cell['selected_body_node_ids'])
        assert len(cell['original_local_internal_material_force_N']) == 4
        for local, value in enumerate(cell['original_local_internal_material_force_N']):
            assert len(value) == 2
            expected_cell.update(vectors('original_local_' + str(local) + '_internal_material', value))
        for prefix, name in (('saved_weak_material', 'saved_weak_material_on_body_N'), ('saved_top_material_line', 'saved_top_material_line_on_body_N'),
            ('rounded_P_direct_volume', 'rounded_P_direct_volume_on_body_N'), ('regrouped_same_q_terms', 'regrouped_same_q_terms_on_body_N'),
            ('geometric_three_depth_volume', 'geometric_three_depth_volume_on_body_N'), ('geometric_depth_gap', 'geometric_depth_gap_on_body_N')):
            expected_cell.update(vectors(prefix, cell[name]))
        expected_cell.update(vectors('same_q_term_regrouping_error', gate['error_N']))
        expected_cell.update(vectors('same_q_term_regrouping_roundoff_bound', gate['roundoff_bound_N']))
        assert len(cell['descriptive_differences_N']) == 7
        for name, value in cell['descriptive_differences_N'].items():
            expected_cell.update(vectors(name, value))
        expected_cell_rows.append(expected_cell)
        case_checks.append(dict(identity=identity, cell_id=cell['cell_id'], original_W_preserved_exact=True, original_T_preserved_exact=True,
            original_selected_local_force_preserved_exact=True, top_P_column_and_reference_coordinates_preserved_exact=True,
            saved_same_q_term_gate=gate, samples_count=9, depths_count=3, signed_descriptive_differences=cell['descriptive_differences_N']))
for actual, expected in ((samples, expected_sample_rows), (depths, expected_depth_rows), (comparisons, expected_cell_rows)):
    assert len(actual) == len(expected)
    for saved, item in zip(actual, expected):
        compare(saved, item)

review = dict(schema_version='saved-bottom-material-volume-terminal-execution-review-1.0',
    status='pass_actual_saved_execution_terminal_review', created_UTC=datetime.now(timezone.utc).isoformat(),
    reviewer_role='Independent source/input/terminal reviewer; no candidate rerun', repo_root=str(ROOT), approved_source_commit=SOURCE,
    authorization=dict(path=REL + '/author/authorization.json', sha256=sha(STAGE / 'author/authorization.json'),
        direct_human_answer=authorization['direct_human_answer'], questionItemId=authorization['questionItemId'],
        recorded_UTC=authorization['recorded_utc'], source_publication_precedes_authorization_precedes_launch=True),
    source_publication=dict(path=REL + '/author/M_VOLUME1_source_publication_receipt.json', sha256=sha(STAGE / 'author/M_VOLUME1_source_publication_receipt.json'),
        published_commit=source_publication['published_commit'], status=source_publication['status'], matching_actual_external_receipt=True),
    protocol_sha256=protocol_sha, all31_actual_pins_raw_SHA_pass=True, historical_false_flags_preserved_separate_human_authorization=True,
    actual_launcher_terminal=dict(path=REL + '/volume_launch.json', sha256=sha(STAGE / 'volume_launch.json'),
        status=launch['status'], invocations=launch['invocations'], exit_code=launch['exit_code'], stop_reason=launch['stop_reason'],
        elapsed_seconds=launch['elapsed_seconds'], sampled_peak_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
        started_UTC=launch['started_utc'], completed_UTC=launch['completed_utc'], complete_process_terminal_scope=True),
    actual_helper_receipt=dict(path=REL + '/run_001/execution_receipt.json', sha256=sha(RUN / 'execution_receipt.json'),
        status=helper['status'], calls=helper['calls'], counts=helper['counts'], elapsed_seconds=helper['elapsed_seconds'],
        sampled_peak_RSS_bytes=helper['sampled_peak_RSS_bytes'], cost_scope='Snapshot after output hashes/final checkpoint, before success receipt construction/write; outer covers complete process terminal',
        mechanical_hooks_monitored=False),
    exact_output_names_and_raw_SHA_verified=outputs, rows=dict(samples=36, depths=12, cell_comparisons=4),
    all_CSV_headers_rows_fields_and_JSON_values_exactly_matched=True,
    four_case_original_associations_and_saved_gates=case_checks,
    stop_and_unique_run=dict(stop_file_absent=True, stdout_single_PASS_record=True, stdout_sha256=sha(STAGE / 'volume_stdout.log'),
        invocations1_exit0_no_stop_record=True, launcher_refuses_preexisting_launch_receipt_and_stdout=True,
        worker_refuses_preexisting_output_directory=True, recorded_no_retry_repair_rerun_extension_force=True),
    issues=[],
    scope_limits=['Existing JSON/CSV and raw bytes only; no NPZ field decode, candidate import/API rerun, contraction, integration or fsum recomputation.',
        'Saved same-q-term errors/bounds and PASS are checked as recorded; their q-term L1 calculation is not rerun.',
        'Field read/API counts are source/receipt evidence, not independently instrumented mechanical hooks.',
        'PNG raw SHA/IHDR dimensions verified; this terminal audit does not inspect pixels or establish visual readability.',
        'Signed W/V/T and geometric differences remain descriptive; no original DD replay, material pressure/Hu traction, effective grip or full HF5 qualification is added.'],
    reviewer_activity=dict(ordinary_JSON_CSV_source_and_raw_SHA_reads=True, NPZ_field_decodes=0, candidate_imports=0, API_reruns=0,
        new_contraction_integration_fsum_calls=0, force_kernel_tangent_HP_equilibrium_calls=0, new_PNG_renders=0, repo_mutations=0,
        external_review_report_only=True))
target = OUT / 'terminal_execution_review.json'
target.write_text(json.dumps(review, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
print(json.dumps(dict(status=review['status'], path=str(target), sha256=sha(target), rows=review['rows']), ensure_ascii=False))
