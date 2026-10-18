"""Freeze the authorized, source-reviewed continued-unload package; no scientific reads."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_005'
BASE = '8a78fbf54fcd45640879ad357c880d12ee38aca9'


def read(path):
    return json.loads(path.read_bytes())


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT,text=True).strip()


def main():
    assert git('rev-parse','HEAD') == BASE and git('branch','--show-current') == 'main'
    assert not git('status','--porcelain') and not (ROOT/REL).exists()
    protocol, prep, auth = [read(AUTHOR/n) for n in ('protocol.proposed.json','preparation_receipt.json','authorization.json')]
    review = read(AUTHOR/'SOURCE_REVIEW.json')
    assert review['status'].startswith('pass') and not review.get('blockers',review.get('blocking_findings',[]))
    digest = pin(AUTHOR/'protocol.proposed.json')
    assert digest == prep['protocol_sha256'] == auth['protocol_sha256'] == review['protocol_sha256']
    assert auth['authorized_execution_source_commit'] == protocol['source_baseline_commit'] == BASE
    assert auth['card'] == auth['approval_card'] == protocol['card'] == 'L-CUNLOAD5'
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['direct_human_request'] == '批准按 L-CUNLOAD5 实施并执行'
    for name, row in prep['files'].items():
        assert pin(AUTHOR/name) == row['sha256']
    for name, digest_source in protocol['source_bindings'].items():
        path = AUTHOR/Path(name).name if name.startswith(REL+'/') else ROOT/name
        assert pin(path) == digest_source, name
    payloads = {r['path']:r for r in protocol['old_scientific_inputs']}
    assert len(payloads) == 2
    for name, expected in protocol['input_bindings'].items():
        if name in payloads:
            assert payloads[name]['sha256'] == expected and (ROOT/name).stat().st_size == payloads[name]['bytes']
        else:
            path = AUTHOR/'unload_task.json' if name == REL+'/unload_task.json' else ROOT/name
            assert pin(path) == expected, name
    cwd = Path(protocol['working_directory'])
    assert cwd.is_dir() and not list(cwd.iterdir())
    stage = ROOT/REL
    (stage/'author').mkdir(parents=True,exist_ok=False)
    copies = {n:n for n in ('execute_unload.py','launch_unload.py','unload_task.json','L-CUNLOAD5_CARD.md')}
    copies['protocol.proposed.json'] = 'protocol.json'
    for n in ('prepare_package.py','freeze_package.py','environment.json','preparation_receipt.json',
              'authorization.json','SOURCE_REVIEW.json','SOURCE_REVIEW.md'):
        copies[n] = 'author/'+n
    for n in ('close.py','publish.py','archive_publication.py'):
        if (AUTHOR/n).is_file(): copies[n] = 'author/'+n
    for source,target in copies.items():
        shutil.copyfile(AUTHOR/source,stage/target)
        assert pin(AUTHOR/source) == pin(stage/target)
    for name, expected in protocol['source_bindings'].items():
        assert pin(ROOT/name) == expected
    receipt = dict(card='L-CUNLOAD5',status='frozen_authorized_not_started',source_baseline_commit=BASE,
        protocol_sha256=digest,authorization_sha256=pin(stage/'author/authorization.json'),
        source_review_sha256=pin(stage/'author/SOURCE_REVIEW.json'),copies=len(copies),
        source_bindings=len(protocol['source_bindings']),input_bindings=len(protocol['input_bindings']),
        old_payloads_opened=0,scientific_invocations=0,default_source_changes=0,new_tests=0,
        files={t:dict(bytes=(stage/t).stat().st_size,sha256=pin(stage/t)) for t in copies.values()},
        recorded_utc=datetime.now(timezone.utc).isoformat())
    (stage/'author/freeze_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:receipt[k] for k in ('status','protocol_sha256','copies','source_bindings','scientific_invocations')}),flush=True)


if __name__ == '__main__':
    main()
