"""Freeze the closed outputs and explicit M-AREF1 publication delta."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = 'e687bdf1ca60edbd0fd044f4f8c990b3b9ccc182'
REL = 'lf_data_preparation/native_interface_001/alpha_reference_001'
STAGE = ROOT / REL
CONFIG = REL + '/author/execution_delivery_config.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
read = lambda path: json.loads(path.read_bytes())


def sha(path):
    value = sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def new_bytes(path, raw):
    with path.open('xb') as output:
        output.write(raw)


def main():
    git = lambda *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)
    assert git('rev-parse', 'HEAD').decode().strip() == BASE and not (ROOT / CONFIG).exists()
    oldraw = git('show', BASE + ':handoff/repository_manifest.json')
    assert (ROOT / 'handoff/repository_manifest.json').read_bytes() == oldraw
    previous = {row['path']: row for row in json.loads(oldraw)['files']}
    outer = read(STAGE / 'reference_launch.json')
    helper = read(STAGE / 'run_001/reference/lifecycle.json')
    summary = read(STAGE / 'run_001/reference/summary.json')
    assert outer['status'] == helper['status'] == summary['status'] == 'pass'
    assert outer['exit_code'] == 0 and outer['invocations'] == 1 and outer['completed_utc']
    assert outer['all_bindings_unchanged'] is True and outer['stop_reason'] is None
    assert helper['HP_calls_started'] == helper['HP_calls_completed'] == summary['HP_calls_completed'] == 4
    assert helper['accepted_mechanical_states_completed'] == helper['workpiece_states_completed'] == summary['accepted_states'] == 2
    reviews = ('execution_terminal_review.json', 'actual_input_and_index_review.json',
               'execution_documentation_review.json', 'delivery_tool_static_review.json')
    for name in reviews:
        review = read(HERE / name)
        assert review['status'].startswith('pass') and review['execution_status'] == 'pass'
    files = ('EXECUTION_TERMINAL_REVIEW.md', 'execution_terminal_review.json',
        'ACTUAL_INPUT_AND_INDEX_REVIEW.md', 'actual_input_and_index_review.json',
        'TERMINAL_REVIEW_PLAN.md', 'EXECUTION_DOCUMENTATION_REVIEW.md', 'execution_documentation_review.json',
        'DELIVERY_TOOL_STATIC_REVIEW.md', 'delivery_tool_static_review.json',
        'DELIVERY_TOOL_INTERFACE.md', 'delivery_tool_author_receipt.json',
        'archive_authorization.py', 'deliver_execution.py', 'write_execution_documentation.py',
        'configure_execution_delivery.py', 'write_execution_terminal_review.py')
    for name in files:
        new_bytes(STAGE / 'author' / name, (HERE / name).read_bytes())
    history = read(STAGE / 'author/execution_documentation_receipt.json')['front_history']
    assert {row['path'] for row in history} == FRONTS
    for row in history:
        prior = git('show', BASE + ':' + row['path'])
        current = (ROOT / row['path']).read_bytes()
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha(ROOT / row['path']) == row['new_sha256']
    run_files = {path.relative_to(ROOT).as_posix(): sha(path) for path in (STAGE / 'run_001').rglob('*') if path.is_file()}
    assert len(run_files) == 39
    closed = dict(run_files)
    for name in ('reference_launch.json', 'reference_stdout.log',
                 'author/authorization.json', 'author/direct_human_reply.json', 'author/source_publication_receipt.json'):
        closed[REL + '/' + name] = sha(STAGE / name)
    stage_names = {path.relative_to(ROOT).as_posix() for path in STAGE.rglob('*') if path.is_file()}
    old_stage = {name for name in previous if name.startswith(REL + '/')}
    assert len(old_stage) == 24 and old_stage <= stage_names
    assert all(sha(ROOT / name) == previous[name]['sha256'] for name in old_stage)
    changed_old = {name.decode() for name in git('diff', '--name-only', '-z').split(b'\0') if name}
    assert changed_old == FRONTS
    allowed = (stage_names - previous.keys()) | FRONTS | {CONFIG}
    proof = REL + '/author/source_publication_receipt.json'
    value = dict(source_commit=BASE, executed_card='M-AREF1', authorized=True, executed=True,
        execution_closed=True, execution_status='pass', protocol_sha256=sha(STAGE / 'protocol.json'),
        allowed_delta_paths=sorted(allowed), front_history=history,
        closed_output_SHA256=dict(sorted(closed.items())), closed_run_files=len(run_files),
        previous_publication_receipt=dict(path=proof, sha256=sha(ROOT / proof)),
        terminal_review_paths=[REL + '/author/' + name for name in reviews], final_review_path=None,
        inherited_input_NPZ_not_raw_reread=10, new_archive_NPZ_hash_scope='Raw file identity for publication only; no decode',
        new_HF_F_T_HP_solver_tests_API_plot_calls=0, full_source_scan=False)
    new_bytes(ROOT / CONFIG, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8'))
    print(json.dumps(dict(status='closed_execution_delivery_configured', allowed_delta_files=len(allowed),
        run_files=len(run_files), closed_files=len(closed), config_sha256=sha(ROOT / CONFIG)), ensure_ascii=False))


if __name__ == '__main__':
    main()
