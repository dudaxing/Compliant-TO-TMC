"""Create a data+HF-only detached acceptance root; no original source is moved."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import tempfile
from uuid import uuid4

root=Path(__file__).resolve().parents[1]
destination=Path(tempfile.gettempdir())/('hf1_detached_'+uuid4().hex[:12])
destination.mkdir()
repo=destination/'hf_repo'
shutil.copytree(root/'hf_repo',repo,ignore=shutil.ignore_patterns('.venv','.git','__pycache__','.pytest_cache','build','*.egg-info'))
shutil.copytree(root/'geometry_dataset',destination/'geometry_dataset')
(destination/'foreign_cwd').mkdir()
(destination/'mplconfig').mkdir()
manifest=json.loads((destination/'geometry_dataset/file_manifest.json').read_text(encoding='utf-8'))
# Record all bytes irrespective of the source manifest representation.
data_files={str(p.relative_to(destination/'geometry_dataset')).replace('\\','/'):
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (destination/'geometry_dataset').rglob('*') if p.is_file()}
for path in (destination/'geometry_dataset').rglob('*'):
    if path.is_file():
        path.chmod(0o444)
forbidden=[str(root),'C:/Users/Lenovo/Downloads/Diversity-TO-Compliant-O-main (6).zip',
           'C:/Users/Lenovo/Zotero/storage/AAXN3GZJ','C:/Users/Lenovo/Zotero/storage/RQ982KG5',
           'C:/Users/Lenovo/Zotero/storage/PMK9MVG8']
receipt={'detached_root':str(destination),'copied_hf_repo':str(repo),
         'copied_dataset':str(destination/'geometry_dataset'),'foreign_cwd':str(destination/'foreign_cwd'),
         'forbidden_roots':forbidden,'dataset_hashes_before':data_files,
         'wheel_sha256':hashlib.sha256((repo/'dist/independent_hf_evaluator-0.1.0-py3-none-any.whl').read_bytes()).hexdigest()}
(root/'hf1_results/detached_location.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='dataset_hashes_before'},ensure_ascii=False,indent=2))
