"""Review actual saved M-BOUND1 terminal records; never import/run mechanics.

This file is prepared before authorization. main() needs genuine future launch,
helper and output records; merely parsing this source produces no terminal PASS.
"""
import csv
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import struct
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
STAGE = ROOT / REL
RUN = STAGE / 'run_001'
OUT = Path(__file__).resolve().parent
SOURCE = 'eb68c00d50b28de89a475c18a0879be4a4482f68'
PROTOCOL_SHA = 'f27d201b01efc5c49212a43536e928ba6ac88ba4346ac6949dccdfcac8d94e33'
SOURCE_PUBLICATION = OUT.parent / 'MBOUND1_source_prepare_001/publication_receipt.json'
FORCE_COLUMNS = [part+'_F'+axis+'_N' for part in ('total','material','regularization') for axis in 'xy']


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    value = sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def identity(row):
    return dict(index=int(row['index']), original_target_index=int(row['original_target_index']),
        leg=row['leg'], d_mm=float(row['d_mm']), state_sha256=row['state_sha256'])


def vectors(prefix, values):
    assert len(values) == 2 and all(isfinite(value) for value in values)
    return {prefix+'_F'+axis+'_N': values[index] for index, axis in enumerate('xy')}


def compare_csv(saved, expected):
    """Compare recorded fields only; original string columns remain exact text."""
    assert list(saved) == list(expected)
    for key, value in expected.items():
        if isinstance(value, list):
            actual = json.loads(saved[key])
        elif isinstance(value, bool):
            assert saved[key] == str(value), (key, saved[key], value)
            continue
        elif isinstance(value, int):
            actual = int(saved[key])
        elif isinstance(value, float):
            actual = float(saved[key])
            assert isfinite(actual)
        else:
            actual = saved[key]
        assert actual == value, (key, actual, value)


def saved_gate(record, source):
    """Check saved success/error/bound fields, without recalculating the L1."""
    assert record['passed'] is True
    assert record['bound_source'] == source+'; 8eps times L1, no floor'
    assert len(record['error_N']) == len(record['roundoff_bound_N']) == 2
    for error, bound in zip(record['error_N'], record['roundoff_bound_N']):
        assert isfinite(error) and isfinite(bound) and bound >= 0 and abs(error) <= bound


