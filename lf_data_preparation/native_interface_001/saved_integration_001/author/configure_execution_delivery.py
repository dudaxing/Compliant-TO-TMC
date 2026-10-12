"""Freeze closed execution outputs and the small explicit publication delta."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = '2b550d09f4347240ef6cb626b4c829566b638e61'
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
STAGE = ROOT / REL
CONFIG = REL + '/author/execution_delivery_config.json'
FINAL = REL + '/author/execution_final_delivery_review.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md', 'hf_repo/README.md', 'docs/NATIVE_EVALUATION_INTERFACE.md'}
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
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert not (ROOT / CONFIG).exists() and not (ROOT / FINAL).exists()
    old = read(ROOT / 'handoff/repository_manifest.json')
    assert (ROOT / 'handoff/repository_manifest.json').read_bytes() == git('show', BASE + ':handoff/repository_manifest.json')
    previous = {row['path']: row for row in old['files']}
    protocol, outer, helper = (read(STAGE / name) for name in ('protocol.json', 'integration_launch.json', 'run_001/execution_receipt.json'))
    assert outer['status'] == helper['status'] == 'pass' and outer['exit_code'] == 0 and outer['completed_utc']
    assert outer['invocations'] == helper['focused_tests_started'] == helper['focused_tests_completed'] == 1
    assert all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
    assert all(sha(ROOT / name) == pin for name, pin in protocol['installed_runtime_SHA256'].items())
    for name in ('documentation_execution_review.json', 'DOCUMENTATION_EXECUTION_REVIEW.md',
                 'DELIVERY_TOOL_STATIC_REVIEW.json', 'DELIVERY_TOOL_STATIC_REVIEW.md'):
        new_bytes(STAGE / 'author' / name, (HERE / name).read_bytes())
    for path in HERE.glob('*.py'):
        destination = STAGE / 'author' / path.name
        if destination.exists():
            assert sha(destination) == sha(path)
        else:
            new_bytes(destination, path.read_bytes())
    history = read(STAGE / 'author/execution_documentation_receipt.json')['front_history']
    history += read(STAGE / 'author/installed_entry_documentation_receipt.json')['front_history']
    assert len(history) == 4 and {row['path'] for row in history} == FRONTS
    for row in history:
        prior = git('show', BASE + ':' + row['path'])
        current = (ROOT / row['path']).read_bytes()
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha(ROOT / row['path']) == row['new_sha256']
    run_files = {path.relative_to(ROOT).as_posix(): sha(path) for path in (STAGE / 'run_001').rglob('*') if path.is_file()}
    outputs = dict(run_files)
    for name in ('integration_launch.json', 'integration_stdout.log',
                 'author/authorization.json', 'author/direct_human_reply.json', 'author/source_publication_receipt.json'):
        outputs[REL + '/' + name] = sha(STAGE / name)
    stage_names = {path.relative_to(ROOT).as_posix() for path in STAGE.rglob('*') if path.is_file()}
    targets = {row['target'] for row in protocol['installation']}
    changed_old = FRONTS | {row['target'] for row in protocol['installation'] if row['previous_sha256'] is not None}
    assert len(changed_old) == 10
    new_stage = stage_names - previous.keys()
    assert all(sha(ROOT / name) == previous[name]['sha256'] for name in stage_names & previous.keys())
    allowed = new_stage | targets | FRONTS | {CONFIG, FINAL}
    cache = sorted(name for name in run_files if name.startswith(REL + '/run_001/pytest_cache/'))
    assert len(cache) == 4
    value = dict(status='prepared_closed_execution_delivery_configuration', source_commit=BASE,
        executed_card='M-INTEGRATE1', authorized=True, executed=True, execution_status='pass', execution_closed=True,
        protocol_sha256=sha(STAGE / 'protocol.json'), allowed_delta_paths=sorted(allowed), final_review_path=FINAL,
        front_history=history, changed_old_paths=sorted(changed_old), closed_output_SHA256=dict(sorted(outputs.items())),
        closed_run_files=len(run_files), preserved_pytest_cache_paths=cache,
        peer_reviews={REL + '/author/' + name: sha(STAGE / 'author' / name) for name in
            ('execution_terminal_review.json', 'focused_execution_review.json', 'documentation_execution_review.json', 'DELIVERY_TOOL_STATIC_REVIEW.json')},
        default_core_installed=True, new_NPZ_decodes_or_HF_or_tests_or_plots=0, full_source_scan=False)
    new_bytes(ROOT / CONFIG, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    print(json.dumps(dict(status=value['status'], delta_files=len(allowed), run_files=len(run_files), cache_files=len(cache),
        config_sha256=sha(ROOT / CONFIG), changed_old_files=len(changed_old)), ensure_ascii=False))


if __name__ == '__main__':
    main()
