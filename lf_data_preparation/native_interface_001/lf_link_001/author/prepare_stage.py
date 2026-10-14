"""Prepare L-LINK1 ordinary sources only; preserve closed media identity with stat."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = '909f8acee95279e449e09961fd4fe68fed9d688f'
REL = 'lf_data_preparation/native_interface_001/lf_link_001'
PRIOR = Path('D:/hf-native-workpiece-api-author-20261014/LF_REFERENCE_execution_001')
MANIFEST_SHA = 'aaa13ff53e966d3b18296a0199a4e5fc889bfd238af48f551b85964a8cf1f6b3'
ORDINARY = {'.json', '.md', '.py', '.toml'}


def raw(path):
    assert path.suffix.lower() in ORDINARY
    return path.read_bytes()


def sha(path):
    return sha256(raw(path)).hexdigest()


def read(path):
    return json.loads(raw(path))


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)


def main():
    stage = ROOT / REL
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert git('branch', '--show-current').decode().strip() == 'main'
    assert git('remote', 'get-url', '--push', 'origin').decode().strip() == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    assert not git('status', '--porcelain') and not stage.exists()
    old_raw = raw(ROOT / 'handoff/repository_manifest.json')
    assert sha256(old_raw).hexdigest() == MANIFEST_SHA
    old_manifest = json.loads(old_raw)
    old = {row['path']: row for row in old_manifest['files']}
    assert len(old) == 20536 and sum(row['bytes'] for row in old.values()) == 11309928280
    prior = read(PRIOR / 'execution_publication_receipt.json')
    assert prior['status'] == 'published_and_incrementally_restored_pass'
    assert prior['published_commit'] == BASE and prior['manifest_sha256'] == MANIFEST_SHA
    assert prior['executed_card'] == 'L-REF1' and prior['execution_closed'] is True and prior['execution_status'] == 'pass'
    seed = read(HERE / 'input_contract_seed.json')
    assert seed['card'] == 'L-LINK1' and seed['source_baseline_commit'] == BASE and seed['protocol_seed_only'] is True
    assert seed['selected_accepted_indices'] == seed['original_target_indices'] == [13, 16]
    assert seed['production_accepted_states'] == 25 and seed['expected_reference_states'] == 2
    before = seed['source_before_installation']
    assert sha(ROOT / before['path']) == before['sha256'] == old[before['path']]['sha256']
    assert before['path'] not in seed['bindings']
    sealed = {}
    for key in ('production_receipt_file', 'reference_execution_receipt_file'):
        receipt = read(ROOT / seed[key])
        assert receipt['status'] == 'pass' and receipt['output_identity_seal'] == 'complete_inside_original_helper_window'
        sealed.update(receipt['outputs'])
    assert len(seed['inherited_media_bindings']) == 5
    for name, record in seed['inherited_media_bindings'].items():
        assert set(record) == {'sha256', 'bytes'}
        assert record['sha256'] == old[name]['sha256'] == sealed[name]['sha256'] == seed['bindings'][name]
        assert record['bytes'] == old[name]['bytes'] == sealed[name]['bytes'] == (ROOT / name).stat().st_size
    files = read(HERE / 'file_plan.json')['files']
    for relative, name in files.items():
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        source = HERE / name
        assert source.is_file()
        if source.suffix == '.py':
            ast.parse(raw(source).decode('utf-8-sig'))
    for name in ('candidate_api_source_review.json', 'candidate_contract_source_review.json', 'publisher_source_review.json'):
        review = read(HERE / name)
        assert str(review['status']).startswith('pass') and review['blocking_findings'] == []
    for name, expected in seed['bindings'].items():
        if name.startswith(REL + '/'):
            relative = name[len(REL) + 1:]
            assert sha(HERE / files[relative]) == expected
        elif name in seed['inherited_media_bindings']:
            assert old[name]['sha256'] == expected
        else:
            assert sha(ROOT / name) == old[name]['sha256'] == expected
    stage.mkdir(parents=True)
    for relative, name in files.items():
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw(HERE / name))
    for old_name, new_name in (
        ('execution_publication_receipt.json', 'previous_publication_receipt.json'),
        ('root_execution_publication_terminal_confirmation.json', 'previous_root_terminal_confirmation.json')):
        with (stage / 'author' / new_name).open('xb') as stream:
            stream.write(raw(PRIOR / old_name))
    protocol = dict(seed, protocol_seed_only=False, installed=False, prepared=True, authorized=False, executed=False,
        created_utc=datetime.now(timezone.utc).isoformat(), origin='https://github.com/dudaxing/Compliant-TO-TMC.git')
    protocol['bindings'] = dict(seed['bindings'])
    for relative in files:
        protocol['bindings'][REL + '/' + relative] = sha(stage / relative)
    for name in ('previous_publication_receipt.json', 'previous_root_terminal_confirmation.json'):
        protocol['bindings'][REL + '/author/' + name] = sha(stage / 'author' / name)
    write_new(stage / 'protocol.json', protocol)
    prefix = raw(HERE / 'front_prefix.md')
    histories = []
    for name in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
        original = git('show', BASE + ':' + name)
        assert raw(ROOT / name) == original
        current = prefix + original
        assert current.count(original) == 1
        (ROOT / name).write_bytes(current)
        histories.append(dict(path=name, old_sha256=sha256(original).hexdigest(), new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix), history_end_byte_exclusive=len(current), old_raw_contiguous_once=True))
    artifacts = {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(stage.rglob('*')) if path.is_file()}
    receipt = dict(card='L-LINK1', status='source_prepared_not_executed', source_baseline_commit=BASE,
        prepared=True, authorized=False, executed=False, installed=False, artifact_SHA256=artifacts,
        front_history=histories, protocol_sha256=sha(stage / 'protocol.json'), default_runtime_changes=0,
        scientific_or_media_byte_reads_hashes_headers_decode=0, new_HF_API_tests_plots_solver_force_tangent_HP=0)
    write_new(stage / 'author' / 'source_preparation_receipt.json', receipt)
    write_new(HERE / 'preparation_write_receipt.json', dict(status='ordinary_source_preparation_pass',
        source_baseline_commit=BASE, stage=REL, protocol_sha256=receipt['protocol_sha256'],
        stage_files_written=len(artifacts) + 1, modified_fronts=2, scientific_content_read=False, runtime_executed=False))
    print(json.dumps(dict(status=receipt['status'], stage=REL, files=len(artifacts) + 1, protocol_sha256=receipt['protocol_sha256'])))


if __name__ == '__main__':
    main()
