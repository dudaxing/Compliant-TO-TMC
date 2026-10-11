"""Finalize metadata-only M-BOUND1 input scope; never decode NPZ or compute forces."""
from collections import Counter
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT = Path(__file__).resolve().parent
BASE = Path('lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square')
S1 = Path('lf_data_preparation/native_interface_001/nested_material_support_001')
M2 = Path('lf_data_preparation/native_interface_001/nested_ledger_002')
FORCE_COLUMNS = [part + '_F' + axis + '_N' for part in ('total', 'material', 'regularization') for axis in ('x', 'y')]
IDENTITY_COLUMNS = ('index', 'original_target_index', 'leg', 'd_mm', 'state_sha256')


def sha(path):
    value = sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def binding(relative):
    path = ROOT / relative
    return dict(path=relative.as_posix(), bytes=path.stat().st_size, sha256=sha(path))


def read(relative):
    return json.loads((ROOT / relative).read_bytes())


def csv_records(relative):
    with (ROOT / relative).open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def record_identity(row):
    return dict(index=int(row['index']), original_target_index=int(row['original_target_index']),
                leg=row['leg'], d_mm=float(row['d_mm']), state_sha256=row['state_sha256'])


inventory_path = OUT / 'input_scope.json'
inventory_sha_before = sha(inventory_path)
inventory = json.loads(inventory_path.read_bytes())
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == inventory['inspected_HEAD'] == '0d83b18b2bb320f137b1c4c3295805dc7c15aa65'
model, result = read(BASE / 'model/model.json'), read(BASE / 'result.json')
grid = model['grid']
assert grid['shape_yx'] == [80, 168]
assert grid['axes'] == [[1., 0.], [0., 1.]]
assert grid['cell_size_mm'] == [.5, .5] and grid['origin_mm'] == [0., 0.]
ny, nx = grid['shape_yx']
dx, dy = grid['cell_size_mm']
x0, y0 = grid['origin_mm']
body = model['region_metadata']['workpiece']
body_nodes = set(body['nodes'])
body_cells = set(body['cells'])
assert len(body_nodes) == 703 and len(body_cells) == 648
assert body['nodes'] == sorted(body_nodes) and body['cells'] == sorted(body_cells)


def coordinate(node):
    iy, ix = divmod(node, nx + 1)
    assert 0 <= iy <= ny and 0 <= ix <= nx
    return [x0 + ix * dx, y0 + iy * dy]


def connectivity(cell):
    iy, ix = divmod(cell, nx)
    assert 0 <= iy < ny and 0 <= ix < nx
    bl = iy * (nx + 1) + ix
    return [bl, bl + 1, bl + nx + 2, bl + nx + 1]


