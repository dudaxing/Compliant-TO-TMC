"""L-USE1 approved one-shot helper; the reusable example itself uses stdlib only."""
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
read = lambda p: json.loads(p.read_bytes())
protocol = read(STAGE / 'protocol.json')
OUTPUT = ROOT / protocol['output_directory']
events, calls, peak = Counter(), dict(consumptions_started=0, consumptions_completed=0), 0
process = psutil.Process()


def checkpoint(event='resource_check'):
    global peak
    peak = max(peak, process.memory_info().rss)
    if (perf_counter() - STARTED > protocol['helper_seconds']
            or peak > protocol['sampled_RSS_bytes'] or (STAGE / 'stop_requested.txt').exists()):
        raise RuntimeError('L-USE1 resource/stop boundary reached')
    events[event] += 1


def seal():
    result = {}
    for name in ('states_table.json', 'REVIEW.md'):
        checkpoint()
        path = OUTPUT / name
        if path.exists():
            raw = path.read_bytes()
            result[path.relative_to(ROOT).as_posix()] = dict(sha256=sha256(raw).hexdigest(), bytes=len(raw))
    checkpoint()
    return result


def main():
    auth = read(STAGE / 'author/authorization.json')
    assert auth['card'] == protocol['card'] == 'L-USE1' and auth['authorized'] is True
    assert auth['authorization_from_direct_human_reply'] is True and auth['one_invocation'] is True
    assert auth['protocol_sha256'] == sha256((STAGE / 'protocol.json').read_bytes()).hexdigest()
    assert not OUTPUT.exists()
    status, error, outputs, identity_seal, table = 'not_pass', None, {}, 'not_complete', None
    try:
        checkpoint()
        source = ROOT / protocol['example_source']
        assert sha256(source.read_bytes()).hexdigest() == protocol['source_bindings'][protocol['example_source']]
        spec = importlib.util.spec_from_file_location('_lf_saved_consumption_example', source)
        example = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(example)
        calls['consumptions_started'] += 1
        table = example.main(['--repo', str(ROOT), '--index', protocol['index_file'],
            '--output', str(OUTPUT)], checkpoint)
        calls['consumptions_completed'] += 1
        assert {record['path']: record['sha256'] for record in table['inputs'].values()} == protocol['json_input_bindings']
        assert len(table['rows']) == protocol['expected_rows'] == 25
        assert [row['accepted_row_index'] for row in table['rows'] if row['has_matched_reference']] == [13, 16]
        reference = table['independent_reference']
        assert reference['status'] == 'matched_partial' and reference['full_path_reference_pass'] is False
        assert reference['selected_reference_pass'] is True and reference['accepted_reference_pass'] is False
        assert len(table['existing_media']) == 5 and all(value is False for value in table['producer_flags'].values())
        assert {key: events[key] for key in ('json_read_started', 'json_read_completed', 'table_written', 'review_written')} == dict(json_read_started=3, json_read_completed=3, table_written=1, review_written=1)
        checkpoint(); outputs = seal(); identity_seal = 'complete_inside_original_helper_window'
        status = 'pass'
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
        if perf_counter()-STARTED <= protocol['helper_seconds'] and not (STAGE/'stop_requested.txt').exists():
            try:
                outputs = seal(); identity_seal = 'actual_partial_inside_original_helper_window'
            except BaseException:
                identity_seal = 'not_completed_before_resource_close'
    if not OUTPUT.exists():
        OUTPUT.mkdir(parents=True, exist_ok=False)
    calls.update(json_reads_started=events['json_read_started'], json_reads_completed=events['json_read_completed'],
        table_writes=events['table_written'], review_writes=events['review_written'])
    receipt = dict(card='L-USE1', status=status, error=error, calls=calls,
        protocol_sha256=auth['protocol_sha256'], authorized_execution_source_commit=auth['authorized_execution_source_commit'],
        rows_written=len(table['rows']) if table else 0, selected_indices=[13,16] if table else [],
        matched_reference_rows=sum(row['has_matched_reference'] for row in table['rows']) if table else 0,
        outputs=outputs, output_identity_seal=identity_seal, elapsed_seconds=perf_counter()-STARTED,
        helper_seconds=protocol['helper_seconds'], sampled_peak_RSS_bytes=peak, sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()), completed_utc=datetime.now(timezone.utc).isoformat(),
        zero_new_science_basis='Pinned stdlib example and metadata wrapper; no dynamic mechanical hook monitoring',
        new_HF_API_calls=0, new_tests=0, new_force_calls=0, new_tangent_calls=0, new_HP_calls=0,
        new_solver_calls=0, new_plots=0, media_reads=0, media_decodes=0, pixel_checks=0,
        NPZ_reads=0, scientific_gzip_reads=0, CSV_reads=0)
    with (OUTPUT/'execution_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    try:
        checkpoint()
    except RuntimeError as failure:
        status = receipt['status'] = 'not_pass'
        receipt['error'] = dict(type=type(failure).__name__, message=str(failure))
        receipt['elapsed_seconds'] = perf_counter()-STARTED
        (OUTPUT/'execution_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(status=status, calls=calls, rows=receipt['rows_written'])), flush=True)
    if status != 'pass':
        raise RuntimeError('L-USE1 closed not_pass; no retry')


if __name__ == '__main__':
    main()
