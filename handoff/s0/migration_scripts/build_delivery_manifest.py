"""Build the S0 delivery manifest; optionally copy only that payload to a new tree."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--worktree',type=Path,required=True);p.add_argument('--slim-copy',type=Path)
    a=p.parse_args();root=a.worktree.resolve()
    candidate=json.loads((root/'handoff/s0/migration_candidate.json').read_text())
    external={f['path'] for group in candidate['groups'].values() for f in group['files']}
    assert len(external)==1099 and all(not n.startswith(('hf_repo/','geometry_dataset/')) for n in external)
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=root).decode().split('\0')
    names=sorted(set(n for n in names if n and n not in external and n!='handoff/repository_manifest.json'))
    records=[]
    for name in names:
        path=(root/name).resolve();assert path.is_relative_to(root) and path.is_file(),name
        records.append({'path':name,'bytes':path.stat().st_size,'sha256':sha(path)})
    result={'schema_version':'github-handoff-repository-1.0','created_utc':datetime.now(timezone.utc).isoformat(),
            'science_version':'0.5.0','science_baseline_commit':'b1334bb6a83ba9a0efab7bdba7bd39722146f024',
            'storage_stage':'HF4-C2-S0','previous_delivery_commit':candidate['baseline_commit'],
            'scope':'Lightweight tracked payload except this manifest; all declared external scientific evidence is required only by verify --full. File identity is not mechanics admission.',
            'files':records}
    manifest=root/'handoff/repository_manifest.json';manifest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if a.slim_copy:
        dest=a.slim_copy.resolve();assert not dest.exists() and not dest.is_relative_to(root)
        dest.mkdir(parents=True)
        for row in records+ [{'path':'handoff/repository_manifest.json','bytes':manifest.stat().st_size,'sha256':sha(manifest)}]:
            target=dest/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
            with (root/row['path']).open('rb') as src,target.open('xb') as out:shutil.copyfileobj(src,out,1024*1024)
            assert target.stat().st_size==row['bytes'] and sha(target)==row['sha256']
        assert not any((dest/name).exists() for name in external)
    print(json.dumps({'manifest_files':len(records),'tracked_file_count':len(records)+1,
                      'tracked_file_bytes':sum(f['bytes'] for f in records)+manifest.stat().st_size,
                      'manifest_sha256':sha(manifest),'slim_copy':str(a.slim_copy) if a.slim_copy else None}))

if __name__=='__main__':main()
