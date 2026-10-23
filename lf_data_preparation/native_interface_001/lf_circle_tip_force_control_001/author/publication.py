"""Ordinary incremental publication and same-machine restore identity checks."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
RESTORE=Path('D:/hf-restore-20260930')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_force_control_001'
BASELINE='5c496c808d78e20ad26541febbcc6b49ca3ab647'
def git(folder,*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=folder)
def write(path,value):
    path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def identity(path):
    raw=path.read_bytes(); return dict(path=path.relative_to(ROOT).as_posix(),bytes=len(raw),sha256=sha256(raw).hexdigest())
def delivery_manifest():
    dest=ROOT/REL; name='DELIVERY_MANIFEST.json'
    files=[dict(path=p.relative_to(dest).as_posix(),bytes=p.stat().st_size,sha256=sha256(p.read_bytes()).hexdigest())
           for p in sorted(dest.rglob('*')) if p.is_file() and p.name!=name]
    write(dest/name,dict(stage='L-CTIPFLOAD1',files=files,scientific_recalculations=0,
        scope='Current delivered bytes excluding this manifest; no NPZ or archive decode. Later publication snapshots retain their own commit context.'))
    return dict(status='PASS',files=len(files))
def manifest(stage):
    path=ROOT/'handoff/repository_manifest.json'; data=json.loads(path.read_bytes())
    old={x['path']:x for x in data['files']}
    indexed={s.decode() for s in git(ROOT,'ls-files','-z').split(b'\0') if s}
    indexed.remove('handoff/repository_manifest.json')
    changed={s.decode() for s in git(ROOT,'diff','--cached','--name-only','-z').split(b'\0') if s}
    changed.discard('handoff/repository_manifest.json')
    assert not (set(old)-indexed), 'No deletion belongs in this delivery'
    assert indexed-set(old)<=changed
    entries=[identity(ROOT/x['path']) if x['path'] in changed else x for x in data['files']]
    entries += [identity(ROOT/name) for name in sorted(indexed-set(old))]
    assert {x['path'] for x in entries}==indexed
    data.update(files=entries,created_utc=datetime.now(timezone.utc).isoformat(),storage_stage=stage,
        previous_delivery_commit=git(ROOT,'rev-parse','HEAD').decode().strip(),
        scope='Changed/new staged files rehashed; unchanged committed identities inherited without rereading old scientific payloads. Git-index paths excluding this manifest; SHA is byte identity, not scientific admission.')
    write(path,data)
    return dict(status='PASS',entries=len(entries),rehashed=len(changed),inherited=len(indexed-changed))
def restored(mode,remote_head):
    head=git(ROOT,'rev-parse','HEAD').decode().strip()
    assert head==remote_head==git(RESTORE,'rev-parse','HEAD').decode().strip()
    assert not git(ROOT,'status','--porcelain') and not git(RESTORE,'status','--porcelain')
    data=json.loads((ROOT/'handoff/repository_manifest.json').read_bytes()); lookup={x['path']:x for x in data['files']}
    indexed={s.decode() for s in git(ROOT,'ls-files','-z').split(b'\0') if s}
    assert set(lookup)==indexed-{'handoff/repository_manifest.json'}
    names=[s.decode() for s in git(ROOT,'diff','--name-only','-z',BASELINE,head).split(b'\0') if s]
    checked=[]
    for name in names:
        row=identity(ROOT/name)
        assert (ROOT/name).read_bytes()==(RESTORE/name).read_bytes(),name
        assert name not in lookup or row==lookup[name],name
        checked.append(row)
    receipt=dict(stage='L-CTIPFLOAD1',status='PASS',created_utc=datetime.now(timezone.utc).isoformat(),
        commit=head,remote_main_verified=remote_head,origin='https://github.com/dudaxing/Compliant-TO-TMC.git',
        restore_directory=RESTORE.as_posix(),both_worktrees_clean=True,changed_files_verified=checked,
        manifest_index_set_equal=True,manifest_entries=len(lookup),new_scientific_calls=0,
        scope='Same computer, separate directory; changed delivery byte identities only. Not another computer/environment or numerical rerun.')
    if mode=='restore':
        target=ROOT/REL/'PUBLICATION_RESTORE_RECEIPT.json'
        assert not target.exists()
        receipt['snapshot_note']='First publication commit; later receipt archival commit checked in external final receipt to avoid self-reference.'
        write(target,receipt)
        report=ROOT/REL/'RESULTS.md'; raw=report.read_bytes()
        assert '## 发布与恢复'.encode() not in raw
        suffix=f'\n## 发布与恢复\n\n实现与原始证据提交`{head}`已普通推送并核远端main，`D:/hf-restore-20260930`已普通fetch／ff-only恢复到同提交。两工作树当时干净，{len(checked)}份本轮变化文件逐字节一致，仓库清单与Git索引集合相同；详见[实际回执](PUBLICATION_RESTORE_RECEIPT.json)。这是同机异目录核对，没有异机数值复算。归档回执的后续提交也将普通推送并恢复核对。\n'
        report.write_bytes(raw+suffix.encode('utf-8'))
    else:
        target=AUTHOR/'FINAL_PUBLICATION_ARCHIVE_RECEIPT.json'; write(target,receipt)
    return dict(status='PASS',commit=head,changed_files=len(checked),receipt=str(target))
if __name__=='__main__':
    if sys.argv[1]=='delivery-manifest': result=delivery_manifest()
    elif sys.argv[1]=='manifest': result=manifest(sys.argv[2])
    else: result=restored(sys.argv[1],sys.argv[2])
    print(json.dumps(result))
