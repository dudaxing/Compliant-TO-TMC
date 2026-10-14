"""L-LINK1: finite metadata tests, one public association, then one-file installation."""
from time import perf_counter
STARTED = perf_counter()
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
import psutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--protocol', type=Path, required=True)
parser.add_argument('--time-limit', type=float, required=True)
ARGS = parser.parse_args()
ROOT, PROTOCOL_FILE = ARGS.repo.resolve(), ARGS.protocol.resolve()
STAGE = PROTOCOL_FILE.parent
read = lambda path: json.loads(path.read_bytes())
CONTRACT = read(PROTOCOL_FILE)
OUTPUT = ROOT/CONTRACT['output_directory']
PROCESS, peak = psutil.Process(), 0
calls = dict(tests_started=0, tests_completed=0, saved_summary_started=0,
    saved_summary_completed=0, response_writes=0, index_writes=0,
    installation_started=0, installation_completed=0)
unit_tests_run, unit_reference_calls = 0, 0
all_bindings_unchanged, installation_complete = False, False


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def checkpoint():
    global peak
    peak = max(peak, PROCESS.memory_info().rss)
    if (perf_counter()-STARTED > ARGS.time_limit or peak > CONTRACT['sampled_RSS_bytes']
            or (STAGE/'stop_requested.txt').exists()):
        raise RuntimeError('L-LINK1 cooperative resource/stop boundary reached')


def verify_bindings():
    for name, pin in CONTRACT['bindings'].items():
        checkpoint()
        if Path(name).suffix.lower() not in {'.py','.json','.md','.png','.gif'}:
            raise ValueError('Scientific archive is outside L-LINK1 input scope: '+name)
        if sha(ROOT/name) != pin:
            raise ValueError('Immutable artifact changed: '+name)
    checkpoint()


def authorize():
    auth = read(STAGE/'author/authorization.json')
    reply_file, proof_file = STAGE/'author/direct_human_reply.json', STAGE/'author/source_publication_receipt.json'
    reply, proof = read(reply_file), read(proof_file)
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    if not (CONTRACT['schema_version'] == 'lf-selected-reference-linked-delivery-card-1.0'
            and CONTRACT['card'] == auth['card'] == reply['card'] == proof['prepared_card'] == 'L-LINK1'
            and CONTRACT['prepared'] is True and CONTRACT['authorized'] is CONTRACT['executed'] is False
            and auth['authorized'] is True and auth['one_invocation'] is True
            and auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
            and auth['protocol_sha256'] == proof['protocol_sha256'] == sha(PROTOCOL_FILE)
            and auth['authorized_execution_source_commit'] == reply['authorized_execution_source_commit'] == proof['published_commit'] == head
            and auth['human_evidence_sha256'] == sha(reply_file)
            and auth['source_publication_receipt_sha256'] == sha(proof_file)
            and auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip()
            and reply['reply_context'] and proof['status'] == 'published_and_incrementally_restored_pass'
            and ARGS.time_limit == auth['helper_seconds'] == CONTRACT['phases']['link']['helper_seconds'] == 180
            and auth['outer_seconds'] == CONTRACT['phases']['link']['outer_seconds'] == 240
            and CONTRACT['phases']['link']['tests_seconds'] == 60
            and auth['sampled_RSS_bytes'] == CONTRACT['sampled_RSS_bytes'] == 8*1024**3):
        raise ValueError('L-LINK1 requires direct approval of its actual published source and unchanged card')
    return proof['published_commit']


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ValueError('Imported source origin differs: '+name)
    return module