def main():
    # These reads fail before any report write when real execution is absent.
    protocol = read(STAGE / 'protocol.json')
    authorization = read(STAGE / 'author/authorization.json')
    publication = read(SOURCE_PUBLICATION)
    archived_publication_file = STAGE / 'author/M_BOUND1_source_publication_receipt.json'
    direct_reply_file = STAGE / 'author/direct_human_reply.json'
    direct_reply = read(direct_reply_file)
    launch = read(STAGE / 'hu_boundary_launch.json')
    helper = read(RUN / 'execution_receipt.json')
    result = read(RUN / 'hu_boundary.json')
    scope = read(STAGE / 'author/final_input_scope.json')
    protocol_sha = sha(STAGE / 'protocol.json')
    assert protocol_sha == PROTOCOL_SHA
    assert git('rev-parse', 'HEAD') == SOURCE
    assert git('branch', '--show-current') == 'main'
    assert git('remote', 'get-url', 'origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    assert publication['status'] == 'published_and_incrementally_restored_pass'
    assert publication['published_commit'] == SOURCE and publication['remote_main_confirmed_equal']
    assert publication['source_and_restore_clean'] and publication['protocol_sha256'] == protocol_sha
    assert publication['binding_count'] == 45
    assert publication['authorized'] is False and publication['executed'] is False
    assert archived_publication_file.read_bytes() == SOURCE_PUBLICATION.read_bytes()
    for name, pin in publication['peer_reviews'].items():
        assert sha(ROOT / name) == pin
    assert authorization['status'] == 'direct_human_authorization_recorded_before_one_execution'
    assert direct_reply['authorization_from_direct_human_reply'] is True
    assert direct_reply['card'] == 'M-BOUND1' and direct_reply['approved_source_commit'] == SOURCE
    assert isinstance(authorization['direct_human_answer'], str) and authorization['direct_human_answer'].strip()
    assert isinstance(authorization['reply_context'], str) and authorization['reply_context'].strip()
    assert authorization['direct_human_answer'] == direct_reply['direct_human_answer']
    assert authorization['reply_context'] == direct_reply['reply_context']
    assert authorization.get('questionItemId') == direct_reply.get('questionItemId')
    assert authorization['human_evidence_sha256'] == sha(direct_reply_file)
    assert authorization['approved_source_commit'] == SOURCE
    assert authorization['authorized'] is True and authorization['executed_at_record'] is False
    assert authorization['protocol_sha256'] == protocol_sha
    assert authorization['card'] == protocol['card']
    assert authorization['card_sha256'] == sha(ROOT / authorization['card'])
    assert authorization['resource'] == dict(helper_seconds=180, outer_seconds=240, sampled_RSS_bytes=8589934592)
    assert datetime.fromisoformat(publication['created_utc']) < datetime.fromisoformat(authorization['recorded_utc'])
    assert datetime.fromisoformat(authorization['recorded_utc']) < datetime.fromisoformat(launch['started_utc'])
    assert datetime.fromisoformat(launch['started_utc']) < datetime.fromisoformat(launch['completed_utc'])
    assert protocol['prepared'] is True and protocol['authorized'] is False and protocol['executed'] is False
    assert protocol['selected_states'] == scope['selected_states']
    assert protocol['selected_endpoint_cell_ids'] == [10371,10407,10408]
    assert len(protocol['bindings']) == 45 and launch['bindings'] == protocol['bindings']
    for name, pin in protocol['bindings'].items():
        assert sha(ROOT / name) == pin
    for name in ('hf_repo/src/hf_eval/saved_q1_hu_boundary.py', REL+'/execute_saved_hu_boundary.py',
            REL+'/launch_boundary.py', REL+'/protocol.json', REL+'/M-BOUND1_CARD.md'):
        original = subprocess.check_output(['git', 'show', SOURCE+':'+name], cwd=ROOT)
        assert original == (ROOT / name).read_bytes()
    assert len(protocol['selected_archive_plan']) == 2
    for plan, original in zip(protocol['selected_archive_plan'], scope['selected_archive_plan']):
        assert plan == {key: original[key] for key in
            ('path','path_base','declared_archive_sha256','selected_fields','array_fields_decoded')}
        assert list(plan['selected_fields']) == ['element_regularization_force']
        assert plan['selected_fields']['element_regularization_force']['dtype'] == 'float64'
        assert plan['selected_fields']['element_regularization_force']['shape'] == [13440,8]
    assert launch['phase'] == 'hu_boundary' and launch['status'] == 'pass' and launch['invocations'] == 1
    assert launch['exit_code'] == 0 and launch['stop_reason'] is None and launch['all_bindings_unchanged'] is True
    assert launch['protocol_sha256'] == helper['protocol_sha256'] == protocol_sha
    assert launch['outer_seconds'] == 240 and launch['sampled_RSS_limit_bytes'] == 8589934592
    assert launch['argv'][1:] == ['-B', *protocol['phases']['hu_boundary']['argv']]
    assert 'venv-handoff' in launch['argv'][0] and launch['argv'][0].endswith('python.exe')
    assert helper['status'] == 'pass' and helper['all_bindings_unchanged'] is True
    assert helper['mechanical_hooks_monitored'] is False
    assert helper['calls'] == protocol['expected_calls'] == dict(NPZ_read_started=2, NPZ_read_completed=2,
        selected_array_fields=2, hu_boundary_started=2, hu_boundary_completed=2, PNG_writes=2)
    counts = dict(cells_total=1444, group_rows_total=10, whole_rows_total=2, nodes_total=1406,
        selected_endpoint_rows_total=24, node_category_rows_total=14)
    assert helper['counts'] == result['counts'] == protocol['expected_counts'] == counts
    assert 0 < helper['elapsed_seconds'] < 180
    assert helper['elapsed_seconds'] < launch['elapsed_seconds'] < 240
    # Sampling schedules differ: do not impose an ordering between the two RSS maxima.
    assert 0 < helper['sampled_peak_RSS_bytes'] < 8589934592
    assert 0 < launch['peak_sampled_tree_RSS_bytes'] < 8589934592
    assert not (STAGE / 'stop_requested.txt').exists()
    stdout = (STAGE / 'hu_boundary_stdout.log').read_text(encoding='utf-8').splitlines()
    stdout_JSON_records, stdout_nonJSON_lines = [], []
    for line_number, line in enumerate(stdout, 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            stdout_nonJSON_lines.append(dict(line_number=line_number,text=line))
        else:
            stdout_JSON_records.append(dict(line_number=line_number,record=record))
    exact_PASS = dict(status='pass',calls=helper['calls'])
    stdout_PASS_records = [record for record in stdout_JSON_records if record['record'] == exact_PASS]
    assert len(stdout_PASS_records) == 1
    stdout_other_JSON_records = [record for record in stdout_JSON_records if record['record'] != exact_PASS]
    names = set(protocol['expected_output_files'])
    assert len(names) == 10 and names == {path.name for path in RUN.iterdir()}
    assert names-{'execution_receipt.json'} == set(helper['output_SHA256'])
    outputs = {}
    source_nominal_png_dimensions = {'Q1_Hu_endpoint_actions.png':[2400,1500], 'Hu_owner_node_comparison.png':[2400,1800]}
    for name in sorted(names):
        path = RUN / name
        record = dict(path=(Path(REL)/'run_001'/name).as_posix(), bytes=path.stat().st_size, sha256=sha(path))
        if name == 'execution_receipt.json':
            record['separately_hashed_receipt_not_self_bound'] = True
        else:
            assert record['sha256'] == helper['output_SHA256'][name]
            record['matches_helper_output_hash'] = True
        if name.endswith('.png'):
            with path.open('rb') as stream:
                header = stream.read(24)
            assert header[:8] == b'\x89PNG\r\n\x1a\n' and header[12:16] == b'IHDR'
            record['PNG_IHDR_dimensions'] = list(struct.unpack('>II', header[16:24]))
            record['source_nominal_PNG_dimensions_descriptive_only'] = source_nominal_png_dimensions[name]
        outputs[name] = record
    assert result['schema_version'] == 'saved-two-state-Q1-Hu-boundary-1.0'
    assert result['actual_deformation_view'] == protocol['actual_deformation_view']
    assert result['geometry_scope'] == 'Reference grid only; reuse original actual-deformation view'
    assert len(result['states']) == 2
    _, source_support = rows(ROOT / protocol['material_support_cells_file'])
    source_node_columns, source_nodes = rows(ROOT / protocol['ledger_nodes_file'])
    source_category_columns, source_categories = rows(ROOT / protocol['ledger_categories_file'])
    source_support = {(int(row['index']),int(row['cell_id'])): row for row in source_support}
    source_nodes = {(int(row['index']),int(row['node_id'])): row for row in source_nodes if int(row['index']) in (6,13)}
    source_categories = [row for row in source_categories if int(row['index']) in (6,13)]
    assert len(source_nodes) == 1406 and len(source_categories) == 14
    assert result['original_node_categories'] == source_categories
    endpoint_scope = {(item['index'],item['cell_id'],item['local_node']):item
        for item in scope['endpoint_geometry_metadata_records']}
    expected = {name: [] for name in ('cells.csv','groups.csv','whole.csv','nodes.csv','selected_endpoints.csv')}
    states_review = []
    node_gates = []
    for selected, saved in zip(protocol['selected_states'], result['states']):
        assert saved['identity'] == selected
        index = selected['index']
        assert saved['counts'] == dict(cells=722,local_occurrences=2738,groups=5,whole=1,nodes=703,selected_endpoints=12)
        assert saved['original_Hu_pattern'] == dict(support_cells_checked=722,numeric_exact=True,byte_or_signed_zero_gate=False)
        assert saved['original_body_scatter'] == dict(calls=1,body_DOFs=1406,numeric_exact=True,
            order='Ascending original cell/local/component C order; internal bincount then negate; body DOFs only')
        assert len(saved['cells']) == 722 and len(saved['nodes']) == 703 and len(saved['selected_endpoints']) == 12
        assert [cell['cell_id'] for cell in saved['cells']] == sorted(set(cell['cell_id'] for cell in saved['cells']))
        assert list(saved['groups']) == ['body','bottom_owner','left_owner','right_owner','corner_only']
        assert [cell['cell_id'] for cell in saved['corner_only_cells']] == [10371,10408]
        occurrences = Counter()
        role_occurrences = Counter()
        role_cell_counts = Counter()
        for cell in saved['corner_only_cells']:
            assert cell == next(item for item in saved['cells'] if item['cell_id'] == cell['cell_id'])
        for cell in saved['cells']:
            old = source_support[(index,cell['cell_id'])]
            assert identity(old) == selected and cell['group'] == old['group']
            assert cell['node_ids'] == json.loads(old['node_ids'])
            assert cell['selected_local_indices'] == json.loads(old['selected_local_indices'])
            assert cell['selected_body_node_ids'] == json.loads(old['selected_body_node_ids'])
            assert cell['selected_local_node_count'] == int(old['selected_local_node_count'])
            occurrences.update(cell['selected_body_node_ids'])
            role_occurrences[cell['group']] += cell['selected_local_node_count']
            role_cell_counts[cell['group']] += 1
            assert cell['Q1_pattern_numeric_exact'] is True and cell['Q1_sign_pattern'] == [1.,-1.,1.,-1.]
            assert len(cell['original_local_internal_Hu_force_N']) == 4
            assert cell['original_BL_internal_Hu_N'] == cell['original_local_internal_Hu_force_N'][0]
            row = dict(selected,cell_id=cell['cell_id'],group=cell['group'],node_ids=cell['node_ids'],
                selected_local_indices=cell['selected_local_indices'],selected_body_node_ids=cell['selected_body_node_ids'],
                selected_local_node_count=cell['selected_local_node_count'],Q1_pattern_numeric_exact=cell['Q1_pattern_numeric_exact'])
            for local, value in enumerate(cell['original_local_internal_Hu_force_N']):
                row.update(vectors('original_'+str(local)+'_internal_Hu',value))
            row.update(vectors('selected_body_Hu',cell['force_on_body_N']))
            expected['cells.csv'].append(row)
        for name, group in saved['groups'].items():
            assert group['cell_count'] == role_cell_counts[name]
            assert group['local_occurrence_count'] == role_occurrences[name]
            expected['groups.csv'].append(dict(selected,group=name,cell_count=group['cell_count'],
                local_occurrence_count=group['local_occurrence_count'],**vectors('selected_body_Hu',group['force_on_body_N'])))
        whole = saved['whole']
        state = read(ROOT / protocol['state_files'][str(index)])
        assert whole['original_state_Hu_on_body_N'] == state['workpiece']['force_on_lower_body_N']['regularization']
        saved_gate(whole['original_node_L1_comparison'],'original node Hu forces')
        saved_gate(whole['selected_local_L1_comparison'],'selected original local Hu forces')
        row = dict(selected)
        for name in ('regrouped_local_Hu_on_body_N','original_node_Hu_on_body_N','original_state_Hu_on_body_N','corner_only_Hu_on_body_N'):
            row.update(vectors(name.removesuffix('_N'),whole[name]))
        for name in ('original_node_L1_comparison','selected_local_L1_comparison'):
            row.update(vectors(name+'_error',whole[name]['error_N']))
            row.update(vectors(name+'_roundoff_bound',whole[name]['roundoff_bound_N']))
        for name, value in whole['descriptive_differences_N'].items():
            row.update(vectors(name,value))
        assert list(whole['descriptive_differences_N']) == ['local_minus_original_state','local_minus_corner_only','regrouped_five_roles_minus_local']
        expected['whole.csv'].append(row)
        original_state_nodes = sorted((node for state_index,node in source_nodes if state_index == index))
        assert [node['node_id'] for node in saved['nodes']] == original_state_nodes
        for node in saved['nodes']:
            old = source_nodes[(index,node['node_id'])]
            assert node['original_node_record'] == old
            assert list(node['original_node_record']) == source_node_columns
            assert all(node['original_node_record'][column] == old[column] for column in FORCE_COLUMNS)
            assert node['original_Hu_on_body_N'] == [float(old['regularization_F'+axis+'_N']) for axis in 'xy']
            assert 1 <= node['selected_local_occurrences'] <= 4
            assert node['selected_local_occurrences'] == occurrences[node['node_id']]
            saved_gate(node['local_regrouping'],'selected original local Hu forces')
            row = dict(old,selected_local_occurrences=node['selected_local_occurrences'],
                **vectors('regrouped_local_Hu',node['regrouped_local_Hu_on_body_N']),
                **vectors('local_regrouping_error',node['local_regrouping']['error_N']),
                **vectors('local_regrouping_roundoff_bound',node['local_regrouping']['roundoff_bound_N']))
            expected['nodes.csv'].append(row)
            node_gates.append(dict(index=index,node_id=node['node_id'],passed=True,
                error_N=node['local_regrouping']['error_N'],roundoff_bound_N=node['local_regrouping']['roundoff_bound_N']))
        assert [(endpoint['cell_id'],endpoint['local_node_index']) for endpoint in saved['selected_endpoints']] == [
            (cell,local) for cell in (10371,10407,10408) for local in range(4)]
        for endpoint in saved['selected_endpoints']:
            old = endpoint_scope[(index,endpoint['cell_id'],endpoint['local_node_index'])]
            assert endpoint['group'] == old['source_group'] and endpoint['node_id'] == old['node_id']
            assert endpoint['local_node_name'] == old['local_name']
            assert endpoint['coordinates_mm'] == old['reference_coordinates_mm']
            assert endpoint['selected_body_node'] == old['is_body_node']
            saved_cell = next(cell for cell in saved['cells'] if cell['cell_id'] == endpoint['cell_id'])
            assert endpoint['original_internal_Hu_force_N'] == saved_cell['original_local_internal_Hu_force_N'][endpoint['local_node_index']]
            assert endpoint['covector_scope'] == 'ON-body only if selected_body_node; otherwise negative local covector, not an applied physical load'
            row = dict(selected,cell_id=endpoint['cell_id'],group=endpoint['group'],local_node_index=endpoint['local_node_index'],
                local_node_name=endpoint['local_node_name'],node_id=endpoint['node_id'],x_mm=endpoint['coordinates_mm'][0],
                y_mm=endpoint['coordinates_mm'][1],selected_body_node=endpoint['selected_body_node'],
                **vectors('original_internal_Hu',endpoint['original_internal_Hu_force_N']),
                **vectors('negative_local_Hu_covector',endpoint['negative_local_Hu_covector_N']),covector_scope=endpoint['covector_scope'])
            expected['selected_endpoints.csv'].append(row)
        states_review.append(dict(identity=selected,original_state_whole_Hu_preserved_exact=True,
            original_S1_topology_exact=True,original_M2_node_records_and_six_force_texts_exact=True,
            recorded_pattern=saved['original_Hu_pattern'],recorded_body_scatter=saved['original_body_scatter'],
            saved_old_node_L1_gate=whole['original_node_L1_comparison'],
            saved_new_selected_local_L1_gate=whole['selected_local_L1_comparison'],
            checked_node_local_L1_gate_records=703,endpoint_geometry_and_selection_exact=True))
    expected_lengths = {'cells.csv':1444,'groups.csv':10,'whole.csv':2,'nodes.csv':1406,'selected_endpoints.csv':24}
    for name, expected_rows in expected.items():
        columns, actual = rows(RUN/name)
        assert len(actual) == len(expected_rows) == expected_lengths[name]
        assert columns == list(expected_rows[0])
        for saved, record in zip(actual,expected_rows):
            compare_csv(saved,record)
    category_columns, actual_categories = rows(RUN/'node_categories.csv')
    assert category_columns == source_category_columns and actual_categories == source_categories
    assert len(node_gates) == 1406
    review = dict(schema_version='saved-Q1-Hu-boundary-terminal-execution-review-1.0',
        status='pass_actual_saved_execution_terminal_review',created_UTC=datetime.now(timezone.utc).isoformat(),
        reviewer_role='Independent ordinary-record reviewer; no numerical replay',repo_root=str(ROOT),approved_source_commit=SOURCE,
        authorization=dict(path=REL+'/author/authorization.json',sha256=sha(STAGE/'author/authorization.json'),
            direct_human_answer=authorization['direct_human_answer'],questionItemId=authorization.get('questionItemId'),
            reply_context=authorization['reply_context'],
            archived_direct_reply_path=REL+'/author/direct_human_reply.json',
            archived_direct_reply_sha256=sha(direct_reply_file),
            original_answer_context_card_source_and_human_evidence_SHA_exact=True,
            approval_wording_not_restricted_to_a_literal=True,
            source_publication_precedes_recorded_authorization_precedes_launch=True),
        source_publication=dict(path=REL+'/author/M_BOUND1_source_publication_receipt.json',sha256=sha(archived_publication_file),
            matching_actual_external_publication_receipt=True,
            published_commit=publication['published_commit'],status=publication['status']),
        protocol_sha256=protocol_sha,all45_actual_pins_raw_SHA_pass=True,
        historical_false_flags_preserved_separate_human_authorization=True,
        actual_launcher_terminal=dict(path=REL+'/hu_boundary_launch.json',sha256=sha(STAGE/'hu_boundary_launch.json'),
            status=launch['status'],invocations=launch['invocations'],exit_code=launch['exit_code'],stop_reason=launch['stop_reason'],
            elapsed_seconds=launch['elapsed_seconds'],sampled_peak_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
            started_UTC=launch['started_utc'],completed_UTC=launch['completed_utc'],
            cost_scope='Completed helper child process and final binding check; elapsed snapshot before launcher final receipt write. No OS hard memory cap.'),
        actual_helper_receipt=dict(path=REL+'/run_001/execution_receipt.json',sha256=sha(RUN/'execution_receipt.json'),
            status=helper['status'],calls=helper['calls'],counts=helper['counts'],elapsed_seconds=helper['elapsed_seconds'],
            sampled_peak_RSS_bytes=helper['sampled_peak_RSS_bytes'],
            cost_scope='Final-checkpoint snapshot before success receipt construction/write; outer retains completed helper process terminal.',
            mechanical_hooks_monitored=False),
        exact_output_names_and_raw_SHA_verified=outputs,rows=counts,
        all_CSV_headers_rows_fields_and_JSON_values_exactly_matched=True,
        original14_category_full_text_rows_exact=True,original1406_node_six_force_text_rows_exact=True,
        saved_state_pattern_scatter_and_two_distinct_L1_gate_records=states_review,
        saved_node_local_L1_gate_records_checked=1406,
        stop_and_unique_run=dict(stop_file_absent=True,stdout_exact_protocol_PASS_object_count=1,
            stdout_exact_protocol_PASS_records=stdout_PASS_records,
            stdout_other_JSON_records_descriptive=stdout_other_JSON_records,
            stdout_nonJSON_warning_or_other_lines_descriptive=stdout_nonJSON_lines,
            stdout_total_lines_descriptive=len(stdout),stdout_no_total_line_count_gate=True,
            stdout_sha256=sha(STAGE/'hu_boundary_stdout.log'),invocations1_exit0_no_stop_record=True,
            source_once_guard_and_exclusive_output_directory_preserved=True,no_retry_repair_rerun_extension_force_in_records=True),
        issues=[],scope_limits=[
            'Ordinary JSON/CSV, source bytes and raw archive SHA only; no NPZ decode, candidate import, API rerun, new scientific fsum/integration or mechanics.',
            'Original local Hu values are checked for JSON/CSV consistency and recorded field descriptors; this review does not independently decode their original NPZ source.',
            'Pattern/scatter PASS and all local/node L1 errors/bounds are checked as saved. Their force arithmetic, exact Q1 pattern, bincount and L1 computations are not replayed.',
            'Field/API/PNG counts and absence of retries are source/receipt/unique-file evidence, not independent instrumentation. mechanical_hooks_monitored=false remains an honest limitation.',
            'Human authorization record identity/order is checked; this file alone cannot authenticate the originating human conversation.',
            'Two RSS maxima are separate samples. They are not hard caps or continuous peak observations, and are not required to have a particular ordering.',
            'PNG signature/raw SHA are checked. Actual IHDR and source nominal dimensions are descriptive only, with no size equality gate; pixels/readability require a separate visual inspection.',
            'The exact protocol PASS JSON object must occur once. Other stdout JSON/text lines are retained descriptively, allowing library warnings; no total-line-count gate is added. Only JSONDecodeError is classified as non-JSON text; other reader errors propagate.',
            'Owner/whole/corner differences remain descriptive. No continuous total pressure, unique edge/corner pressure allocation, effective grip, energy gradient or HF5 qualification is added.'],
        reviewer_activity=dict(ordinary_JSON_CSV_source_raw_SHA_reads=True,NPZ_field_decodes=0,candidate_imports=0,API_reruns=0,
            new_scientific_fsum_integration_force_recomputations=0,force_kernel_tangent_HP_equilibrium_calls=0,
            PNG_renders_or_pixel_decodes=0,repository_mutations=0,external_review_report_only=True))
    target = OUT/'terminal_execution_review.json'
    with target.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(review,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=review['status'],path=str(target),sha256=sha(target),rows=review['rows']),ensure_ascii=False))


if __name__ == '__main__':
    main()
