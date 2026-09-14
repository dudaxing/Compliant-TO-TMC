"""Copy supplied material without modifying it; preserve hashes and author files."""
from pathlib import Path
import hashlib, json, shutil
root = Path(__file__).resolve().parents[1]
records = json.loads((root/'hf0_audit/environment/source_inventory.json').read_text(encoding='utf-8'))
names = ['lf_snapshot.zip','tmc_source.zip','frederiksen_2026.pdf','frederiksen_2025.pdf','hf_start_brief.txt']
manifest=[]
for record,name in zip(records,names):
    source=Path(record['source_path_record_only']); target=root/'reference_inputs'/name
    if not target.exists():
        shutil.copyfile(source,target)
        target.chmod(0o444)
    with target.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    assert digest==record['sha256'], name
    manifest.append({'file':name,'sha256':digest,'bytes':target.stat().st_size,'original_path_record_only':str(source)})
(root/'reference_inputs/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('All five source copies match HF-0 hashes; copies marked read-only.')
