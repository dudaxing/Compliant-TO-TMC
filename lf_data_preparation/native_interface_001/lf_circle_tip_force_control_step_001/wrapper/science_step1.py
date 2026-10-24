"""One frozen nonzero-q force continuation; no scientific work at import time."""
import time
START = time.monotonic()

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import traceback

BASE = Path(__file__).resolve().parent
RUN = BASE/'run_001'
STAGE = 'L-CTIPFSTEP1'


def read(path):
    return json.loads(Path(path).read_bytes())


def identity(path):
    raw = Path(path).read_bytes()
    return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def progress(value):
    pending = RUN/'science_progress.pending.json'
    pending.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    os.replace(pending, RUN/'science_progress.json')


def main():
    if len(sys.argv) != 1 or (RUN/'science_receipt.json').exists() or (RUN/'force').exists():
        raise ValueError('Preserve existing output; only the unique frozen command is authorized')
    receipt = dict(stage=STAGE, status='not_pass', started_utc=datetime.now(timezone.utc).isoformat(),
        api_attempts=0, api_returns=0, external_retries=0, new_tests=0, new_HP=0,
        production_modifications=0, accepted_callbacks=[])
    events, allowed = [], set()
    try:
        p = read(BASE/'protocol.json')
        bound = read(p['source_binding_file'])
        contract = read(p['contract_file'])
        if (p['stage'] != STAGE or Path(p['runtime_base']).resolve() != BASE
                or p['source_context'] != bound or p['source_selected'] != bound['selected_force_state']
                or p['loads_half_N'] != contract['loads']['full_targets_half_N']
                or p['segment_loads_half_N'] != contract['loads']['requested_segment_half_N']
                or p['controller_seconds'] != contract['resources']['controller_seconds']
                or p['parent_result'] != contract['api_call']['saved_force_result']):
            raise ValueError('Protocol/source/approved contract differs')
        allowed = {os.path.normcase(str(Path(row['path']).resolve()))
            for row in bound['scientific_dependencies_stat_only']}
        if len(allowed) != 3:
            raise ValueError('Exactly three frozen old admission NPZ paths are required')
        new_tree = (RUN/'force').resolve()

        def audit(event, args):
            if event != 'open' or not isinstance(args[0], (str, bytes)):
                return
            path = Path(os.fsdecode(args[0]))
            if path.suffix.lower() != '.npz':
                return
            path = path.resolve()
            key = os.path.normcase(str(path))
            access = args[2] & (os.O_WRONLY | os.O_RDWR)
            read_capable = access != os.O_WRONLY
            write_capable = access != os.O_RDONLY
            new_output = path.is_relative_to(new_tree)
            row = dict(path=path.as_posix(), mode=args[1], flags=args[2],
                read_capable=read_capable, write_capable=write_capable,
                scope='new_output' if new_output else 'old_admission',
                allowed=(new_output or key in allowed), elapsed_worker_seconds=time.monotonic()-START)
            events.append(row)
            if write_capable and not new_output:
                raise RuntimeError('NPZ write outside the new force tree: '+str(path))
            if read_capable and not (new_output or key in allowed):
                raise RuntimeError('NPZ read outside frozen old admission/new output paths: '+str(path))

        sys.addaudithook(audit)
        for pin in p['bindings']:
            path = Path(pin['path'])
            if path.suffix.lower() in ('.npz', '.zip', '.png', '.gif', '.svg'):
                raise ValueError('Binding verification must not open scientific payload or media')
            if identity(path) != {key: pin[key] for key in ('bytes', 'sha256')}:
                raise ValueError('Frozen ordinary/source bytes changed: '+str(path))
        progress(dict(stage=STAGE, phase='import_and_nonzero_source_admission_pending',
            accepted_count=0, elapsed_worker_seconds=time.monotonic()-START))
        sys.path.insert(0, p['production_src'])
        from hf_eval.native_guided_force_resume import extend_native_guided_force
        import hf_eval.native_guided_force_resume as implementation
        if Path(implementation.__file__).resolve() != Path(p['production_src']).resolve()/'hf_eval/native_guided_force_resume.py':
            raise ValueError('Imported continuation is not the installed frozen source')

        def on_accept(row):
            keys = ('P_target_half_N', 'body_q_mm', 'input_mean_mm', 'R_input_N',
                'relative_residual', 'relative_generalized_force_residual', 'minimum_J',
                'max_abs_Hu_per_mm', 'relative_global_force_balance', 'newton_checks',
                'is_original_target', 'original_target_index', 'segment_original_target_index',
                'bisection_depth', 'state_sha256', 'fresh_anchor')
            actual = {key: row[key] for key in keys}
            actual['elapsed_worker_seconds'] = time.monotonic()-START
            receipt['accepted_callbacks'].append(actual)
            progress(dict(stage=STAGE, phase='accepted_force_state',
                accepted_count=len(receipt['accepted_callbacks']), last=actual))
            print(json.dumps(dict(phase='accepted', accepted_index=len(receipt['accepted_callbacks'])-1, **actual)), flush=True)

        receipt['api_attempts'] = 1
        result = extend_native_guided_force(p['parent_result'], p['loads_half_N'], RUN/'force',
            time_limit_seconds=p['controller_seconds'], on_accept=on_accept)
        receipt['api_returns'] = 1
        receipt.update(production_status=result['status'], production_failure=result['failure'],
            target_reached=result['target_reached'], accepted_states=len(result['accepted_steps']),
            call_counts=result['call_counts'], result_identity=identity(RUN/'force/result.json'),
            admitted_old_NPZ_paths_by_source_control_flow=3,
            decoded_archives_by_completed_admission_control_flow=2,
            decoded_fields_by_completed_admission_control_flow=6,
            decoded_field_count_basis='Byte-frozen completed admission: four geometry masks and selected lift/fluctuation. This is source-control-flow accounting, not a dynamic field hook.')
        if result['status'] != 'success' or result['target_reached'] is not True or result['failure'] is not None:
            raise RuntimeError('Unique continuation did not reach P2; preserve its actual result/partial')
        inherited = dict(bound['settings'])
        inherited['time_limit_seconds'] = p['controller_seconds']
        cont = result['continuation']
        counts = result['call_counts']
        if (result['schema_version'] != 'hf-native-guided-force-1.1'
                or result['source'] != bound['root_fixed_source']
                or result['force_task']['body_load_targets_half_N'] != p['loads_half_N']
                or result['force_task']['anchor_target_half_N'] != p['loads_half_N'][0]
                or result['force_task']['segment_anchor_half_N'] != p['segment_loads_half_N'][0]
                or result['force_task']['held_input_mean_mm'] != 1.06
                or result['settings'] != inherited or result['force_settings'] != bound['force_settings']
                or result['response_mode'] != bound['response_mode']
                or result['tangent_mode'] != bound['tangent_mode']
                or result['initial_guess'] != bound['initial_guess']
                or cont['global_original_target_offset'] != 1
                or cont['requested_segment_targets_half_N'] != p['segment_loads_half_N']
                or cont['parent_result']['path'] != Path(p['parent_result']).resolve().as_posix()
                or len(receipt['accepted_callbacks']) != len(result['accepted_steps'])
                or len(result['model']['coordinates_mm']) != 14985
                or len(result['model']['connectivity']) != 14720
                or counts['solver_invocations'] != 1 or counts['HP_calls'] != 0
                or counts['save_force_calls'] != 0 or counts['save_tangent_calls'] != 0):
            raise ValueError('Returned continuation differs from the frozen execution contract')
        actual_old = {os.path.normcase(str(Path(row['path']).resolve())) for row in events
            if row['scope'] == 'old_admission' and row['read_capable']}
        if actual_old != allowed:
            raise ValueError('Observed old NPZ path set differs from the three frozen admission paths')
        receipt['status'] = 'pass'
    except BaseException as error:
        receipt['error'] = dict(type=type(error).__name__, code=getattr(error, 'code', None),
            message=str(error), traceback=traceback.format_exc())
    finally:
        old = [row for row in events if row['scope'] == 'old_admission' and row['read_capable']]
        new = [row for row in events if row['scope'] == 'new_output']
        receipt.update(elapsed_worker_seconds=time.monotonic()-START, npz_open_events=events,
            old_npz_read_open_events=old, unique_old_NPZ_read_paths=sorted({row['path'] for row in old}),
            new_output_npz_open_events=new, npz_open_audit_does_not_patch_HF_or_numpy=True,
            open_observation_scope='Named NPZ open capability events only; includes raw hash/readback. Not field-decode counts or proof of all external reads.')
        write_new(RUN/'science_receipt.json', receipt)
        progress(dict(stage=STAGE, phase='science_worker_closed', status=receipt['status'],
            accepted_count=len(receipt['accepted_callbacks']), elapsed_worker_seconds=receipt['elapsed_worker_seconds']))
        print(json.dumps(dict(status=receipt['status'], elapsed=receipt['elapsed_worker_seconds'])), flush=True)
    return 0 if receipt['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