cells_relative = S1 / 'run_001/cells.csv'
nodes_relative = M2 / 'run_001/all_nodes.csv'
categories_relative = M2 / 'run_001/category_loads.csv'
cell_columns, cells = csv_records(cells_relative)
node_columns, nodes = csv_records(nodes_relative)
category_columns, categories = csv_records(categories_relative)
assert len(cells) == 1444 and len(nodes) == 16872 and len(categories) == 168
runtime_paths = [BASE / 'model/model.json', BASE / 'result.json', cells_relative, nodes_relative, categories_relative]
archive_plan, selected_states, topology, endpoints, whole_saved = [], [], [], [], []
category_saved_records = []
for index in (6, 13):
    state_relative = BASE / 'accepted' / f'{index:03d}' / 'state.json'
    state = read(state_relative)
    selected = dict(index=index, original_target_index=state['original_target_index'], leg=state['leg'],
                    d_mm=state['d'], state_sha256=state['state_sha256'])
    assert selected == next(row for row in inventory['selected_states'] if row['index'] == index)
    assert state['assembler_state_sha256'] == state['state_sha256']
    listed = result['states'][index]
    assert listed['descriptor_file_sha256'] == sha(ROOT / state_relative)
    archive_relative = BASE / state['forces']['path']
    archive_binding = binding(archive_relative)
    assert archive_binding['sha256'] == state['forces']['sha256']
    old_plan = next(plan for plan in inventory['available_archive_plans'] if plan['path'] == archive_relative.as_posix())
    assert old_plan['actual_archive_sha256'] == archive_binding['sha256']
    descriptor = state['forces']['fields']['element_regularization_force']
    assert descriptor == old_plan['selected_fields']['element_regularization_force']
    assert descriptor['dtype'] == 'float64' and descriptor['shape'] == [13440, 8]
    archive_plan.append(dict(index=index, state_sha256=state['state_sha256'], path=archive_relative.as_posix(),
        path_base=BASE.as_posix(), declared_archive_sha256=state['forces']['sha256'], actual_archive_sha256=archive_binding['sha256'],
        selected_fields={'element_regularization_force': descriptor},
        selected_ZIP_directory_metadata={'element_regularization_force': old_plan['selected_ZIP_directory_metadata']['element_regularization_force']},
        field_dtype_shape_SHA_are_saved_descriptor_declarations=True, array_fields_decoded=False,
        field_byte_identity_pending_authorized_runtime_decode=True,
        original_state_file=state_relative.as_posix(), original_state_descriptor_sha256=state['descriptor_sha256']))
    selected_states.append(selected)
    runtime_paths += [state_relative, archive_relative]
    selected_cells = [row for row in cells if int(row['index']) == index]
    selected_nodes = [row for row in nodes if int(row['index']) == index]
    selected_categories = [row for row in categories if int(row['index']) == index]
    assert len(selected_cells) == 722 and len(selected_nodes) == 703 and len(selected_categories) == 7
    assert all(record_identity(row) == selected for row in selected_cells + selected_nodes + selected_categories)
    cell_ids = [int(row['cell_id']) for row in selected_cells]
    node_ids = [int(row['node_id']) for row in selected_nodes]
    assert cell_ids == sorted(set(cell_ids)) and node_ids == sorted(body_nodes)
    assert Counter(row['group'] for row in selected_cells) == dict(body=648, bottom_owner=36, left_owner=18, right_owner=18, corner_only=2)
    assert {int(row['cell_id']) for row in selected_cells if row['group'] == 'body'} == body_cells
    selected_node_rows = {int(row['node_id']): row for row in selected_nodes}
    occurrence_counts = Counter()
    for row in selected_cells:
        cell = int(row['cell_id'])
        conn = json.loads(row['node_ids'])
        local = json.loads(row['selected_local_indices'])
        saved_body_nodes = json.loads(row['selected_body_node_ids'])
        assert conn == connectivity(cell)
        assert local == [a for a, node in enumerate(conn) if node in body_nodes]
        assert saved_body_nodes == [conn[a] for a in local]
        assert int(row['selected_local_node_count']) == len(local)
        occurrence_counts.update(saved_body_nodes)
    assert len(occurrence_counts) == 703 and max(occurrence_counts.values()) == 4
    assert sum(occurrence_counts.values()) == 2738
    for row in selected_nodes:
        assert [float(row['x_mm']), float(row['y_mm'])] == coordinate(int(row['node_id']))
        assert all(isinstance(row[key], str) for key in FORCE_COLUMNS)
    original_corner_cells = [int(row['cell_id']) for row in selected_cells if row['group'] == 'corner_only']
    assert original_corner_cells == [10371, 10408]
    lookup = {int(row['cell_id']): row for row in selected_cells}
    cell_examples = []
    for cell, expected_group, expected_mask in ((10371, 'corner_only', [False, False, True, False]),
            (10407, 'bottom_owner', [False, False, True, True]),
            (10408, 'corner_only', [False, False, False, True])):
        row = lookup[cell]
        conn = connectivity(cell)
        mask = [node in body_nodes for node in conn]
        assert row['group'] == expected_group and mask == expected_mask
        coordinates = [coordinate(node) for node in conn]
        original_body_coordinate_text = {}
        for local, node in enumerate(conn):
            coordinate_text = None
            if mask[local]:
                saved_row = selected_node_rows[node]
                coordinate_text = {'x_mm': saved_row['x_mm'], 'y_mm': saved_row['y_mm']}
                assert [float(coordinate_text['x_mm']), float(coordinate_text['y_mm'])] == coordinates[local]
                original_body_coordinate_text[str(node)] = coordinate_text
            endpoints.append(dict(**selected, cell_id=cell, local_node=local,
                local_name=('BL', 'BR', 'TR', 'TL')[local], node_id=node, reference_coordinates_mm=coordinates[local],
                is_body_node=mask[local], original_body_coordinate_text=coordinate_text,
                source_group=expected_group))
        cell_examples.append(dict(cell_id=cell, group=row['group'], node_ids=conn,
            reference_coordinates_mm=coordinates, body_mask=mask,
            selected_local_indices=json.loads(row['selected_local_indices']),
            selected_body_node_ids=json.loads(row['selected_body_node_ids']),
            original_body_coordinate_text=original_body_coordinate_text,
            original_S1_row=row))
    topology.append(dict(identity=selected, support_cells=722, body_nodes=703, body_DOFs=1406,
        original_support_cell_order='strictly increasing original cell_id',
        original_selected_body_node_order='strictly increasing original node_id',
        local_order='BL BR TR TL', component_order='x y',
        source_mask_and_model_membership_exact=True, grid_connectivity_and_CSV_coordinates_exact=True,
        selected_body_occurrences=2738, max_occurrences_per_body_node=4,
        support_group_counts=dict(Counter(row['group'] for row in selected_cells)),
        original_corner_only_cell_ids=original_corner_cells, endpoint_cell_examples=cell_examples,
        selected_node_force_texts_parsed_or_summed=False))
    whole_saved.append(dict(identity=selected, original_force_on_lower_body_N=state['workpiece']['force_on_lower_body_N'],
        original_regularization_on_body_N=state['workpiece']['force_on_lower_body_N']['regularization'],
        source_pointer='/workpiece/force_on_lower_body_N/regularization', computed=False))
    category_saved_records += selected_categories

