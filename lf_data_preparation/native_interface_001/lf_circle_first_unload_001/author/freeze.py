"""Freeze reviewed ordinary files after direct approval; no HF execution."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_001'
BASE = 'c78658322587499e901e654516aed62b45aa022d'


def main():
    auth = json.loads((AUTHOR/'HUMAN_AUTHORIZATION.json').read_bytes())
    review = json.loads((AUTHOR/'SOURCE_REVIEW.json').read_bytes())
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is True
    assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
    assert subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
    assert not subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','status','--porcelain'],cwd=ROOT)
    destination = ROOT/STAGE
    assert not destination.exists()
    raw = (AUTHOR/'protocol.proposed.json').read_bytes()
    protocol = json.loads(raw)
    files = json.loads((AUTHOR/'package_files.json').read_bytes())
    for name,pin in protocol['baseline_source_bindings'].items():
        path = Path(files[name]) if name in files else ROOT/name
        assert sha256(path.read_bytes()).hexdigest() == pin, name
    assert sha256((AUTHOR/'L-CUNLOAD1_CARD.md').read_bytes()).hexdigest() == auth['approved_card_sha256']
    # Review hashes bind every executable/package source and proposed protocol.
    for name,pin in review['reviewed_file_sha256'].items():
        assert sha256((AUTHOR/name).read_bytes()).hexdigest() == pin, name
    destination.mkdir(parents=True,exist_ok=False)
    for name,source in files.items():
        target = ROOT/name
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:
            stream.write(Path(source).read_bytes())
    (destination/'protocol.json').write_bytes(raw)
    for name in ('SOURCE_REVIEW.json','SOURCE_REVIEW.md'):
        (destination/'author'/name).write_bytes((AUTHOR/name).read_bytes())
    auth.update(protocol_sha256=sha256(raw).hexdigest(),approval_card='L-CUNLOAD1')
    (destination/'author/authorization.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    cwd = Path(protocol['working_directory'])
    assert not cwd.exists()
    cwd.mkdir(exist_ok=False)
    receipt = dict(status='frozen_not_executed',card='L-CUNLOAD1',created_utc=datetime.now(timezone.utc).isoformat(),
        source_baseline_commit=BASE,protocol_sha256=auth['protocol_sha256'],
        copied_files=len(files),baseline_source_count=len(protocol['baseline_source_bindings']),
        production_files_modified=0,science_calls=0,
        note='Preapproval false/pending records are immutable historical snapshots; new explicit human authorization is author/authorization.json.')
    (destination/'author/freeze_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(receipt),flush=True)


if __name__ == '__main__':
    main()
