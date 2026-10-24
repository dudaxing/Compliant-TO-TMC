"""Close FSTEP1 from existing ordinary metadata only, after launcher terminal.

Never read scientific NPZ/ZIP or image bytes.  Their identities are copied from
already written seal/renderer/root-QA receipts, not re-established here.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

AUTHOR = Path(__file__).resolve().parent
BASE = Path('D:/hfst1_001')
RUN = BASE/'run_001'
STAGE = 'L-CTIPFSTEP1'


def ordinary_identity(path):
    path = Path(path)
    if path.suffix.lower() not in ('.json', '.py', '.md', '.txt'):
        raise ValueError('Closure identity reads ordinary metadata/source only: '+str(path))
    raw = path.read_bytes()
    return raw, dict(path=path.as_posix(), bytes=len(raw), sha256=sha256(raw).hexdigest())


def main():
    output = AUTHOR/'EXECUTION_RESULT.json'
    if len(sys.argv) != 1 or output.exists():
        raise FileExistsError('One ordinary closure record; preserve existing output')
    identities = {}

    def read(role, path, required=False):
        path = Path(path)
        if not path.exists():
            if required:
                raise FileNotFoundError('Launcher must be terminal before closure: '+str(path))
            return None
        raw, pin = ordinary_identity(path)
        identities[role] = pin
        return json.loads(raw)

    protocol = read('protocol', BASE/'protocol.json', True)
    seal = read('seal', BASE/'seal_receipt.json', True)
    top = read('top_supervision', BASE/'top_supervision.json', True)
    if protocol['stage'] != STAGE or seal['stage'] != STAGE:
        raise ValueError('Wrong closure stage')

    def clean(row):
        proof = (row or {}).get('cleanup_proof', {})
        return ((row or {}).get('cleanup_verified') is True and proof.get('pass') is True
            and proof.get('job_handle_closed') is True
            and proof.get('final_accounting', {}).get('ActiveProcesses') == 0)

    # A timeout/typed partial may be a closed NOT_PASS.  Unproven process-tree
    # termination is not recorded as scientifically closed by this program.
    if not clean(top):
        raise RuntimeError('Complete helper-tree cleanup is unproven; do not claim scientific_window_closed')
    helper = read('helper_receipt', BASE/'helper_receipt.json')
    science = read('science_receipt', RUN/'science_receipt.json')
    force = read('force_result', RUN/'force/result.json')
    check = read('continuation_check', RUN/'continuation_check.json')
    renderer = read('renderer_receipt', RUN/'view/renderer_receipt.json')
    geometry = read('geometry_metrics', RUN/'view/geometry_metrics.json')
    qa = read('root_QA', BASE/'root_qa.json')
    clock_receipts = dict(top_start=read('top_start', BASE/'top_start.json'),
        helper_start=read('helper_start', BASE/'helper_start.json'),
        display_start=read('display_start', RUN/'display_start.json'))

    def absent(phase):
        counter = {'science':'science_launches', 'check':'ordinary_check_launches', 'viewer':'viewer_launches'}[phase]
        if helper is not None and helper.get(counter) == 0:
            return dict(status='not_started', reason='Actual helper '+counter+'=0')
        return dict(status='not_available', reason='No ordinary record; not inferred to be a successful or unstarted phase')

    layers = []
    phase_rows = [('top', 'top_supervision.json', top),
        ('science', 'run_001/science_supervision.json', read('science_supervision', RUN/'science_supervision.json')),
        ('check', 'run_001/ordinary_check_supervision.json', read('ordinary_check_supervision', RUN/'ordinary_check_supervision.json')),
        ('viewer', 'run_001/viewer_supervision.json', read('viewer_supervision', RUN/'viewer_supervision.json'))]
    for phase, name, row in phase_rows:
        if row is None:
            layers.append(dict(phase=phase, path=name, **absent(phase)))
            continue
        proof = row.get('cleanup_proof', {})
        layers.append(dict(phase=phase, path=name, status='available',
            reason=row.get('reason'), returncode=row.get('returncode'),
            cleanup_verified=row.get('cleanup_verified'), job_handle_closed=proof.get('job_handle_closed'),
            complete_instance_proof=proof.get('pass'),
            active_processes=proof.get('final_accounting', {}).get('ActiveProcesses'),
            elapsed_seconds=row.get('elapsed_seconds'),
            sampled_peak_tree_rss_bytes=row.get('peak_tree_rss_bytes'),
            normal_exit_and_clean=row.get('reason') == 'normal_exit' and row.get('returncode') == 0 and clean(row),
            receipt=row))
    all_four = len(layers) == 4 and all(row.get('normal_exit_and_clean') is True for row in layers)

    production = []
    for pin in protocol['production']:
        _, actual = ordinary_identity(pin['path'])
        production.append(dict(path=pin['path'], expected={k:pin[k] for k in ('bytes','sha256')},
            actual={k:actual[k] for k in ('bytes','sha256')},
            unchanged=all(pin[k] == actual[k] for k in ('bytes','sha256'))))
    unchanged = sum(row['unchanged'] for row in production)
    declared_source_paths = {str(Path(pin['path']).resolve()) for pin in protocol['production']}
    actual_source_paths = {str(path.resolve()) for path in (Path(protocol['production_src'])/'hf_eval').rglob('*.py')}
    source_inventory_equal = actual_source_paths == declared_source_paths
    sources_ok = len(production) == unchanged == 58 and source_inventory_equal
    summary = None
    if force is not None:
        keys = ('schema_version','status','failure','target_reached','source','continuation','force_task',
            'settings','force_settings','response_mode','tangent_mode','initial_guess','parent_initial_guess',
            'call_counts','path_summary','mechanics_source_sha256','timing_seconds','descriptor_sha256','scope')
        summary = {key:force.get(key) for key in keys}
        scalar_keys = ('P_target_half_N','load_increment_from_anchor_half_N','load_increment_from_root_half_N',
            'generalized_body_internal_force_half_N','generalized_force_residual_half_N',
            'generalized_force_scale_half_N','generalized_force_bound_half_N',
            'relative_generalized_force_residual','body_q_mm','input_mean_mm','R_input_N',
            'force_on_body_N','ledger','relative_residual','residual_scale_half_N','force_scale_floor_half_N',
            'constraint_residual','constraint_bound','relative_global_force_balance',
            'global_force_balance_scale_half_N','minimum_J','max_abs_Hu_per_mm','max_abs_prescribed_error_mm',
            'newton_checks','is_original_target','original_target_index','segment_original_target_index',
            'original_target_force_half_N','bisection_depth','state_sha256','fresh_anchor','state','fields')
        summary.update(scalar_rows=[{key:row[key] for key in scalar_keys if key in row}
                for row in force.get('accepted_steps',[])],
            newton_history=force.get('newton_history', []), trials=force.get('trials', []),
            failed_attempts=force.get('failed_attempts', []),
            linear_solve_diagnostics=force.get('linear_solve_diagnostics', []),
            Newton_base_checks=len(force.get('newton_history', [])),
            line_search_trial_count=len(force.get('trials', [])),
            qualification_flags={key:value for key,value in force.items() if key.endswith('_qualified')},
            scalar_rows_scope='All actual accepted states, including internal bisection; fields/state are ordinary declarations only. No positions/body arrays or scientific payloads decoded.')
    rendered_pins = ({Path(row['path']).name:{key:row[key] for key in ('bytes','sha256')}
        for row in renderer.get('images',[])} if renderer else {})
    qa_pass = (qa is not None and qa.get('status') == 'pass' and qa.get('pixel_inspections') == 5
        and qa.get('scientific_calls') == 0 and qa.get('rerenders') == 0
        and qa.get('image_identities') == rendered_pins
        and set(rendered_pins) == set(protocol['image_names']))
    force_pass = (force is not None and force.get('status') == 'success'
        and force.get('failure') is None and force.get('target_reached') is True
        and force.get('path_summary',{}).get('reached_force_half_N') == protocol['loads_half_N'][-1])
    qualification_flags = summary.get('qualification_flags', {}) if summary else {}
    qualifications_ok = all(qualification_flags.get(key) is False for key in
        ('independent_HP_qualified','effective_grasp_qualified','release_qualified','HF_qualified'))
    gates = dict(numerical_path=force_pass, science_receipt=(science or {}).get('status') == 'pass',
        ordinary_check=(check or {}).get('status') == 'pass',
        pure_renderer=(renderer or {}).get('status') == 'rendered_pending_root_visual_check',
        root_QA=qa_pass, helper_receipt=(helper or {}).get('status') == 'pass',
        four_normal_exit_cleanup_proofs=all_four, seal_execution_pass=seal.get('execution_pass') is True,
        seal_status=seal.get('status') == 'pass', production_58_unchanged=sources_ok,
        qualifications_preserved=qualifications_ok)
    status = 'PASS' if all(gates.values()) else 'NOT_PASS'
    result = dict(stage=STAGE, schema_version=STAGE+'-closed-ordinary-execution-result-1.0',
        status=status, scientific_window_closed=True, created_utc=datetime.now(timezone.utc).isoformat(),
        baseline=protocol['baseline'], pass_components=gates, protocol_identity=identities['protocol'],
        original_protocol=dict(stage=protocol['stage'], baseline=protocol['baseline'],
            loads_half_N=protocol['loads_half_N'], segment_loads_half_N=protocol['segment_loads_half_N'],
            controller_seconds=protocol['controller_seconds'], helper_seconds=protocol['helper_seconds'],
            outer_seconds=protocol['outer_seconds'], root_P0_half_N=protocol['root_P0_half_N']),
        seal=seal, helper_receipt=helper or dict(status='not_available'), supervised_layers=layers,
        clock_receipts=clock_receipts, production_source_inventory_equal=source_inventory_equal,
        extra_production_paths=sorted(actual_source_paths-declared_source_paths),
        missing_production_paths=sorted(declared_source_paths-actual_source_paths),
        production_sources_unchanged=unchanged, production_source_identity_check=production,
        new_HP=(force or {}).get('call_counts',{}).get('HP_calls'), new_tests=0,
        new_production_modifications=0 if sources_ok else None,
        external_retries=protocol.get('external_retries'),
        science_receipt=science or absent('science'), check=check or absent('check'),
        renderer=renderer or absent('viewer'), root_QA=qa or absent('viewer'),
        geometry_metrics=geometry or absent('viewer'),
        force_summary=summary or dict(status=absent('science')['status'], scalar_rows=[]),
        prior_reference_history=protocol['history'],
        source_selected=protocol['source_selected'], source_context=protocol['source_context'],
        reference_comparison=dict(status='not_available_no_P2_reference', q_error_mm=None,
            full_DOF_error_mm=None, R_error_N=None), ordinary_file_identities=identities,
        existing_media_pins_from_receipts=dict(images=rendered_pins,
            animation=(renderer or {}).get('animation'), provenance='Copied from original renderer/rootQA receipts only; no media bytes read or rehashed by closure'),
        archive_pin_from_seal=seal.get('archive'),
        new_science_in_this_recording=0, NPZ_decodes_in_this_recording=0,
        scientific_payload_bytes_read_or_hashed_in_this_recording=0, ZIP_or_media_opens_in_this_recording=0,
        plots_or_tests_or_pixel_rechecks_in_this_recording=0,
        scope='Only closed-window ordinary receipts and production source identities; no new equilibrium/reference or reopening. Pending renderer/helper labels retain their earlier receipt time.',
        qualification='Guided total weak-force continuation only; no pressure, pure contact, capacity, stability, release, full-path HP or HF qualification')
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    live_path = AUTHOR/'LIVE_HANDOFF.json'
    if live_path.exists():
        live = json.loads(live_path.read_bytes())
        live.update(status='closed_'+status+'_no_reopen', scientific_window_closed=True,
            elapsed_outer_seconds=seal.get('elapsed_outer_seconds'),
            execution_result=output.as_posix(),
            next_action='Ordinary actual-result review, documentation, main publication and restore only; no further science/cache decode/media reopening/drawing under this closed window.')
        live_path.write_bytes((json.dumps(live, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())
    print(json.dumps(dict(stage=STAGE, status=status, scientific_window_closed=True,
        supervised_layers=len(layers), production_sources_unchanged=unchanged,
        accepted_states=len((summary or {}).get('scalar_rows',[])), recording_scientific_calls=0)), flush=True)


if __name__ == '__main__':
    main()
