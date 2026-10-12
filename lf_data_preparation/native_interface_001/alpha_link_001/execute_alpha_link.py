"""M-ALINK1: associate one saved child suffix with its existing reference/views.

The public summary/writer are reused once. Only JSON, declared source and raw
image bytes are read; no arrays, compressed reference data or mechanics run.
This prepared source requires its own direct human approval before execution.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import psutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--protocol', type=Path, required=True)
parser.add_argument('--time-limit', type=float, required=True)
ARGS = parser.parse_args()
ROOT, PROTOCOL_FILE = ARGS.repo.resolve(), ARGS.protocol.resolve()
STAGE = PROTOCOL_FILE.parent
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
CONTRACT = read(PROTOCOL_FILE)
auth = read(STAGE/'author/authorization.json')
reply_file, proof_file = STAGE/'author/direct_human_reply.json', STAGE/'author/source_publication_receipt.json'
reply, proof = read(reply_file), read(proof_file)
head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
if not (CONTRACT['schema_version'] == 'alpha-saved-segment-linked-delivery-card-1.0'
        and CONTRACT['card'] == auth['card'] == reply['card'] == proof['prepared_card'] == 'M-ALINK1'
        and CONTRACT['prepared'] is True and CONTRACT['authorized'] is CONTRACT['executed'] is False
        and auth['authorized'] is True
        and auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
        and auth['protocol_sha256'] == proof['protocol_sha256'] == sha(PROTOCOL_FILE)
        and auth['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit'] == head
        and auth['human_evidence_sha256'] == sha(reply_file)
        and auth['source_publication_receipt_sha256'] == sha(proof_file)
        and auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip()
        and reply['reply_context'] == 'Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction'
        and proof['status'] == 'published_and_incrementally_restored_pass'
        and proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
        and ARGS.time_limit == auth['helper_seconds'] == CONTRACT['phases']['link']['helper_seconds'] == 180.
        and auth['outer_seconds'] == CONTRACT['phases']['link']['outer_seconds'] == 240
        and auth['sampled_RSS_bytes'] == CONTRACT['sampled_RSS_bytes'] == 8*1024**3
        and auth['invocations_authorized'] == 1 and auth['retries'] == 0 and auth['force'] is False):
    raise ValueError('M-ALINK1 requires its actual direct human approval and published source proof')
if any(Path(name).suffix.lower() not in {'.py','.json','.md','.png','.gif'} for name in CONTRACT['bindings']):
    raise ValueError('M-ALINK1 bindings may only read declared source, JSON, documentation or raw media')
OUTPUT = ROOT/CONTRACT['output_directory']
PROCESS, peak = psutil.Process(), 0
calls = dict(saved_summary_started=0, saved_summary_completed=0, response_writes=0, index_writes=0)
all_bindings_unchanged = False


def checkpoint():
    global peak
    peak = max(peak, PROCESS.memory_info().rss)
    if perf_counter()-STARTED > ARGS.time_limit or peak > CONTRACT['sampled_RSS_bytes'] or (STAGE/'stop_requested.txt').exists():
        raise RuntimeError('M-ALINK1 cooperative resource/stop boundary reached')


def write(path, value):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def artifact(name):
    return dict(path=name, path_scope='repo_relative', sha256=CONTRACT['bindings'][name])


def verify_bindings():
    for name, pin in CONTRACT['bindings'].items():
        if sha(ROOT/name) != pin:
            raise ValueError('Original bound artifact changed: '+name)
        checkpoint()


def verify_response(response):
    path, reference, views, continuation = (response[name] for name in ('path','independent_reference','views','continuation'))
    if not (response['status'] == 'success' and response['failure'] is None
            and path['accepted_states'] == CONTRACT['expected_accepted_states'] == 2
            and len(CONTRACT['selected_state_identity']) == 2
            and path['requested_targets_mm'] == CONTRACT['targets_mm'] == [1.2,1.15] and path['completed'] is True
            and path['task_target_executed'] is path['full_original_path_completed'] is False
            and response['target_response'] is None
            and continuation['original_target_indices'] == CONTRACT['original_target_indices'] == [13,14]
            and continuation['requested_suffix_targets_mm'] == CONTRACT['targets_mm']
            and continuation['parent_status'] == 'failed' and continuation['parent_failure']['code'] == 'time_limit'
            and continuation['parent_path_completed'] is continuation['parent_task_target_executed'] is False
            and continuation['parent_unload_endpoint_reached'] is continuation['full_original_path_executed_by_child'] is False
            and continuation['segment_completed'] is continuation['anchor_revalidated'] is continuation['anchor_identity_preserved'] is True
            and all(value is False for value in response['producer_flags'].values())
            and reference['status'] == 'matched' and reference['source_bindings_verified'] is True
            and reference['accepted_reference_pass'] is reference['full_path_reference_pass'] is True
            and reference['HP_calls_completed'] == 4 and reference['full_original_path_reference_pass'] is False
            and reference['reference_scope'] == 'Child accepted suffix only'
            and all(reference[key] is False for key in ('HP_all_columns_qualified','contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified'))
            and views['status'] == 'matched' and views['case_label'] == 'resumed_alpha_half'
            and sorted(link['path'] for link in views['links']) == sorted(CONTRACT['media_files'])
            and sorted(link['kind'] for link in views['links']) == ['gif','png','png','png']):
        raise ValueError('Saved child/reference/view scope differs; association cannot change qualification')
    for name, expected in zip(('maximum_loading_stroke','requested_endpoint_response'), CONTRACT['selected_state_identity']):
        row = response[name]
        if not (row['index'] == expected['child_index'] and row['original_target_index'] == expected['original_target_index']
                and row['state_sha256'] == expected['state_sha256'] and row['d_mm'] == expected['target_mm']
                and row['leg'] == expected['leg'] and row['continuation_anchor'] is expected['continuation_anchor']):
            raise ValueError('Child/original state identity differs: '+name)


def run():
    global all_bindings_unchanged
    checkpoint(); verify_bindings()
    previous = read(ROOT/CONTRACT['previous_publication_file'])
    launch, lifecycle = (read(ROOT/CONTRACT[name]) for name in ('reference_launch_file','reference_lifecycle_file'))
    if not (previous['status'] == 'published_and_incrementally_restored_pass' and previous['executed_card'] == 'M-AREF1'
            and previous['execution_status'] == 'pass' and previous['execution_closed'] is True
            and previous['published_commit'] == CONTRACT['source_baseline_commit']
            and launch['status'] == lifecycle['status'] == 'pass' and launch['invocations'] == 1
            and launch['exit_code'] == 0 and launch['stop_reason'] is None and launch['completed_utc']
            and lifecycle['HP_calls_started'] == lifecycle['HP_calls_completed'] == 4
            and lifecycle['accepted_mechanical_states_completed'] == lifecycle['workpiece_states_completed'] == 2
            and launch['protocol_sha256'] == previous['protocol_sha256']):
        raise ValueError('Existing closed, published two-state reference provenance differs')
    sys.path.insert(0, str(ROOT/'hf_repo/src'))
    from hf_eval.native_response import summarize_saved_native_result, write_native_response
    for name in ('hf_eval','hf_eval.native_response'):
        source = Path(sys.modules[name].__file__).resolve()
        if source != ROOT/('hf_repo/src/hf_eval/__init__.py' if name == 'hf_eval' else 'hf_repo/src/hf_eval/native_response.py'):
            raise ValueError('Imported public summary source origin differs')
    calls['saved_summary_started'] += 1
    response = summarize_saved_native_result(CONTRACT['result_file'], repo_root=ROOT,
        reference_file=CONTRACT['reference_file'], view_manifest=CONTRACT['raw_view_file'])
    calls['saved_summary_completed'] += 1
    verify_response(response); checkpoint()
    linked = OUTPUT/'linked_response.json'
    write_native_response(response, linked); calls['response_writes'] += 1
    index = dict(schema_version='alpha-saved-segment-linked-index-1.0', status='pass',
        linked_response=dict(path=linked.relative_to(ROOT).as_posix(), path_scope='repo_relative', sha256=sha(linked)),
        saved_artifacts={key:artifact(CONTRACT[key]) for key in ('result_file','model_file','original_response_file',
            'parent_result_file','reference_file','raw_view_file','view_case_summary_file','reference_launch_file','reference_lifecycle_file','previous_publication_file')},
        images=response['views']['links'], physics=response['physics'], options=response['options'],
        path=response['path'], continuation=response['continuation'],
        maximum_loading_stroke=response['maximum_loading_stroke'], requested_endpoint_response=response['requested_endpoint_response'],
        target_response=response['target_response'], independent_reference=response['independent_reference'],
        views=response['views'], source_flags=response['producer_flags'], force_semantics=response['force_semantics'],
        field_scope=response['field_scope'],
        qualification='Existing saved association only. Full-path reference pass covers only the complete two-state child suffix; the parent/original15-target path remains failed/incomplete. No all-column,pressure,effective-clamp,stability or HF5 qualification.',
        path_basis='Artifact paths are relative to the restored repository root; inherited continuation metadata is copied without rewriting its historical paths')
    write(OUTPUT/'light_index.json', index); calls['index_writes'] += 1
    if {name for name in sys.modules if name == 'hf_eval' or name.startswith('hf_eval.')} != {'hf_eval','hf_eval.native_response'}:
        raise ValueError('Unexpected mechanical HF module imported')
    verify_bindings(); all_bindings_unchanged = True
    outputs = {path.name:sha(path) for path in (linked, OUTPUT/'light_index.json')}
    checkpoint()
    return outputs


def receipt(status, outputs, error=None):
    return dict(schema_version='M-ALINK1-saved-association-execution-1.0', status=status, error=error,
        calls=dict(calls), protocol_sha256=sha(PROTOCOL_FILE), all_bindings_unchanged=all_bindings_unchanged,
        outputs=outputs, elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak,
        helper_seconds=ARGS.time_limit, sampled_RSS_limit_bytes=CONTRACT['sampled_RSS_bytes'],
        new_NPZ_decodes=0, new_gzip_reads=0, new_force_calls=0, new_tangent_calls=0, new_HP_calls=0,
        new_solver_calls=0, new_model_constructions=0, new_plots=0, mechanical_hooks_monitored=False,
        zero_new_mechanics_basis='Pinned stdlib-only public response source and exact pure HF imports; saved JSON/source/raw-media identity association, no archive re-audit or mechanics hooks',
        stop_policy='One approved window; first error stops; no repair,retry,extension or force')


def main():
    OUTPUT.mkdir(parents=True, exist_ok=False)
    outputs = {}
    try:
        outputs = run()
        write(OUTPUT/'execution_receipt.json', receipt('pass', outputs))
        checkpoint()
        print(json.dumps(dict(status='pass', calls=calls)), flush=True)
    except BaseException as error:
        # A final resource boundary can fail after receipt creation; retain the
        # actual not-pass terminal record rather than the provisional pass.
        outputs = {path.name:sha(path) for path in OUTPUT.iterdir() if path.name != 'execution_receipt.json' and path.is_file()}
        (OUTPUT/'execution_receipt.json').write_text(json.dumps(receipt('not_pass', outputs, repr(error)),
            ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
