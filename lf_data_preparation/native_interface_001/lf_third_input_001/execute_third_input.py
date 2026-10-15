"""Run the authorized third LF input preparation once; seal actual outputs."""
from time import perf_counter
STARTED = perf_counter()
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
read = lambda path: json.loads(path.read_bytes())
protocol = read(STAGE / 'protocol.json')
OUTPUT = ROOT / protocol['output_directory']
events, peak = Counter(), 0
process = psutil.Process()


def checkpoint(event='checkpoint'):
    global peak
    peak = max(peak, process.memory_info().rss)
    if (perf_counter()-STARTED > protocol['helper_seconds'] or peak > protocol['sampled_RSS_bytes']
            or (STAGE/'stop_requested.txt').exists()):
        raise RuntimeError('L-THIRD1 resource/stop boundary reached')
    events[event] += 1


def check_bindings():
    for name, pin in protocol['source_bindings'].items():
        checkpoint()
        assert sha256((ROOT/name).read_bytes()).hexdigest() == pin, name


def seal():
    outputs = {}
    if OUTPUT.exists():
        for path in sorted(OUTPUT.rglob('*')):
            if path.is_file():
                checkpoint()
                raw = path.read_bytes()
                outputs[path.relative_to(ROOT).as_posix()] = dict(sha256=sha256(raw).hexdigest(), bytes=len(raw))
    checkpoint()
    return outputs


def main():
    auth = read(STAGE/'author/authorization.json')
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['card'] == protocol['card'] == 'L-THIRD1'
    assert auth['protocol_sha256'] == sha256((STAGE/'protocol.json').read_bytes()).hexdigest()
    assert not OUTPUT.exists()
    status, error, outputs, seal_status, report = 'not_pass', None, {}, 'not_complete', None
    try:
        check_bindings()
        checkpoint('helper_import_started')
        spec = importlib.util.spec_from_file_location('_third_lf_preparation', STAGE/'prepare_third_input.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        checkpoint('helper_import_completed')
        report = module.main(['--repo', str(ROOT), '--protocol', str(STAGE/'protocol.json')], checkpoint)
        for event in ('source_extract', 'input_prepare', 'model_build', 'model_write', 'plot'):
            assert events[event+'_started'] == events[event+'_completed'] == 1, event
        assert events['geometry_read_started'] == events['geometry_read_completed'] == 2
        assert events['source_array_read_started'] == events['source_array_read_completed'] == events['report_written'] == 1
        check_bindings()
        outputs = seal()
        assert (OUTPUT/'compatibility.json').is_file() and (OUTPUT/'undeformed_compatibility.png').is_file()
        seal_status, status = 'complete_inside_original_helper_window', 'pass'
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
        if perf_counter()-STARTED <= protocol['helper_seconds'] and not (STAGE/'stop_requested.txt').exists():
            try:
                outputs, seal_status = seal(), 'actual_partial_inside_original_helper_window'
            except BaseException:
                seal_status = 'not_completed_before_resource_close'
    OUTPUT.mkdir(parents=True, exist_ok=True)
    receipt = dict(card='L-THIRD1', status=status, error=error, invocations=1, events=dict(events), outputs=outputs,
        output_identity_seal=seal_status, protocol_sha256=auth['protocol_sha256'], source_baseline_commit=auth['source_baseline_commit'],
        new_sources_pinned_individually=True, elapsed_seconds=perf_counter()-STARTED,
        helper_seconds=protocol['helper_seconds'], sampled_peak_RSS_bytes=peak, sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()), completed_utc=datetime.now(timezone.utc).isoformat(),
        new_input_preparations=events['input_prepare_completed'], new_model_builds=events['model_build_completed'],
        new_plots=events['plot_completed'], new_force_calls=0, new_tangent_calls=0, new_HP_calls=0, new_solver_calls=0,
        zero_mechanics_basis='Pinned source calls only input preparation, reference model construction/write and undeformed plotting; no response entry',
        claim='Input and undeformed compatibility only; manufacturing pending; no pressure or effective gripping qualification')
    target = OUTPUT/'execution_receipt.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    try:
        checkpoint()
    except RuntimeError as failure:
        receipt.update(status='not_pass', error=dict(type=type(failure).__name__, message=str(failure)), elapsed_seconds=perf_counter()-STARTED)
        target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        status = 'not_pass'
    print(json.dumps(dict(status=status, events=dict(events), outputs=len(outputs))), flush=True)
    if status != 'pass':
        raise RuntimeError('L-THIRD1 closed not_pass; no retry')


if __name__ == '__main__':
    main()
