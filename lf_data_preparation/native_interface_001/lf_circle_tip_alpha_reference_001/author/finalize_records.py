"""Finalize new ordinary records and links without reading scientific payloads."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import re


ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_reference_001'
CARD = 'L-CTIPAREF1'
ORDINARY = {'.py', '.json', '.jsonl', '.ndjson', '.md', '.html', '.log', '.txt'}


def main():
    destination = STAGE/'author/finalize_records.py'
    result = STAGE/'author/FINAL_DOC_REVIEW.json'
    assert not destination.exists() and not result.exists(), 'Preserve completed finalization records'
    review = json.loads((STAGE/'author/SOURCE_REVIEW.json').read_bytes())
    assert sha256(Path(__file__).read_bytes()).hexdigest() == review['reviewed_support_sha256']['finalize_records.py']
    destination.write_bytes(Path(__file__).read_bytes())
    for path in STAGE.rglob('*'):
        if path.is_file() and path.suffix.lower() in ORDINARY:
            raw = path.read_bytes()
            assert all(line.rstrip(b' \t') == line for line in raw.splitlines()), path
            if path.suffix == '.py':
                ast.parse(raw)
    checks = dict(new_ordinary_syntax_and_whitespace=True)
    checked = []
    for name in ('RESULTS.md', 'NEXT_STEPS.md', 'run_001/REVIEW.md', 'run_001/reference/REVIEW.md'):
        path = STAGE/name
        if name.startswith('run_001/') and not path.is_file():
            continue
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if link.startswith('<') and link.endswith('>'):
                link = link[1:-1]
            if '://' in link or link.startswith('#'):
                continue
            target = (path.parent/link.split('#')[0]).resolve()
            target.relative_to(ROOT)
            assert target.exists(), (name, link)
            checked.append(dict(document=name, link=link))
    checks['new_document_links_exist'] = True
    history = json.loads((STAGE/'author/front_history.json').read_bytes())
    assert len(history['files']) == 7
    for row in history['files']:
        raw = (ROOT/row['path']).read_bytes()
        old = raw[row['prefix_bytes']:]
        assert len(old) == row['old_bytes'] and sha256(old).hexdigest() == row['old_sha256']
        assert raw.count(old) == 1
    checks['seven_original_front_suffixes_preserved_once'] = True
    report = dict(card=CARD, status='pass_ordinary_final_documents', checks=checks,
        checked_links=checked, science_or_media_payload_reads=0,
        scientific_tests_or_reexecution=0)
    with result.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], links=len(checked), fronts=7)), flush=True)


if __name__ == '__main__':
    main()
