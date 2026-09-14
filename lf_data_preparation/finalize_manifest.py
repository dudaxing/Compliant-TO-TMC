"""Freeze a data-only package file inventory after all export evidence is written."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);a=p.parse_args()
    root=a.dataset.resolve();entries=[]
    for f in sorted(root.rglob('*')):
        if f.is_symlink():raise ValueError('Dataset may not contain symlinks')
        if not f.is_file() or f==root/'file_manifest.json':continue
        if f.suffix.lower() in {'.py','.pyc','.m','.whl','.zip','.exe','.dll'}:raise ValueError(f'Code/archive found in data package: {f}')
        entries.append({'path':f.relative_to(root).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    manifest={'schema_version':'hf-file-manifest-1.0','root':'.','paths':'package_relative_no_external_runtime_paths',
              'self_excluded':'file_manifest.json','file_count':len(entries),'files':entries}
    (root/'file_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'file_count':len(entries),'total_bytes':sum(x['bytes']for x in entries)}))

if __name__=='__main__':main()
