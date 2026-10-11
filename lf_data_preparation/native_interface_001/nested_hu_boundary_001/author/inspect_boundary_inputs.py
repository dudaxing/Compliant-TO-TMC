"""Ordinary source/descriptor/CSV and ZIP-directory inventory; no NPZ decoding."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import csv
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT = Path(__file__).resolve().parent
BASE = Path('lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square')
S1 = Path('lf_data_preparation/native_interface_001/nested_material_support_001')
M2 = Path('lf_data_preparation/native_interface_001/nested_ledger_002')
REF = Path('lf_data_preparation/native_interface_001/nested_reference_002/run_001/reference')
VIEW = Path('functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square')
read = lambda path: json.loads((ROOT / path).read_bytes())


def sha(path):
    result = sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def identity(path):
    file = ROOT / path
    return dict(path=path.as_posix(), bytes=file.stat().st_size, sha256=sha(file))


def rows(path):
    with (ROOT / path).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def record_identity(row):
    return dict(index=int(row['index']), original_target_index=int(row['original_target_index']), leg=row['leg'],
                d_mm=float(row['d_mm']), state_sha256=row['state_sha256'])


def archive(directory, descriptor, fields):
    relative = directory / descriptor['path']
    actual = sha(ROOT / relative)
    assert actual == descriptor['sha256']
    with ZipFile(ROOT / relative) as saved:
        members = {item.filename: item for item in saved.infolist()}
        selected = {field:dict(member=field + '.npy', uncompressed_bytes=members[field + '.npy'].file_size,
            compressed_bytes=members[field + '.npy'].compress_size, CRC=members[field + '.npy'].CRC) for field in fields}
        all_members = list(members)
    return dict(path=relative.as_posix(), path_base=directory.as_posix(), declared_archive_sha256=descriptor['sha256'],
        actual_archive_sha256=actual, selected_fields={field:descriptor['fields'][field] for field in fields},
        selected_ZIP_directory_metadata=selected, all_member_names=all_members,
        raw_archive_SHA_verified=True, NPY_header_or_payload_read=False, array_fields_decoded=False,
        field_dtype_shape_SHA_are_saved_descriptor_declarations=True)


head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == '0d83b18b2bb320f137b1c4c3295805dc7c15aa65'
model, result = read(BASE / 'model/model.json'), read(BASE / 'result.json')
ref = read(REF / 'summary.json')
s1_protocol, m2_protocol = read(S1 / 'protocol.json'), read(M2 / 'protocol.json')
assert ref['status'] == 'pass' and ref['accepted_states'] == 24
assert ref['HP_calls_started'] == ref['HP_calls_completed'] == 48
assert ref['result_sha256'] == sha(ROOT / BASE / 'result.json')
body = model['region_metadata']['workpiece']
node_ids = set(body['nodes'])
support_cells = rows(S1 / 'run_001/cells.csv')
ledger_nodes = rows(M2 / 'run_001/all_nodes.csv')
ledger_categories = rows(M2 / 'run_001/category_loads.csv')
original_nodes = rows(VIEW / 'nodes.csv')
original_by_node = {(int(row['index']), int(row['node_id'])): row for row in original_nodes}
archive_plans = [archive(BASE / 'model', model['arrays'], ['coordinates', 'connectivity', 'edofs', 'hessian', 'weights', 'kr', 'thickness'])]
selected_states = []
state_inventory = []
topology = []
raw_paths = [BASE / 'model/model.json', BASE / 'model/model.npz', BASE / 'result.json',
    S1 / 'protocol.json', S1 / 'run_001/cells.csv', S1 / 'run_001/occurrences.csv', S1 / 'run_001/nodes.csv',
    S1 / 'run_001/groups.csv', S1 / 'run_001/whole_material_comparison.csv', S1 / 'run_001/execution_receipt.json',
    M2 / 'protocol.json', M2 / 'run_001/all_nodes.csv', M2 / 'run_001/category_loads.csv', M2 / 'run_001/execution_receipt.json',
    VIEW / 'nodes.csv', REF / 'summary.json']
for index in (6, 13):
    state_file = BASE / 'accepted' / f'{index:03d}' / 'state.json'
    state = read(state_file)
    selected = dict(index=index, original_target_index=state['original_target_index'], leg=state['leg'],
        d_mm=state['d'], state_sha256=state['state_sha256'])
    assert selected == next(item for item in s1_protocol['selected_states'] if item['index'] == index)
    assert state['state_sha256'] == state['assembler_state_sha256']
    listed = result['states'][index]
    assert listed['descriptor_file_sha256'] == sha(ROOT / state_file)
    selected_states.append(selected)
    plan = archive(BASE, state['forces'], ['Hu', 'J', 'element_regularization_force', 'global_regularization_force'])
    archive_plans.append(plan)
    saved_reference_file = REF / f'accepted_{index:03d}/summary.json'
    reference = read(saved_reference_file)
    assert reference['status'] == 'pass' and reference['state_sha256'] == selected['state_sha256']
    assert reference['target_mm'] == selected['d_mm'] and reference['original_target_index'] == index and reference['leg'] == 'loading'
    assert reference['HP_calls'] == 2 and reference['elements_compared'] == 13440 and reference['global_DOFs_compared'] == 27378
    assert all(value['pass_gate'] for value in reference['force_checks'].values())
    state_inventory.append(dict(identity=selected, state_descriptor=identity(state_file),
        archive_descriptor=plan, force_kernel_version=state['force_kernel_version'], response_mode=state['response_mode'],
        Hu_and_J_saved_but_no_Hu_hi_Hu_lo_J_hi_J_lo_saved=True,
        original_saved_force_and_reference_snapshot=dict(path=saved_reference_file.as_posix(), status=reference['status'],
            force_checks=reference['force_checks'], local_force_worst=reference['local_force_worst'],
            workpiece_checks_descriptor=reference['workpiece_checks'])))
    selected_cells = [row for row in support_cells if int(row['index']) == index]
    selected_nodes = [row for row in ledger_nodes if int(row['index']) == index]
    assert len(selected_cells) == 722 and len(selected_nodes) == 703
    assert {int(row['node_id']) for row in selected_nodes} == node_ids
    occurrence_counts = Counter()
    corner_only = []
    for row in selected_cells:
        assert record_identity(row) == selected
        conn = json.loads(row['node_ids'])
        local = json.loads(row['selected_local_indices'])
        body_nodes = json.loads(row['selected_body_node_ids'])
        assert local == [a for a, node in enumerate(conn) if node in node_ids]
        assert body_nodes == [conn[a] for a in local]
        assert len(local) == int(row['selected_local_node_count'])
        occurrence_counts.update(body_nodes)
        if row['group'] == 'corner_only':
            corner_only.append(row)
    assert set(occurrence_counts) == node_ids and max(occurrence_counts.values()) == 4
    assert sum(occurrence_counts.values()) == 2738
    assert Counter(row['group'] for row in selected_cells) == dict(body=648, bottom_owner=36, left_owner=18, right_owner=18, corner_only=2)
    for row in selected_nodes:
        assert record_identity(row) == selected
        original = original_by_node[(index, int(row['node_id']))]
        assert all(row[key] == value for key, value in original.items())
    topology.append(dict(identity=selected, support_cells=722, body_nodes=703, local_body_occurrences=2738,
        max_contributing_cells_per_body_node=4, five_support_counts=dict(Counter(row['group'] for row in selected_cells)),
        S1_original_topology_consistent_with_model_JSON_body_ids=True,
        M2_six_force_texts_and_identity_coordinates_match_original_view_CSV_exactly=True,
        corner_only_original_rows=corner_only,
        original_body_force_summary=state['workpiece']))
    raw_paths += [state_file, BASE / state['forces']['path'], saved_reference_file]

source_paths = {
    'hf_repo/src/hf_eval/tmc_kernel.py': 'q1_operators lines47-66: mixed Hessian signs plus minus plus minus; both XY/YX; weights include area and thickness',
    'hf_repo/src/hf_eval/compensated_invariants.py': 'kinematics_pairs lines423-455 and hessian_action_pair lines458-471',
    'hf_repo/src/hf_eval/split_kernel_invariants_hu.py': '_response lines176-180,201-212: original DD scale and Hessian action, rounded at output separately from total',
    'hf_repo/src/hf_eval/native_mean.py': 'capture lines178-205: same accepted-state fields, rounded elemental regularization and global measured regularization persisted',
    'hf_repo/src/hf_eval/split_displacement.py': 'measure lines200-201: original C-order global component bincount',
    'hf_repo/src/hf_eval/saved_workpiece_loads.py': 'original nodal closure8eps original node L1; no total=material+Hu gate',
    'hf_repo/src/hf_eval/saved_material_support.py': 'original material full-global exact replay and selected-local elemental-L18eps regrouping; material-only scope',
    'hf_repo/src/hf_eval/workpiece_nodal.py': 'ON-body sign negative global internal, thickness already included',
}
raw_paths += [Path(path) for path in source_paths]
bindings = {path.as_posix(): identity(path) for path in raw_paths}
for path, value in bindings.items():
    for old_protocol in (s1_protocol, m2_protocol):
        if path in old_protocol.get('bindings', {}):
            assert value['sha256'] == old_protocol['bindings'][path]
minimum_plans = [dict(path=plan['path'], path_base=plan['path_base'], declared_archive_sha256=plan['declared_archive_sha256'],
    selected_fields={'element_regularization_force':plan['selected_fields']['element_regularization_force']},
    array_fields_decoded=False) for plan in archive_plans[1:]]
publication_path = Path('D:/hf-native-workpiece-api-author-20261009/MVOLUME1_execution_review_001/publication_receipt.json')
publication = json.loads(publication_path.read_bytes())
assert publication['published_commit'] == head and publication['execution_closed']

report = dict(schema_version='saved-Hu-boundary-input-inventory-1.0',
    status='read_only_input_inventory_ready_candidate_scope_pending', created_UTC=datetime.now(timezone.utc).isoformat(),
    inspected_HEAD=head, repo_root=str(ROOT), selected_states=selected_states,
    available_archive_plans=archive_plans, available_original_model_metadata=dict(grid=model['grid'], element_node_order=model['element_node_order'],
        dof_order=model['dof_order'], quadrature=model['quadrature'], material=model['material'],
        body_cells_from_bound_JSON=body['cells'], body_nodes_from_bound_JSON=body['nodes']),
    saved_state_and_reference_inventory=state_inventory,
    minimal_pattern_only_archive_plan=minimum_plans,
    minimal_pattern_only_proposed_scope=dict(existing_archives=2, selected_fields=2,
        original_element_regularization_force_only=True,
        ordinary_topology_and_force_sources=[(S1/'run_001/cells.csv').as_posix(), (M2/'run_001/all_nodes.csv').as_posix()],
        no_model_NPZ_needed_if_only_closed_S1_support_topology_is_used=True,
        no_new_Hu_J_hessian_weights_kr_decode=True,
        scope_not_yet_chosen_by_root=True,
        caveat='This is a possible minimum for a saved local-force pattern/generalized-action observer. New full-global replay or constitutive hyperstress reconstruction is a different scope.'),
    alternative_inputs=dict(full_original_global_component_replay='Would additionally need model edofs/connectivity and global_regularization_force each state; original C-order exact numeric comparison can then be declared. Do not silently widen the minimum scope.',
        closed_body_only_replay='S1 contains all722 cells touching all703 body nodes. Preserving increasing original cellID and localDOF order permits selected-body original bincount comparison to M2 saved node force text, without decoding full global_regularization_force. Only body-node agreement could be claimed.',
        saved_rounded_Hu_J_reconstruction='hessian/weights/kr plus Hu/J are actually available but reconstructing exp(-5J) from once-rounded fields is new constitutive arithmetic and cannot claim original DD scale/Hu replay or a unique boundary density.'),
    algebraic_source_facts=dict(
        original_hessian='For a=(BL,BR,TR,TL), hessian[a,XY]=hessian[a,YX]=s_a/(hx*hy), s=(+1,-1,+1,-1); XX/YY zero.',
        original_regularization='r_Hu[a,i] = DD(scale * sum_JK(Hu[i,J,K] * hessian[a,J,K])), scale=DD(kr * sum_q(weights[q] * exp(-5*J[q]))), output once-rounded.',
        expected_four_corner_pattern='In the original Q1 real/compensated algebra, r_Hu[a,i]=s_a*A_i, A_i=scale*(Hu_iXY+Hu_iYX)/(hx*hy). Pattern validity in the saved array has not been checked by this preparation and requires the eventual authorized observer.',
        recoverable_from_saved_force='If original saved four-corner numeric pattern holds, its amplitude can be represented by original BL force, with signs(+,-,+,-). This is a representation of already rounded local weak force; avoid averaging/repairing a failed pattern or reassigning it as point contact pressure.',
        missing_information='Local Q1 forces identify only this integrated mixed-Hessian action. They cannot recover nine-point exp-weighted hyperstress, original DD low words, strong-form Div/Hu derivatives, unique edge density or a continuous traction field.',
        units='Saved elemental/global forces alreadyN and include thickness20mm once. Any derived effective mixed-action coefficient must state its own definition/units and remains a descriptive force-based recovery.',
        scalar_body_projection='Edge-owner TR/TL and paired side selections cancel an ideal(+,-,+,-) pattern; corner-only one-node selections can survive. This is a source-algebra expectation, not a new computed observation.',
        total_component_distinction='Original total residual is DD sum before independent output rounding and total global scatter. Do not impose exact total=rounded material+rounded regularization identity; retain all three original component texts.'),
    ordinary_reusable_records=dict(
        S1_cells=bindings[(S1/'run_001/cells.csv').as_posix()],
        S1_occurrences=bindings[(S1/'run_001/occurrences.csv').as_posix()],
        S1_nodes=bindings[(S1/'run_001/nodes.csv').as_posix()],
        M2_all_nodes=bindings[(M2/'run_001/all_nodes.csv').as_posix()],
        M2_categories=bindings[(M2/'run_001/category_loads.csv').as_posix()],
        original_view_nodes=bindings[(VIEW/'nodes.csv').as_posix()],
        meaning='S1 CSVs carry material forces only; reuse their frozen topology but cannot obtain Hu amplitude from them. M2/all_nodes carries original total/material/regularization force strings and coordinates for all24states; selected6/13 give1406 nodal rows and14 category rows. Do not recompute or relabel prior categories as continuous traction.',
        support_and_node_identity_checks=topology),
    existing_qualification=dict(reference_summary=bindings[(REF/'summary.json').as_posix()],
        actual_status=ref['status'], accepted_states=ref['accepted_states'], HP_calls_started=ref['HP_calls_started'], HP_calls_completed=ref['HP_calls_completed'],
        full_element_and_DOF_coverage=ref['full_element_and_DOF_coverage'], gates=ref['gates'],
        reference_scope=ref['reference_scope'], qualification=ref['qualification'],
        HP_matrix_columns_exhaustively_checked=ref['HP_matrix_columns_exhaustively_checked'],
        contact_qualified=ref['contact_qualified'], clamp_qualified=ref['clamp_qualified'], pressure_qualified=ref['pressure_qualified'], HF5_qualified=ref['HF5_qualified'],
        implication='Original total/material/Hu local/global forces and signed workpiece projections are not a new qualification gap. A new boundary/generalized-action decomposition must state which additional physical/functional evidence it adds and retain existing force gates.'),
    existing_gate_boundaries=dict(
        M2_node_closure=m2_protocol['original_group_roundoff_rule'],
        S1_material_replay=s1_protocol['projection_rules']['global_replay'],
        S1_material_regrouping=s1_protocol['projection_rules']['regrouping'],
        nontransfer='S1 applies material-only. Reusing its arithmetic envelope for new Hu occurrence regrouping requires explicit stage contract based on exactly the same bounded topology/operation count; cannot silently broaden qualification. Existing nodalL1 gate does not bound cancellation-heavy elemental rearrangement.',
        no_extra_force_reference='Do not run new HP merely to duplicate existing24state local/global/body-force checks.'),
    raw_bindings=bindings,
    source_evidence={path:dict(reference=reference, **bindings[path]) for path,reference in source_paths.items()},
    prior_publication_receipt=dict(path=str(publication_path), sha256=sha(publication_path), original_record=publication),
    preparation_actions=dict(ordinary_source_JSON_CSV_read=True, NPZ_ZIP_directory_metadata_opened=3,
        NPY_headers_or_payload_read=0, NPZ_fields_decoded=0, candidate_HF_NumPy_imports=0,
        new_scientific_force_sums_fsum_integrals=0, kernel_tangent_HP_equilibrium_calls=0, plots=0,
        repo_mutations=0, new_external_report_only=True),
)
target = OUT/'input_scope.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
print(json.dumps(dict(status=report['status'], path=str(target), sha256=sha(target),
    available_archives=len(archive_plans), minimum_archives=2, minimum_fields=2, pending='Root final candidate scope'), ensure_ascii=False))
