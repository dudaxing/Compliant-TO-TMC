"""Create one new HF4 repair release and verify each stored payload byte."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, zipfile

root = Path(__file__).resolve().parents[1]
repo = root / 'hf_repo'
out = root / 'deliverables/HF4_repaired_evaluator_and_evidence.zip'
release = root / 'deliverables/HF4_repair_release_manifest.json'
assert not out.exists() and not release.exists(), 'Preserve prior release: choose a new release name'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
assert read(root / 'hf4_repair_results/acceptance_summary.json')['status'] == 'pass_frozen_uniform_task'
assert not subprocess.check_output(['git','status','--porcelain'], cwd=repo, text=True).strip(), 'Commit the reviewed repository first'
commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=repo, text=True).strip()
files = set()
for folder in ('hf_repo', 'hf4_results', 'hf4_repair_results', 'docs'):
    for path in (root / folder).rglob('*'):
        rel = path.relative_to(root)
        if not path.is_file() or path.is_symlink(): continue
        if any(part in {'.git','__pycache__','.pytest_cache','build'} or part.startswith('.venv') or part.endswith('.egg-info') for part in rel.parts): continue
        if path.suffix in ('.pyc','.pyo'): continue
        if 'dist' in rel.parts and path.name != 'independent_hf_evaluator-0.5.0-py3-none-any.whl': continue
        files.add(path)
for name in ('README.md','HF4_REPAIR_EVIDENCE_README.md','verify_delivery.py','HF4_CONTENT_MANIFEST.json','HF3_CONTENT_MANIFEST.json'):
    files.add(root / name)
manifest = dict(schema_version='hf4-repair-content-1.0', version='0.5.0', git_commit=commit,
    status='pass_frozen_uniform_task', created_utc=datetime.now(timezone.utc).isoformat(),
    scope='source, wheel, new and original HF4 evidence; prior HF1-HF3 geometry/results remain in previous deliveries',
    files=[dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(files)])
manifest_path = root / 'HF4_REPAIR_CONTENT_MANIFEST.json'
assert not manifest_path.exists()
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(files): z.write(p, p.relative_to(root).as_posix())
    z.write(manifest_path, manifest_path.name)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(manifest['files']) + 1
    for f in manifest['files']:
        data = z.read(f['path'])
        assert len(data) == f['bytes'] and hashlib.sha256(data).hexdigest() == f['sha256'], f['path']
    assert z.read(manifest_path.name) == manifest_path.read_bytes()
result = dict(schema_version='hf4-repair-release-1.0', version='0.5.0', status=manifest['status'],
    git_commit=commit, baseline_commit='8db49d7a932ac8b25354773f07b8baa0c6410584',
    zip_path=out.relative_to(root).as_posix(), zip_bytes=out.stat().st_size, zip_sha256=sha(out),
    zip_members=len(manifest['files'])+1, payload_files=len(manifest['files']),
    content_manifest_sha256=sha(manifest_path), wheel_sha256=sha(repo/'dist/independent_hf_evaluator-0.5.0-py3-none-any.whl'),
    acceptance_summary_sha256=sha(root/'hf4_repair_results/acceptance_summary.json'),
    verification='all ZIP CRCs and every payload SHA256/size verified; manifest bytes compared',
    old_zip_sha256=sha(root/'deliverables/HF4_AB_partial_evaluator_and_evidence.zip'))
assert result['old_zip_sha256'] == 'b5244189723fa3426f46b75cb61404d7176914b5681eae8f7d7bd2ad57b3709a'
release.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
