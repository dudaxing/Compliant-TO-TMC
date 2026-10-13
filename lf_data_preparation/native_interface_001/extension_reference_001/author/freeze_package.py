"""Freeze ordinary M-EREF1 sources and inherited input identities; no science import."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/extension_reference_001'
BASE = '43e3ba7f981b2dc44fa84bc7e78b8f5d9e106bdf'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(source.read_bytes())


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASE
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
    packet = HERE / 'frozen_packet'
    packet.mkdir()
    files = ('execute_extension_reference.py', 'launch_reference.py', 'plot_reference_observation.py',
             'M-EREF1_CARD.md', 'PREPARATION_RESULTS.md')
    for name in files:
        copy(HERE / name, packet / name)
    author = ('SOURCE_AUTHOR_NOTES.md', 'source_author_receipt.json', 'input_contract_seed.json',
              'SOURCE_DIFF.patch', 'adapt_reference_sources.py', 'single_state_reference_source_audit.json',
              'SINGLE_STATE_REFERENCE_SOURCE_AUDIT.md')
    for name in author:
        copy(HERE / name, packet / 'author' / name)
    copy(HERE / 'front_prefix.md', packet / 'author/front_prefix.md')
    proof_file = Path('D:/hf-native-workpiece-api-author-20261012/MEXTEND2_execution_review_001/execution_publication_receipt.json')
    proof = read(proof_file)
    assert proof['published_commit'] == BASE and proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    copy(proof_file, packet / 'author/previous_publication_receipt.json')
    contract = read(HERE / 'input_contract_seed.json')
    assert contract['source_baseline_commit'] == BASE and contract['card'] == 'M-EREF1'
    bindings = dict(contract['ordinary_source_input_bindings'])
    entries = {row['path']: row for row in read(ROOT / 'handoff/repository_manifest.json')['files']}
    for name, pin in bindings.items():
        assert entries[name]['sha256'] == pin == sha(ROOT / name)
    for name, identity in contract['inherited_NPZ_bindings'].items():
        assert identity['sha256'] == entries[name]['sha256'] and (ROOT / name).stat().st_size == entries[name]['bytes']
        bindings[name] = identity['sha256']
    for path in packet.rglob('*'):
        if path.is_file():
            bindings[REL + '/' + path.relative_to(packet).as_posix()] = sha(path)
    contract.update(prepared=True, authorized=False, executed=False,
        prepared_utc=datetime.now(timezone.utc).isoformat(), bindings=bindings,
        new_production_F_T_model_solver_tests=0, new_reference_observation_plots=1,
        postrun_new_PNG_pixel_QA_maximum=1, no_postrun_science_array_or_gzip_decode=True,
        prerequisite='New direct human approval of this published/restored card and 900/960-second window')
    contract.pop('new_production_F_T_model_solver_tests_plots', None)
    with (packet / 'protocol.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(contract, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    receipt = dict(status='frozen_source_preparation_not_executed', card='M-EREF1', source_baseline_commit=BASE,
        prepared=True, authorized=False, executed=False, protocol_SHA256=sha(packet / 'protocol.json'),
        artifact_SHA256={path.relative_to(packet).as_posix(): sha(path) for path in packet.rglob('*') if path.is_file()},
        expected_HP_calls=2, expected_plots=1, immutable_bindings=len(bindings), inherited_NPZ_stat_only=6,
        default_changes=0, new_HF_import_tests_science_arrays_gzip_media_pixels_or_plots=0)
    with (HERE / 'frozen_preparation_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'artifact_SHA256'}))


if __name__ == '__main__':
    main()
