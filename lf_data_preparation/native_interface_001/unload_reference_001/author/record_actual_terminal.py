"""Record the actual terminal observation of the sole M-PREF1 session."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/unload_reference_001'
HERE = Path('D:/hf-native-workpiece-api-author-20261013/MPREF1_execution_review_001')


def main():
    HERE.mkdir(parents=True,exist_ok=True)
    execution = ROOT/REL/'run_001/reference/execution_receipt.json'
    outer = ROOT/REL/'reference_launch.json'
    e,o = (json.loads(path.read_bytes()) for path in (execution,outer))
    assert e['status']==o['status']=='pass' and o['invocations']==1 and o['exit_code']==0
    assert e['HP_calls_started']==e['HP_calls_completed']==4
    assert e['accepted_mechanical_states_completed']==e['workpiece_states_completed']==2
    assert e['plot_started']==e['plot_completed']==1
    assert e['output_identity_seal']=='complete_inside_original_helper_window'
    assert o['stop_reason'] is None and o['all_bindings_unchanged'] is True
    assert e['elapsed_seconds']<=900 and o['elapsed_seconds']<=960
    value = dict(card='M-PREF1',root_observed_same_session_terminal=True,
        unified_exec_session_id=90472,initial_launch_chunk_id='72dbb2',terminal_poll_chunk_id='3327b7',
        tool_terminal_exit_code=0,tool_terminal_output='{"status": "pass", "invocations": 1, "exit_code": 0, "elapsed_seconds": 178.64134569995804, "peak_sampled_tree_RSS_bytes": 1280548864, "stop_reason": null}',
        source_baseline_commit='ea5b55cc4f2ace87a78ed512d6bb14382e826a5d',
        execution_status=e['status'],execution_closed=True,
        execution_receipt_sha256=sha256(execution.read_bytes()).hexdigest(),
        outer_sha256=sha256(outer.read_bytes()).hexdigest(),
        outer_elapsed_seconds=o['elapsed_seconds'],helper_receipt_elapsed_seconds=e['elapsed_seconds'],
        peak_sampled_tree_RSS_bytes=o['peak_sampled_tree_RSS_bytes'],
        recorded_utc=datetime.now(timezone.utc).isoformat(),
        observation_new_science_HP_solver_or_plot_calls=0,
        scientific_or_media_byte_reads_hashes_headers_decode=0,
        no_second_launch_retry_repair_extension_or_force=True)
    with (HERE/'root_terminal_confirmation.json').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({key:value[key] for key in ('execution_status','unified_exec_session_id','tool_terminal_exit_code','outer_elapsed_seconds')},ensure_ascii=False))


if __name__=='__main__':
    main()
