"""One ordinary-JSON continuation check; standard library, no scientific reads."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import struct
import sys
from time import monotonic

BASE = Path(__file__).resolve().parent
RUN = BASE/'run_001'
STAGE = 'L-CTIPFSTEP1'


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(part) for key, part in value.items()}
    if isinstance(value, list):
        return [canonical(part) for part in value]
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError('Nonfinite ordinary metadata')
        return (0. if value == 0. else value).hex()
    return value


def canonical_hash(value):
    return sha256(json.dumps(canonical(value), sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def same_bits(a, b):
    return struct.pack('<d', a) == struct.pack('<d', b)


def finite(value):
    return type(value) in (int, float) and isfinite(value)


def main():
    started = monotonic()
    output = RUN/'continuation_check.json'
    if output.exists():
        print('Existing continuation check preserved', flush=True)
        return 1
    report = dict(schema_version=STAGE+'-ordinary-continuation-check-1.0', stage=STAGE,
        status='failed', ordinary_reads=[], checks=[], scientific_NPZ_reads=0,
        scientific_fields_decoded=0, HF_imports=0, new_force_or_tangent_calls=0,
        HP_calls=0, media_reads=0, result_modified=False, accepted_rows=[],
        reference_comparison=dict(status='not_available_no_P2_reference',
            q_error_mm=None, full_DOF_error_mm=None, R_error_N=None),
        scope='Ordinary source/segment identity and original scalar gates only; not new HP, full-field reference or contact/bearing qualification')

    def require(name, condition):
        report['checks'].append(dict(name=name, status='pass' if condition else 'failed'))
        if not condition:
            raise ValueError(name)

    def read_ordinary(path):
        raw = Path(path).read_bytes()
        report['ordinary_reads'].append(dict(path=Path(path).as_posix(), bytes=len(raw), sha256=sha256(raw).hexdigest()))
        return json.loads(raw)

    try:
        require('unique_no_argument_command', len(sys.argv) == 1)
        protocol = read_ordinary(BASE/'protocol.json')
        result = read_ordinary(RUN/'force/result.json')
        require('frozen_stage_and_base', protocol['stage'] == STAGE and Path(protocol['runtime_base']).resolve() == BASE)
        require('new_result_canonical_identity', canonical_hash({k:v for k,v in result.items()
            if k != 'descriptor_sha256'}) == result['descriptor_sha256'])
        context, selected = protocol['source_context'], protocol['source_selected']
        require('protocol_source_selected_consistency', context['selected_force_state'] == selected
            and context['selected_accepted_index'] == context['selected_original_index'] == 1)
        full, segment = protocol['loads_half_N'], protocol['segment_loads_half_N']
        P0, P1, P2 = full
        require('exact_prepared_full_and_segment_loads', full == [0.0002399800950672949,
            0.0002561572865437846, 0.000260201584412907] and segment == [P1, P2]
            and P2 == P1+(P1-P0)/4 and selected['P_target_half_N'] == P1)
        require('successful_known_complete_segment', result['schema_version'] == 'hf-native-guided-force-1.1'
            and result['status'] == 'success' and result['failure'] is None and result['target_reached'] is True)
        settings = dict(context['settings'])
        settings['time_limit_seconds'] = protocol['controller_seconds']
        nonclock = {k:v for k,v in settings.items() if k != 'time_limit_seconds'}
        require('source_physics_options_and_settings_inherit', result['source'] == context['root_fixed_source']
            and result['settings'] == settings and result['force_settings'] == context['force_settings']
            and result['response_mode'] == context['response_mode'] == 'mechanical'
            and result['tangent_mode'] == context['tangent_mode'] == 'chunk256'
            and result['initial_guess'] == context['initial_guess'] == 'guided_reduced_tangent'
            and result['parent_initial_guess'] == 'port_projection')
        task, continuation = result['force_task'], result['continuation']
        require('absolute_loads_held_mean_and_separate_root_scale', task['body_load_targets_half_N'] == full
            and task['held_input_mean_mm'] == 1.06 and task['known_q_target_supplied'] is False
            and task['anchor_target_half_N'] == task['force_scale_anchor_half_N'] == P0
            and task['segment_anchor_half_N'] == P1)
        parent_pin = next(pin for pin in context['ordinary_sources']
            if Path(pin['path']).resolve() == Path(protocol['parent_result']).resolve())
        require('direct_and_root_force_source_pins', continuation['parent_result']['path'] == Path(protocol['parent_result']).resolve().as_posix()
            and continuation['parent_result']['sha256'] == parent_pin['sha256']
            and continuation['parent_result']['descriptor_sha256'] == context['source_force_descriptor_sha256']
            and continuation['root_force_result'] == continuation['parent_result']
            and continuation['root_fixed_result_historical'] == context['root_fixed_source']['parent_result']
            and continuation['root_fixed_result']['sha256'] == context['root_fixed_source']['parent_result']['sha256'])
        require('complete_prefix_segment_and_inherited_metadata',
            continuation['source_body_load_targets_half_N'] == full[:2]
            and continuation['full_extended_body_load_targets_half_N'] == full
            and continuation['requested_segment_targets_half_N'] == segment
            and continuation['global_original_target_offset'] == 1
            and continuation['original_target_indices'] == [1, 2]
            and continuation['force_scale_anchor_half_N'] == P0 and continuation['segment_anchor_half_N'] == P1
            and continuation['inherited_settings_without_clock'] == nonclock
            and continuation['inherited_force_settings'] == context['force_settings']
            and continuation['root_force_ancestors_revalidated'] is False
            and continuation['full_extended_path_executed_by_child'] is False
            and continuation['saved_matrix_or_force_or_tangent_read'] is False
            and all(continuation[k] is True for k in
                ('fresh_anchor_required', 'anchor_revalidated', 'anchor_identity_preserved', 'segment_completed')))
        rows = result['accepted_steps']
        fresh, terminal = rows[0], rows[-1]
        pin = continuation['selected_state']
        require('selected_source_split_and_absolute_bits', pin['accepted_index'] == pin['original_target_index'] == 1
            and pin['state_sha256'] == selected['state_sha256']
            and pin['archive_sha256'] == selected['state']['sha256']
            and pin['state_fields'] == selected['state']['fields']
            and all(same_bits(pin[k], selected[k]) for k in ('P_target_half_N', 'body_q_mm', 'R_input_N')))
        require('fresh_check1_bitwise_split_identity', fresh['fresh_anchor'] is True
            and fresh['newton_checks'] == 1 and fresh['original_target_index'] == 1
            and fresh['segment_original_target_index'] == 0
            and fresh['state_sha256'] == selected['state_sha256']
            and fresh['state']['fields'] == selected['state']['fields']
            and all(same_bits(fresh[k], selected[k]) for k in ('P_target_half_N', 'body_q_mm', 'R_input_N')))
        originals = [row for row in rows if row['is_original_target'] is True]
        require('two_original_requests_and_actual_derived_count', [row['original_target_index'] for row in originals] == [1, 2]
            and [row['P_target_half_N'] for row in originals] == segment and 2 <= len(rows) <= 5)
        report['accepted_count_note'] = 'Maximum5 is derived from the unchanged Nmin/maxdepth rules; not a new controller gate or truncation. All actual rows are retained.'
        nmin = context['force_settings']['minimum_force_increment_half_N']
        require('original_Nmin_derived_halving_limit', (P2-P1)/4 >= nmin*(1-1e-12) and (P2-P1)/8 < nmin*(1-1e-12)
            and result['settings']['max_bisections'] == 4)
        previous = None
        for index, row in enumerate(rows):
            P = row['P_target_half_N']
            require('row_'+str(index)+'_target_index_and_finite_scalars', all(finite(row[k]) for k in
                ('P_target_half_N','body_q_mm','R_input_N','minimum_J','max_abs_Hu_per_mm',
                 'relative_residual','relative_generalized_force_residual','constraint_residual',
                 'constraint_bound','relative_global_force_balance','max_abs_prescribed_error_mm'))
                and (previous is None or P > previous) and P1 <= P <= P2
                and row['original_target_index'] in (1, 2)
                and row['segment_original_target_index'] == row['original_target_index']-1
                and row['original_target_force_half_N'] == full[row['original_target_index']]
                and (row['is_original_target'] is True or (row['original_target_index'] == 2 and P1 < P < P2))
                and row['load_increment_from_anchor_half_N'] == P-P1
                and row['load_increment_from_root_half_N'] == P-P0)
            scale = max(abs(P), abs(P0), 2.12e-7)
            require('row_'+str(index)+'_original_gates_and_body_scale',
                0 <= row['relative_residual'] <= settings['tolerance']
                and 0 <= row['relative_generalized_force_residual'] <= settings['tolerance']
                and row['constraint_bound'] == settings['constraint_tolerance']*max(1.06, settings['displacement_scale_floor'])
                and abs(row['constraint_residual']) <= row['constraint_bound']
                and row['minimum_J'] > 0 and row['max_abs_Hu_per_mm'] >= 0
                and 0 <= row['relative_global_force_balance'] <= 1e-6
                and 0 <= row['max_abs_prescribed_error_mm'] <= 8e-11
                and row['force_scale_floor_half_N'] == 2.12e-7
                and row['generalized_force_scale_half_N'] == scale
                and row['generalized_force_bound_half_N'] == settings['tolerance']*scale
                and 1 <= row['newton_checks'] <= settings['max_checks']
                and 0 <= row['bisection_depth'] <= settings['max_bisections'])
            require('row_'+str(index)+'_external_ledger_and_split_declarations',
                row['ledger']['body_axial_load_N'] == [P, 0.]
                and row['ledger']['body_x_prescribed_drive_included'] is False
                and row['ledger']['body_y_background_overlap_counted_once'] is True
                and set(row['state']['fields']) == {'lift', 'fluctuation'}
                and all(info['dtype'] == 'float64' and info['shape'] == [29970]
                    for info in row['state']['fields'].values()))
            names = ('P_target_half_N','body_q_mm','R_input_N','input_mean_mm','force_on_body_N','ledger',
                'relative_residual','relative_generalized_force_residual','constraint_residual','constraint_bound',
                'minimum_J','max_abs_Hu_per_mm','relative_global_force_balance','max_abs_prescribed_error_mm',
                'generalized_force_residual_half_N','generalized_force_scale_half_N','generalized_force_bound_half_N',
                'newton_checks','is_original_target','original_target_index','segment_original_target_index',
                'bisection_depth','state_sha256','fresh_anchor')
            report['accepted_rows'].append({key: row[key] for key in names})
            previous = P
        path = result['path_summary']
        require('P2_reached_without_replaying_old_prefix', terminal['P_target_half_N'] == P2
            and terminal['original_target_index'] == 2 and terminal['is_original_target'] is True
            and path['target_force_half_N'] == path['reached_force_half_N'] == P2
            and same_bits(path['reached_body_q_mm'], terminal['body_q_mm'])
            and path['last_path_state_sha256'] == terminal['state_sha256']
            and path['requested_segment_targets_half_N'] == segment
            and path['global_original_target_offset'] == 1
            and path['full_extended_path_executed_by_child'] is False)
        model = result['model']
        require('original_model_counts_and_body_membership', len(model['coordinates_mm']) == 14985
            and len(model['connectivity']) == 14720 and len(model['body_nodes']) == 565
            and model['body_nodes'] == model['region_metadata']['workpiece']['nodes']
            and len(model['region_metadata']['workpiece']['cells']) == 510)
        counts = result['call_counts']
        require('one_solver_no_HP_or_save_time_mechanics', counts['solver_invocations'] == 1
            and counts['HP_calls'] == counts['save_force_calls'] == counts['save_tangent_calls'] == 0)
        require('original_qualifications_remain_false', all(result[key] is False for key in
            ('independent_HP_qualified','effective_grasp_qualified','release_qualified','HF_qualified')))
        report.update(status='pass', numeric_path_status=result['status'], numeric_path_failure=result['failure'],
            target_reached=True, loads_half_N=full, requested_segment_half_N=segment,
            accepted_count=len(rows), original_request_count=2, internal_bisection_count=len(rows)-2,
            source_context=context, history=protocol['history'], call_counts=counts,
            path_summary=path, source_selected_identity=pin,
            descriptive_change_from_segment_anchor=dict(delta_P_half_N=P2-P1,
                delta_q_mm=terminal['body_q_mm']-fresh['body_q_mm'],
                delta_R_input_N=terminal['R_input_N']-fresh['R_input_N']),
            J_Hu_scope='Original production scalar records only; no scientific field arrays decoded or extrema re-localized',
            F_Hu_finite_scope='Enforced by the unchanged production controller; not independently decoded by this ordinary checker')
    except Exception as error:
        report['failure'] = dict(type=type(error).__name__, message=str(error))
    report['created_utc'] = datetime.now(timezone.utc).isoformat()
    report['elapsed_seconds'] = monotonic()-started
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=report['status'], checks=len(report['checks']), elapsed=report['elapsed_seconds'])), flush=True)
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
