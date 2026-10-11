"""Freeze only ordinary M-INTEGRATE1 preparation delta and history metadata."""
from hashlib import sha256
from pathlib import Path
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = 'd45f6ee92d8a0d6ca740772a1762abdc691489fa'
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
STAGE = ROOT / REL
CONFIG = REL + '/author/preparation_delivery_config.json'
FINAL = REL + '/author/final_delivery_review.json'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def copy_new(source, destination):
    with destination.open('xb') as output:
        output.write(source.read_bytes())


def main():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == BASE and not (ROOT / CONFIG).exists() and not (ROOT / FINAL).exists()
    for name in ('INTEGRATION_CROSS_REVIEW.json', 'INTEGRATION_CROSS_REVIEW.md',
                 'INTEGRATION_PROTOCOL_REVIEW.json', 'INTEGRATION_PROTOCOL_REVIEW.md'):
        copy_new(HERE / name, STAGE / 'author' / name)
    for path in HERE.glob('*.py'):
        destination = STAGE / 'author' / path.name
        if not destination.exists():
            copy_new(path, destination)
        else:
            assert sha(destination) == sha(path)
    protocol = read(STAGE / 'protocol.json')
    assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert not (STAGE / 'run_001').exists()
    assert all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
    documentation = read(STAGE / 'author/preparation_documentation_receipt.json')
    assert documentation['default_core_installed'] is False and documentation['new_tests_or_science_or_plots'] == 0
    for row in protocol['installation']:
        target = ROOT / row['target']
        assert (sha(target) if target.exists() else None) == row['previous_sha256']
    allowed = {path.relative_to(ROOT).as_posix() for path in STAGE.rglob('*') if path.is_file()}
    allowed.update(('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md', CONFIG, FINAL))
    value = dict(status='prepared_incremental_delivery_configuration', source_commit=BASE,
        prepared_card='M-INTEGRATE1', prepared=True, authorized=False, executed=False,
        protocol_sha256=sha(STAGE / 'protocol.json'), allowed_delta_paths=sorted(allowed),
        final_review_path=FINAL, front_history=documentation['front_history'],
        previous_publication_receipt=dict(path=REL + '/author/M_RESUME1_execution_publication_receipt.json',
            sha256=sha(STAGE / 'author/M_RESUME1_execution_publication_receipt.json')),
        peer_reviews={REL + '/author/' + name: sha(STAGE / 'author' / name) for name in
            ('INTEGRATION_CROSS_REVIEW.json', 'INTEGRATION_PROTOCOL_REVIEW.json')},
        default_core_installed=False, new_tests_or_science_or_plots=0)
    with (ROOT / CONFIG).open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status=value['status'], files=len(allowed), config_sha256=sha(ROOT / CONFIG)), ensure_ascii=False))


if __name__ == '__main__':
    main()