assert len(endpoints) == 24 and len(category_saved_records) == 14
runtime_bindings = {path.as_posix(): binding(path) for path in runtime_paths}
assert len(runtime_bindings) == 9
for relative, value in runtime_bindings.items():
    assert value['sha256'] == inventory['raw_bindings'][relative]['sha256']
source_bindings = {}
for relative, old in inventory['source_evidence'].items():
    actual = binding(Path(relative))
    assert actual['sha256'] == old['sha256']
    source_bindings[relative] = dict(**actual, reference=old['reference'])
regions_relative = Path('hf_repo/src/hf_eval/regions.py')
source_bindings[regions_relative.as_posix()] = dict(**binding(regions_relative),
    reference='node_coordinates and element_connectivity: canonical C-order grid index mapping; source-only geometry metadata verification')
assert source_bindings[regions_relative.as_posix()]['sha256'] == '38d5a08b7c91a0212b28e5856046f3126543eb8d090bb5c30fe072839411d568'
prior = inventory['prior_publication_receipt']
assert sha(Path(prior['path'])) == prior['sha256']
assert prior['original_record']['published_commit'] == head and prior['original_record']['execution_closed']

report = dict(schema_version='saved-Hu-boundary-final-input-scope-1.0',
    status='pass_read_only_final_runtime_input_scope_prepared_not_executed',
    created_UTC=datetime.now(timezone.utc).isoformat(), inspected_HEAD=head, repo_root=str(ROOT),
    prior_inventory=dict(path=str(inventory_path), sha256=inventory_sha_before, preserved=True),
    selected_states=selected_states, selected_archive_plan=archive_plan, runtime_files=runtime_bindings,
    runtime_file_counts=dict(total=9, JSON=4, CSV=3, NPZ=2, selected_NPZ_fields=2),
    ordinary_runtime_record_contract=dict(
        model_JSON='/grid plus /region_metadata/workpiece/nodes and cells; canonical integer body identities',
        result_JSON='two original state entries and original descriptor-file SHA linkage',
        accepted_state_JSON='same accepted-state SHA, assembler-state SHA, force archive/field descriptors and whole original regularization force',
        S1_cells=dict(path=cells_relative.as_posix(), all_rows=1444, selected_rows=1444,
            per_state_rows=722, original_columns=cell_columns,
            used_columns=list(IDENTITY_COLUMNS)+['cell_id','group','selected_local_node_count','node_ids','selected_local_indices','selected_body_node_ids'],
            material_force_columns_read_as_ordinary_text_but_not_numeric_input=True,
            full_four_node_ids_and_selected_local_order_preserved=True),
        M2_nodes=dict(path=nodes_relative.as_posix(), all_rows=16872, selected_rows=1406, per_state_rows=703,
            original_columns=node_columns, original_six_force_text_columns=FORCE_COLUMNS,
            whole_original_selected_row_text_preserved=True, existing_category_text_preserved=True,
            original_view_text_identity_is_inherited_inventory_evidence=True,
            no_original_view_or_nodal_NPZ_runtime_read=True),
        M2_categories=dict(path=categories_relative.as_posix(), all_rows=168, selected_rows=14,
            per_state_rows=7, original_columns=category_columns, original_selected_text_records=category_saved_records,
            force_text_preserved_without_recomputation=True)),
    closed_topology_metadata_checks=topology, original_state_whole_force_records=whole_saved,
    endpoint_geometry_metadata_records=endpoints,
    new_runtime_operation_contract=dict(
        body_replay='Read each saved element_regularization_force only; process all722 original touching cells per state in increasing original cell_id, local BL BR TR TL, component x y (original C order); scatter selected entries only to original703 body nodes/1406 body DOFs.',
        node_force_sign='M2 stores signed ON-body force: compare the negative selected body internal Hu scatter to original regularization_Fx_N and regularization_Fy_N parsed from M2.',
        body_node_comparison='Numeric array_equal after exact preserved selected-entry order; signed-zero equality follows numeric comparison. This is body-node equality only, not full-domain replay, raw bytes or original DD-kernel replay.',
        original_node_whole_closure='math.fsum of original M2 Hu-node forces versus same accepted state whole Hu force; retain old 8*2^-52*fsum(abs(original selected node force)) per state/axis, without absolute floor.',
        new_owner_regroup_closure='math.fsum regrouped owner/body/corner Hu projections versus body-node whole; 8*2^-52*fsum(abs(original selected local Hu elemental terms)) per state/axis, without absolute floor. This new local-term L1 gate does not replace the old nodal L1 gate.',
        pattern_gate='Each selected support cell and each component must have exact numeric original(+,-,+,-) corner pattern. Use original BL amplitude only after gate; no averaging, repair, clipping or reconstructed Hu/J scale.',
        side_pair_gate='Every two-selected-node bottom_owner/left_owner/right_owner projection must cancel under the exact pattern; body cells four nodes also cancel. These structural checks remain pending authorized decode.',
        corner_remainder='Only original10371 and10408 corner_only cells retain one selected body node. Preserve their original selected signed force without allocating it as continuous edge traction.',
        total_force='Retain original six M2 force strings and14 category records; do not impose exact total=independently rounded material+regularization.',
        outputs=dict(cells=1444, groups=10, whole=2, nodes=1406, endpoints=24, original_nodecategory_rows=14, PNG=2, new_public_API_calls=2),
        endpoint_cells_each_state=[10371,10407,10408],
        budget_and_launch_authorization='Not established by this metadata-only report; root candidate protocol/card must set them explicitly.'),
    source_provenance_pins=source_bindings,
    original_gates_from_inventory=inventory['existing_gate_boundaries'],
    existing_24_state_reference_qualification=inventory['existing_qualification'],
    physical_interpretation_limits=inventory['algebraic_source_facts'],
    prohibited_runtime_inputs=['model.npz', 'state displacement NPZ', 'global_regularization_force NPZ field',
        'Hu NPZ field', 'J NPZ field', 'hessian NPZ field', 'weights NPZ field', 'kr NPZ field',
        'M2 ledger.json', 'large S1 support.json', 'saved nodal NPZ'],
    prior_publication_receipt=prior,
    candidate_source_protocol_review='Candidate module/API/worker/protocol/card and future source publication pins are not yet reviewed by this input scope. This report binds original provenance and narrowed runtime inputs only.',
    contradictions=[],
    naming_clarification='Cell10407 is original bottom_owner, whose upper edge belongs to body y=31 over x=79.5..80. The generic side example must not be relabeled right_owner.',
    preparation_actions=dict(ordinary_source_JSON_CSV_read=True, raw_file_SHA_verified=True,
        geometry_divmod_and_integer_counts_only=True, new_ZIP_directory_reads=0,
        NPY_header_or_payload_reads=0, NPZ_fields_decoded=0, candidate_HF_NumPy_imports=0,
        scientific_force_sums_fsum_integrals=0, kernel_tangent_HP_equilibrium_calls=0, plots=0, repo_mutations=0),
)
assert sha(inventory_path) == inventory_sha_before
target = OUT / 'final_input_scope.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
print(json.dumps(dict(status=report['status'], path=str(target), sha256=sha(target),
    runtime_files=9, archives=2, fields=2, endpoint_rows=24, contradictions=0), ensure_ascii=False))
