"""Save reviewed source preparation and prepend current state without replacing history."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE=Path(__file__).resolve().parent
PACKET=HERE/'frozen_packet'
REL='lf_data_preparation/native_interface_001/saved_extension_002'
BASE='d7078c2e72ab6535794ff634cbb9b97325a472c6'
read=lambda path:json.loads(path.read_bytes())
sha=lambda path:sha256(path.read_bytes()).hexdigest()


def copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as output: output.write(source.read_bytes())


def main():
    git=lambda *args:subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=ROOT)
    assert git('rev-parse','HEAD').decode().strip()==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists()
    freeze=read(HERE/'frozen_preparation_receipt.json')
    assert freeze['authorized'] is freeze['executed'] is freeze['installed'] is False
    assert all(sha(PACKET/name)==pin for name,pin in freeze['artifact_SHA256'].items())
    for name in ('final_protocol_scope_review.json','wrapper_static_review_v2_scope.json'):
        review=read(HERE/name)
        assert review['authorized'] is review['executed'] is False and review['blocking_findings']==[]
        assert review['protocol_SHA256']==sha(PACKET/'protocol.json')
        for source,pin in review['current_source_SHA256'].items():
            assert sha(PACKET/source)==pin
    for path in sorted(PACKET.rglob('*')):
        if path.is_file(): copy(path,ROOT/REL/path.relative_to(PACKET))
    for name in ('frozen_preparation_receipt.json','final_protocol_scope_review.json','final_protocol_scope_review.md',
        'wrapper_static_review_v2_scope.json','wrapper_static_review_v2_scope.md','freeze_preparation.py','prepare_formal_stage.py','deliver_preparation.py','generate_preparation_tools.py'):
        destination=ROOT/REL/'author'/name
        if destination.exists(): assert destination.read_bytes()==(HERE/name).read_bytes()
        else: copy(HERE/name,destination)
    prefix=(PACKET/'author/front_prefix.md').read_bytes()
    history=[]
    for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
        path=ROOT/name; old=git('show',BASE+':'+name)
        assert path.read_bytes()==old
        raw=prefix+old
        assert raw.count(old)==1
        path.write_bytes(raw)
        history.append(dict(path=name,old_sha256=sha256(old).hexdigest(),new_sha256=sha(path),
            history_start_byte=len(prefix),history_end_byte_exclusive=len(raw)))
    value=dict(status='prepared_static_review_only',card='M-EXTEND2',source_baseline_commit=BASE,
        prepared=True,authorized=False,executed=False,installed=False,
        artifact_SHA256={path.relative_to(ROOT).as_posix():sha(path) for path in (ROOT/REL).rglob('*') if path.is_file()},
        front_history=history,default_runtime_changes=0,HF_import_collect_tests_science_arrays_media_byte_reads_plots=0)
    with (ROOT/REL/'author/preparation_receipt.json').open('x',encoding='utf-8',newline='\n') as output:
        output.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=value['status'],stage_files=len(value['artifact_SHA256'])+1,
        protocol_SHA256=sha(ROOT/REL/'protocol.json'),fronts=2,default_runtime_changes=0)))


if __name__=='__main__':main()
