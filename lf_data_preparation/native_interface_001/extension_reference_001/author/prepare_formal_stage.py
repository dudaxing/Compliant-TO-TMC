"""Save reviewed ordinary reference preparation and preserve complete front history."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/extension_reference_001'
BASE = '43e3ba7f981b2dc44fa84bc7e78b8f5d9e106bdf'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(source.read_bytes())


def main():
    git = lambda *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)
    assert git('rev-parse', 'HEAD').decode().strip() == BASE and not git('status', '--porcelain')
    stage, packet = ROOT / REL, HERE / 'frozen_packet'
    assert not stage.exists()
    frozen = read(HERE / 'frozen_preparation_receipt.json')
    assert frozen['prepared'] is True and frozen['authorized'] is frozen['executed'] is False
    assert all(sha(packet / name) == pin for name, pin in frozen['artifact_SHA256'].items())
    for name in ('reference_candidate_static_review.json', 'final_protocol_scope_review.json'):
        review = read(HERE / name)
        assert review['authorized'] is review['executed'] is False and review['blocking_findings'] == []
        assert review['protocol_SHA256'] == sha(packet / 'protocol.json')
        assert all(sha(packet / source) == pin for source, pin in review['current_source_SHA256'].items())
    for path in sorted(packet.rglob('*')):
        if path.is_file():
            copy(path, stage / path.relative_to(packet))
    for name in ('frozen_preparation_receipt.json', 'reference_candidate_static_review.json',
                 'reference_candidate_static_review.md', 'final_protocol_scope_review.json',
                 'final_protocol_scope_review.md', 'freeze_package.py', 'prepare_formal_stage.py', 'deliver_preparation.py'):
        copy(HERE / name, stage / 'author' / name)
    prefix = (packet / 'author/front_prefix.md').read_bytes()
    history = []
    for name in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
        previous = git('show', BASE + ':' + name)
        assert (ROOT / name).read_bytes() == previous
        current = prefix + previous
        assert current.count(previous) == 1
        (ROOT / name).write_bytes(current)
        history.append(dict(path=name, old_sha256=sha256(previous).hexdigest(), new_sha256=sha(ROOT / name),
            history_start_byte=len(prefix), history_end_byte_exclusive=len(current)))
    receipt = dict(status='prepared_static_review_only', card='M-EREF1', source_baseline_commit=BASE,
        prepared=True, authorized=False, executed=False, installed=False, default_runtime_changes=0,
        artifact_SHA256={path.relative_to(ROOT).as_posix(): sha(path) for path in stage.rglob('*') if path.is_file()},
        front_history=history, HF_import_tests_science_arrays_gzip_media_pixels_or_plots=0)
    with (stage / 'author/preparation_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status=receipt['status'], stage_files=len(receipt['artifact_SHA256']) + 1,
        protocol_SHA256=sha(stage / 'protocol.json'), fronts=2, default_runtime_changes=0)))


if __name__ == '__main__':
    main()