def run_tests(response_module):
    global unit_tests_run, unit_reference_calls
    tests = load('_l_link_metadata_tests', ROOT/CONTRACT['tests_source'])
    started = perf_counter()
    def tests_checkpoint():
        checkpoint()
        if perf_counter()-started > CONTRACT['phases']['link']['tests_seconds']:
            raise RuntimeError('L-LINK1 finite metadata test boundary reached')
    tests.RESPONSE, tests.FIXTURE_ROOT, tests.CHECKPOINT = response_module, OUTPUT/'tests', tests_checkpoint
    class BoundedResult(unittest.TextTestResult):
        def startTest(self, test):
            global unit_tests_run
            tests_checkpoint()
            super().startTest(test)
            unit_tests_run = self.testsRun

        def stopTest(self, test):
            global unit_reference_calls
            unit_reference_calls = tests.REFERENCE_CALLS
            super().stopTest(test)
            tests_checkpoint()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(tests.SelectedReferenceTests)
    names = [test._testMethodName for test in suite]
    if names != CONTRACT['expected_test_methods'] or len(names) != 16:
        raise ValueError('Frozen sixteen metadata tests differ')
    tests_checkpoint(); calls['tests_started'] += 1
    with (OUTPUT/'tests_stdout.txt').open('x', encoding='utf-8') as stream:
        try:
            result = unittest.TextTestRunner(stream=stream, verbosity=2, failfast=True,
                resultclass=BoundedResult).run(suite)
        finally:
            unit_reference_calls = tests.REFERENCE_CALLS
    unit_tests_run, unit_reference_calls = result.testsRun, tests.REFERENCE_CALLS
    tests_checkpoint()
    if not result.wasSuccessful() or result.testsRun != 16 or unit_reference_calls != 23:
        raise RuntimeError('L-LINK1 metadata tests failed; no association or installation')
    calls['tests_completed'] += 1
    write(OUTPUT/'tests_summary.json', dict(status='pass', test_methods=names,
        unit_tests_run=unit_tests_run, unit_reference_calls=unit_reference_calls,
        elapsed_seconds=perf_counter()-started, failfast=True,
        scope='Sixteen unit methods using ordinary JSON/source fixtures and _reference; no public summary call or scientific/media fixture'))


def artifact(name):
    return dict(path=name, path_scope='repo_relative', sha256=CONTRACT['bindings'][name])


def verify_response(response):
    reference, path, views = (response[name] for name in ('independent_reference','path','views'))
    if not (response['status'] == 'success' and response['failure'] is None
            and path['completed'] is True and path['accepted_states'] == CONTRACT['production_accepted_states'] == 25
            and reference['status'] == 'matched_partial' and reference['selected_reference_pass'] is True
            and reference['source_bindings_verified'] is True
            and reference['matched_state_indices'] == CONTRACT['selected_accepted_indices'] == [13,16]
            and reference['matched_state_count'] == CONTRACT['expected_reference_states'] == 2
            and reference['production_accepted_state_count'] == 25 and reference['HP_calls_completed'] == 4
            and reference['covers_all_accepted_states'] is reference['accepted_reference_pass'] is reference['full_path_reference_pass'] is False
            and all(reference[key] is False for key in ('HP_all_columns_qualified','contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified'))
            and views['status'] == 'matched' and views['case_label'] == 'lf_fine_forward'
            and len(views['links']) == 4 and sorted(link['kind'] for link in views['links']) == ['gif','png','png','png']
            and sorted(link['path'] for link in views['links']) == sorted(
                name for name in CONTRACT['inherited_media_bindings'] if name != CONTRACT['reference_observation_media_file'])
            and all(value is False for value in response['producer_flags'].values())):
        raise ValueError('Actual production/reference/view coverage differs; association cannot upgrade qualification')
    original = read(ROOT/CONTRACT['original_response_file'])
    if any(original.get(key) != value for key, value in response.items()
            if key not in {'independent_reference','views'}):
        raise ValueError('Ordinary original response physics, values or production metadata changed')
    result = read(ROOT/CONTRACT['result_file'])
    for index, target in zip(CONTRACT['selected_accepted_indices'], CONTRACT['targets_mm']):
        if result['states'][index]['d'] != target or result['states'][index]['original_target_index'] != index:
            raise ValueError('Selected production state index/target differs')
    checkpoint()


