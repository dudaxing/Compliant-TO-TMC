"""Write an ordinary JSON draft, without importing candidates or decoding arrays."""
from pathlib import Path
from hashlib import sha256
import json

EXT = Path(__file__).resolve().parent
scope = json.loads((EXT/'final_input_scope.json').read_bytes())
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
CASE = 'lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square'
plans = [dict(path=plan['path'],path_base=plan['path_base'],declared_archive_sha256=plan['declared_archive_sha256'],
    selected_fields=plan['selected_fields'],array_fields_decoded=False) for plan in scope['selected_archive_plan']]
protocol = dict(schema_version='saved-Q1-Hu-boundary-card-1.0',prepared=True,authorized=False,executed=False,
    baseline_main='0d83b18b2bb320f137b1c4c3295805dc7c15aa65',card=f'{REL}/M-BOUND1_CARD.md',
    model_file=f'{CASE}/model/model.json',result_file=f'{CASE}/result.json',
    state_files={str(i):f'{CASE}/accepted/{i:03d}/state.json' for i in (6,13)},
    material_support_cells_file='lf_data_preparation/native_interface_001/nested_material_support_001/run_001/cells.csv',
    ledger_nodes_file='lf_data_preparation/native_interface_001/nested_ledger_002/run_001/all_nodes.csv',
    ledger_categories_file='lf_data_preparation/native_interface_001/nested_ledger_002/run_001/category_loads.csv',
    selected_states=scope['selected_states'],selected_endpoint_cell_ids=[10371,10407,10408],
    actual_deformation_view='functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif',
    output_directory=f'{REL}/run_001',sampled_RSS_bytes=8589934592,
    phases=dict(hu_boundary=dict(helper_seconds=180,outer_seconds=240,argv=[f'{REL}/execute_saved_hu_boundary.py',
        '--repo','.','--protocol',f'{REL}/protocol.json','--time-limit','180'])),
    selected_archive_plan=plans,
    expected_counts=dict(cells_total=1444,group_rows_total=10,whole_rows_total=2,nodes_total=1406,
        selected_endpoint_rows_total=24,node_category_rows_total=14),
    expected_calls=dict(NPZ_read_started=2,NPZ_read_completed=2,selected_array_fields=2,
        hu_boundary_started=2,hu_boundary_completed=2,PNG_writes=2),
    expected_output_files=['hu_boundary.json','cells.csv','groups.csv','whole.csv','nodes.csv',
        'selected_endpoints.csv','node_categories.csv','Q1_Hu_endpoint_actions.png',
        'Hu_owner_node_comparison.png','execution_receipt.json'],
    observation_rules=dict(original_force='Original selected element_regularization_force eight values remain authoritative; exact Q1 numeric sign pattern',
        body_scatter='Only original 1406 body DOFs; ascending original cell/local/component order; internal bincount then negate; numeric array_equal with original nodes, not byte/signed-zero',
        old_whole='Original node-Hu to state-Hu: 8eps times original node-Hu L1, no floor',
        new_regrouping='Selected original local-Hu fsum to original node values and local whole to original-node whole: 8eps times corresponding selected original local-Hu L1, no floor',
        preserved_text='Original six node force strings and complete seven-category rows are copied, not reclassified or recomputed',
        comparisons='Five-role regrouping, two corner-only and original whole differences descriptive only; no equality or pressure gate',
        old_gates='Original M1/M2/SUPPORT/TRACE/VOLUME/HP criteria and force qualification unchanged'),
    qualification_scope='Two saved-state Q1 Hu discrete vertex/support interpretation and original body scatter only; no force-kernel/tangent/HP/equilibrium, reconstructed Hu/J, continuous total pressure, energy gradient or effective-grip qualification',
    prepared_scope='Source/AST/ordinary JSON CSV and raw byte SHA only; no candidate import, NPZ decode, new scientific fsum or render')
raw = (json.dumps(protocol,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
with (EXT/'protocol_draft.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps(dict(status='ordinary_protocol_draft_prepared_not_executed',sha256=sha256(raw).hexdigest())))
