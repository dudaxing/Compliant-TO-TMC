"""Read ordinary preparation/source metadata and bytes; never open payloads."""
from hashlib import sha256
import json
from pathlib import Path

A = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
def read(path):
    return json.loads(Path(path).read_bytes())
def identity(path):
    raw = Path(path).read_bytes()
    return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
binding = read(A/'SOURCE_BINDING.json')
ordinary = []
for item in binding['ordinary_files']:
    actual = identity(item['path'])
    ordinary.append(dict(path=item['path'], passed=actual == {k:item[k] for k in ('bytes','sha256')}))
production = read(A/'PRODUCTION_IDENTITY.json')
source = []
for item in production['files']:
    actual = identity(ROOT/item['path'])
    source.append(dict(path=item['path'], passed=actual == {k:item[k] for k in ('bytes','sha256')}))
observer = read(A/'observer_binding.json')
gates = read(A/'COMPARISON_GATES.json')
parent = read(binding['parent_binding']['result_path'])
probe = read(binding['reference_binding']['result_path'])
model = read(binding['parent_binding']['model_path'])
selected = parent['states'][2]
refrows = probe['accepted_steps']
physics = binding['physics']
payload_stats = []
for item in binding['scientific_payloads_stat_only']:
    path = Path(item['path'])
    payload_stats.append(dict(path=str(path), exists=path.is_file(),
        bytes=path.stat().st_size if path.is_file() else None,
        previous_declared_stat_bytes=item['observed_bytes'],
        payload_read=False,payload_hash_verified=False))
qa = read(A/'SCHEMATIC_QA.json')
checks = dict(
    ordinary_files_exact=len(ordinary) == 8 and all(v['passed'] for v in ordinary),
    all_57_production_bytes_unchanged=len(source) == 57 and all(v['passed'] for v in source),
    correct_complete_fixed_parent=parent['status'] == 'success'
        and parent['path_completed'] is True and parent['loading_peak_reached'] is True
        and parent['targets_mm'] == [0.,.25,.50] and len(parent['states']) == 3
        and selected['is_original_target'] is True and selected['original_target_index'] == 2,
    selected_parent_reference_identity=selected['state_sha256'] == refrows[0]['state_sha256']
        == binding['parent_binding']['selected_state_sha256']
        and selected['R_input'] == refrows[0]['R_input_N'] == binding['parent_binding']['R_input_N'],
    absolute_positive_loads_from_original_probe=gates['task']['P_targets_half_N']
        == [r['Q_drive_half_N'] for r in refrows]
        and refrows[0]['Q_drive_half_N'] == -selected['workpiece']['force_on_lower_body_N']['total'][0],
    observer_only_ids_rebound_to_current_low_parent=observer['held_input_mean_mm'] == .5
        and observer['source_parent_result_sha256'] == binding['parent_binding']['result_file_sha256']
        and observer['historical_source_fields_not_authoritative']['held_input_mean_mm'] == 1.06
        and observer['body_cells'] == physics['body_cells'] and observer['body_nodes'] == physics['body_nodes']
        and len(observer['right_medium_cells']) == 480 and len(observer['right_boundary_nodes']) == 81,
    reference_split_declarations_only=all(item['payload_read'] is False
        and item['payload_hash_verified_this_stage'] is False for item in binding['scientific_payloads_stat_only']),
    future_7_paths_6_decodes_14_fields=binding['future_read_set_proposal']['total_unique_NPZ_with_comparison'] == 7
        and binding['future_read_set_proposal']['total_decoded_field_count'] == 14
        and binding['future_read_set_proposal']['API']['old_NPZ_decoded'] == 2
        and binding['future_read_set_proposal']['comparison']['NPZ_unique'] == 4,
    source_mode_and_predictor_distinguished=binding['parent_binding']['response_mode'] == 'mechanical'
        and binding['parent_binding']['tangent_execution']['mode'] == 'chunk256'
        and binding['parent_binding']['historical_parent_initial_guess'] == 'port_projection'
        and binding['parent_binding']['new_force_initial_guess'] == 'guided_reduced_tangent',
    gates_predeclared_and_independent=gates['endpoint_engineering_regression']['q_abs_error_bound_mm'] == 1e-6
        and gates['endpoint_engineering_regression']['full_field_max_DOF_physical_displacement_error_bound_mm'] == 1e-6
        and gates['per_accepted_state_gates']['free_relative_residual_max'] == 1e-9
        and gates['per_accepted_state_gates']['generalized_relative_residual_max'] == 1e-9,
    no_new_science_in_preparation=read(A/'PREPARATION_STATE.json')['scientific_calls'] == 0
        and read(A/'PREPARATION_STATE.json')['new_r9_force_path_executed'] is False)
result = dict(stage='L-CTIPFREALPREP1',reviewer='/root/fload_tests',checks=checks,
    ordinary_identity_checks=ordinary,production_identity_checks=source,
    old_payload_stats_only=payload_stats,source_payload_reads_or_hashes=0,
    review_science_imports_tests_or_pixel_checks=0,
    document_identities={name:identity(A/name) for name in
      ('PREPARATION.md','L-CTIPFREAL1_CARD.md','SOURCE_BINDING.md','SOURCE_BINDING.json',
       'COMPARISON_GATES.md','COMPARISON_GATES.json','observer_binding.json','PRODUCTION_IDENTITY.json',
       'PREPARATION_STATE.json','control_schematic.png','control_schematic.svg','SCHEMATIC_QA.json')},
    schematic_QA_original_record=qa)
(A/'PREPARATION_REVIEW_AUDIT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'ordinary':len(ordinary),'production':len(source),'checks_passed':sum(checks.values()),
    'checks_total':len(checks),'failed':[k for k,v in checks.items() if not v],
    'payloads_statted_without_reads':len(payload_stats),'gates_scientific_worker_seconds':gates['proposed_resource_contract'].get('optional_scientific_process_deadline_seconds')}))