def run():
    global all_bindings_unchanged, installation_complete
    checkpoint(); verify_bindings()
    before = CONTRACT['source_before_installation']
    if before['path'] != 'hf_repo/src/hf_eval/native_response.py' or sha(ROOT/before['path']) != before['sha256']:
        raise ValueError('Default response source differs before approved installation')
    producer, reference_execution = (read(ROOT/CONTRACT[name]) for name in
        ('production_receipt_file','reference_execution_receipt_file'))
    if not (producer['status'] == reference_execution['status'] == 'pass'
            and producer['output_identity_seal'] == reference_execution['output_identity_seal'] == 'complete_inside_original_helper_window'
            and producer['accepted_states'] == 25
            and reference_execution['selected_accepted_indices'] == [13,16]
            and reference_execution['HP_calls_started'] == reference_execution['HP_calls_completed'] == 4):
        raise ValueError('Original closed production/reference evidence differs')
    if len(CONTRACT['inherited_media_bindings']) != 5:
        raise ValueError('Exactly five inherited media identities are required')
    for name, identity in CONTRACT['inherited_media_bindings'].items():
        record = producer['outputs'].get(name, reference_execution['outputs'].get(name))
        if (record != identity or identity['sha256'] != CONTRACT['bindings'][name]
                or (ROOT/name).stat().st_size != identity['bytes']):
            raise ValueError('Inherited producer media seal differs: '+name)
    sys.path.insert(0, str(ROOT/'hf_repo/src'))
    import hf_eval
    if Path(hf_eval.__file__).resolve() != ROOT/'hf_repo/src/hf_eval/__init__.py':
        raise ValueError('Pure canonical hf_eval package origin differs')
    response_module = load('hf_eval.native_response', ROOT/CONTRACT['candidate_source'])
    run_tests(response_module); checkpoint()
    calls['saved_summary_started'] += 1
    response = response_module.summarize_saved_native_result(CONTRACT['result_file'], repo_root=ROOT,
        reference_file=CONTRACT['reference_file'], view_manifest=CONTRACT['raw_view_file'])
    calls['saved_summary_completed'] += 1
    verify_response(response)
    linked = OUTPUT/'linked_response.json'
    response_module.write_native_response(response, linked); calls['response_writes'] += 1
    checkpoint()
    images = response['views']['links']+[dict(artifact(CONTRACT['reference_observation_media_file']), kind='png',
        scope='Existing two-selected-state reference error observation; not a production deformation image')]
    index = dict(schema_version='lf-selected-reference-linked-index-1.0', status='pass',
        linked_response=dict(path=linked.relative_to(ROOT).as_posix(), path_scope='repo_relative', sha256=sha(linked)),
        saved_artifacts={key:artifact(CONTRACT[key]) for key in ('result_file','model_file','original_response_file',
            'reference_file','raw_view_file','view_case_summary_file','reference_observation_file',
            'production_receipt_file','reference_execution_receipt_file')},
        images=images, physics=response['physics'], options=response['options'], path=response['path'],
        maximum_loading_stroke=response['maximum_loading_stroke'], requested_endpoint_response=response['requested_endpoint_response'],
        target_response=response['target_response'], independent_reference=response['independent_reference'],
        views=response['views'], source_flags=response['producer_flags'], force_semantics=response['force_semantics'],
        field_scope=response['field_scope'], production_accepted_states=25, selected_accepted_indices=[13,16],
        original_target_indices=CONTRACT['original_target_indices'], selected_targets_mm=CONTRACT['targets_mm'],
        qualification='Existing same25-state production completed; only indices13/16 have matched independent reference. No full25 reference/all-column/pressure/effective-clamp/release/stability/HF5 qualification.',
        path_basis='All artifact and five image links are relative to the restored repository root; images are raw-identity associated without decoding or redrawing')
    write(OUTPUT/'light_index.json', index); calls['index_writes'] += 1
    if {name for name in sys.modules if name == 'hf_eval' or name.startswith('hf_eval.')} != {'hf_eval','hf_eval.native_response'}:
        raise ValueError('Unexpected mechanical HF module imported')
    verify_bindings(); all_bindings_unchanged = True
    if sha(ROOT/before['path']) != before['sha256']:
        raise ValueError('Default source changed before approved installation')
    checkpoint(); calls['installation_started'] += 1
    (ROOT/before['path']).write_bytes((ROOT/CONTRACT['candidate_source']).read_bytes())
    if sha(ROOT/before['path']) != CONTRACT['bindings'][CONTRACT['candidate_source']]:
        raise ValueError('Installed default source differs from tested candidate; actual bytes retained')
    calls['installation_completed'] += 1; installation_complete = True
    checkpoint(); verify_bindings()


