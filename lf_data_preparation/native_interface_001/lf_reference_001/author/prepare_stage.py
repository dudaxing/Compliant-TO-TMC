"""Prepare ordinary L-REF1 sources; inherit scientific identities with stat only."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = 'b5a59417fe58989922a6ba42993708917fecafe1'
REL = 'lf_data_preparation/native_interface_001/lf_reference_001'
OLD_MANIFEST = '6543470760c73c6f18dfa7258822e57644da132dc85195743e8994ac9d6f7d86'
PRIOR = Path('D:/hf-native-workpiece-api-author-20261014/LF_FORWARD_execution_publication_001')
ORDINARY = {'.json', '.md', '.py', '.toml'}

def raw(path):
    assert path.suffix.lower() in ORDINARY
    return path.read_bytes()

def pin(path):
    return sha256(raw(path)).hexdigest()

def read(path):
    return json.loads(raw(path))

def dump(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)

def main():
    stage = ROOT / REL
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert git('branch', '--show-current').decode().strip() == 'main'
    assert git('remote', 'get-url', 'origin').decode().strip() == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    assert not git('status', '--porcelain') and not stage.exists()
    manifest_raw = raw(ROOT / 'handoff/repository_manifest.json')
    assert sha256(manifest_raw).hexdigest() == OLD_MANIFEST
    manifest = json.loads(manifest_raw)
    old = {row['path']: row for row in manifest['files']}
    assert len(old) == 20423 and sum(row['bytes'] for row in old.values()) == 11141402568
    prior = read(PRIOR / 'execution_publication_receipt.json')
    assert prior['published_commit'] == BASE and prior['manifest_sha256'] == OLD_MANIFEST
    assert prior['status'] == 'published_and_incrementally_restored_pass'
    assert prior['executed_card'] == 'L-FWD1' and prior['execution_closed'] is True and prior['execution_status'] == 'pass'
    seed = read(HERE / 'input_contract_seed.json')
    assert seed['card'] == 'L-REF1' and seed['source_baseline_commit'] == BASE and seed['protocol_seed_only'] is True
    assert seed['selected_accepted_indices'] == seed['original_target_indices'] == [13, 16]
    assert seed['production_path_completed'] is True and seed['full_production_path_reference_pass'] is False
    closed = read(ROOT / 'lf_data_preparation/native_interface_001/lf_forward_001/run_001/execution_receipt.json')
    assert closed['status'] == 'pass' and closed['last_phase'] == 'closure'
    assert closed['output_identity_seal'] == 'complete_inside_original_helper_window'
    for name, entry in seed['inherited_NPZ_bindings'].items():
        assert old[name]['sha256'] == entry['sha256'] == closed['outputs'][name]['sha256']
        assert old[name]['bytes'] == entry['bytes'] == closed['outputs'][name]['bytes'] == (ROOT / name).stat().st_size
    author_names = [
        'input_contract_seed.json', 'input_scope_review.json', 'INPUT_SCOPE_REVIEW.md',
        'source_author_receipt.json', 'SOURCE_AUTHOR_NOTES.md',
        'physical_math_scope_review.json', 'physical_math_scope_review.md',
        'COST_SCOPE_AUDIT.json', 'COST_SCOPE_AUDIT.md',
        'candidate_math_source_review.json', 'candidate_math_source_review.md',
        'publisher_source.py', 'PUBLISHER_SOURCE_NOTES.md', 'publisher_source_author_receipt.json',
        'publisher_source_review.json', 'publisher_source_review.md', 'prepare_stage.py', 'front_prefix.md',
        'prepare_stage_v1_missing_reference_sources.py', 'prepare_stage_source_revision.json',
    ]
    files = {name: name for name in ('execute_partial_reference.py', 'launch_reference.py',
        'plot_partial_reference_observation.py', 'L-REF1_CARD.md', 'PREPARATION_RESULTS.md')}
    files.update({'author/' + name: name for name in author_names})
    for name in files.values():
        assert (HERE / name).is_file(), name
        if Path(name).suffix == '.py':
            ast.parse(raw(HERE / name).decode('utf-8-sig'))
    for name in ('candidate_math_source_review.json', 'publisher_source_review.json'):
        review = read(HERE / name)
        assert review['status'].startswith('pass') and not review['blocking_findings']
    for name, expected in seed['bindings'].items():
        if name.startswith(REL + '/'):
            assert pin(HERE / Path(name).name) == expected
        elif name in seed['inherited_NPZ_bindings']:
            assert old[name]['sha256'] == expected
        else:
            assert pin(ROOT / name) == old[name]['sha256'] == expected
    stage.mkdir(parents=True)
    for relative, name in files.items():
        path = stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw(HERE / name))
    assert len(seed['reference_sources']) == len({Path(name).name for name in seed['reference_sources']}) == 11
    for name, expected in seed['reference_sources'].items():
        assert pin(ROOT / name) == expected
        relative = 'reference_sources/' + Path(name).name
        path = stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw(ROOT / name))
    for old_name, new_name in (
        ('execution_publication_receipt.json', 'previous_execution_publication_receipt.json'),
        ('root_execution_publication_terminal_confirmation.json', 'previous_root_publication_confirmation.json')):
        with (stage / 'author' / new_name).open('xb') as stream:
            stream.write(raw(PRIOR / old_name))
    protocol = dict(seed, protocol_seed_only=False, installed=False,
        created_utc=datetime.now(timezone.utc).isoformat(),
        origin='https://github.com/dudaxing/Compliant-TO-TMC.git',
        expected_default_changes=0, expected_tests=0, external_retries=0,
        repair_rerun_allowed=False, extension_allowed=False, force_allowed=False)
    protocol['phases']['reference']['argv'] = [REL + '/execute_partial_reference.py', '--repo', '.',
        '--input', seed['production_stage'], '--output', seed['reference_output'],
        '--protocol', REL + '/protocol.json', '--time-limit', '900']
    protocol['bindings'] = dict(seed['bindings'])
    for relative in files:
        protocol['bindings'][REL + '/' + relative] = pin(stage / relative)
    for name, expected in seed['reference_sources'].items():
        protocol['bindings'][REL + '/reference_sources/' + Path(name).name] = expected
    dump(stage / 'protocol.json', protocol)
    histories = []
    prefix = raw(HERE / 'front_prefix.md')
    for name in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
        prior_raw = git('show', BASE + ':' + name)
        assert raw(ROOT / name) == prior_raw
        current = prefix + prior_raw
        assert current.count(prior_raw) == 1
        (ROOT / name).write_bytes(current)
        histories.append(dict(path=name, old_sha256=sha256(prior_raw).hexdigest(),
            new_sha256=sha256(current).hexdigest(), history_start_byte=len(prefix),
            history_end_byte_exclusive=len(current), old_raw_contiguous_once=True))
    artifacts = {path.relative_to(ROOT).as_posix(): pin(path) for path in sorted(stage.rglob('*')) if path.is_file()}
    receipt = dict(card='L-REF1', status='source_prepared_not_executed', source_baseline_commit=BASE,
        prepared=True, authorized=False, executed=False, installed=False, artifact_SHA256=artifacts,
        front_history=histories, protocol_sha256=pin(stage / 'protocol.json'), default_runtime_changes=0,
        scientific_or_media_byte_reads_hashes_headers_decode=0, new_HF_API_tests_plots_solver_force_tangent_HP=0)
    dump(stage / 'author/preparation_receipt.json', receipt)
    dump(HERE / 'preparation_write_receipt.json', dict(status='ordinary_stage_write_pass', stage=REL,
        protocol_sha256=receipt['protocol_sha256'], source_baseline_commit=BASE, new_stage_files=len(artifacts) + 1,
        modified_fronts=2, scientific_bytes_read=False, runtime_executed=False))
    print(json.dumps(dict(status=receipt['status'], stage=REL, files=len(artifacts) + 1, protocol_sha256=receipt['protocol_sha256'])))

if __name__ == '__main__':
    main()