def seal_outputs():
    outputs = {}
    for path in sorted(OUTPUT.rglob('*')):
        if path.is_file() and path.name != 'execution_receipt.json':
            checkpoint()
            outputs[path.relative_to(ROOT).as_posix()] = dict(sha256=sha(path), bytes=path.stat().st_size)
    checkpoint()
    return outputs


def receipt(status, outputs, seal, source_commit, error=None):
    before = CONTRACT['source_before_installation']
    return dict(schema_version='L-LINK1-selected-reference-linked-execution-1.0', card='L-LINK1',
        status=status, error=error, calls=dict(calls), unit_tests_run=unit_tests_run,
        unit_reference_calls=unit_reference_calls, protocol_sha256=sha(PROTOCOL_FILE),
        authorized_execution_source_commit=source_commit, all_bindings_unchanged=all_bindings_unchanged,
        installation_complete=installation_complete, installed_file=before['path'],
        actual_default_SHA256=sha(ROOT/before['path']), candidate_SHA256=CONTRACT['bindings'][CONTRACT['candidate_source']],
        outputs=outputs, output_identity_seal=seal, elapsed_seconds=perf_counter()-STARTED,
        sampled_peak_RSS_bytes=peak, helper_seconds=ARGS.time_limit,
        sampled_RSS_limit_bytes=CONTRACT['sampled_RSS_bytes'],
        new_NPZ_reads=0, new_gzip_reads=0, new_CSV_reads=0, media_decodes=0, new_plots=0,
        new_force_calls=0, new_tangent_calls=0, new_HP_calls=0, new_solver_calls=0, new_model_constructions=0,
        mechanical_hooks_monitored=False,
        zero_new_mechanics_basis='Pinned stdlib-only response/test sources; pure hf_eval package and response module only; ordinary metadata and raw-media identity association, no archive re-audit',
        call_scope='Sixteen _reference unit methods have their own unit_reference_calls; one separate real summarize_saved_native_result invocation',
        stop_policy='One approved window; first error stops; no repair,retry,extension,force,rollback or deletion')


def main():
    source_commit = authorize()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    outputs, seal = {}, 'not_complete'
    try:
        run(); outputs = seal_outputs(); seal = 'complete_inside_original_helper_window'
        write(OUTPUT/'execution_receipt.json', receipt('pass', outputs, seal, source_commit))
        checkpoint()
        print(json.dumps(dict(status='pass', calls=calls, unit_tests_run=unit_tests_run)), flush=True)
    except BaseException as error:
        if perf_counter()-STARTED <= ARGS.time_limit and not (STAGE/'stop_requested.txt').exists():
            try:
                outputs = seal_outputs(); seal = 'actual_partial_inside_original_helper_window'
            except BaseException:
                seal = 'partial_not_complete_before_resource_close'
        else:
            seal = 'not_supplemented_after_resource_close'
        (OUTPUT/'execution_receipt.json').write_text(json.dumps(
            receipt('not_pass', outputs, seal, source_commit, dict(type=type(error).__name__, message=str(error))),
            ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
