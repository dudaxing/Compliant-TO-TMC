"""Read-only SHA256 verification of an unpacked HF4 repair delivery."""
from pathlib import Path, PurePosixPath
import hashlib, json

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'HF4_REPAIR_CONTENT_MANIFEST.json').read_text(encoding='utf-8'))
paths = set()
for item in manifest['files']:
    relative = PurePosixPath(item['path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    assert item['path'] not in paths
    paths.add(item['path'])
    target = root.joinpath(*relative.parts)
    assert target.resolve().is_relative_to(root), item['path']
    assert target.is_file() and target.stat().st_size == item['bytes'], item['path']
    assert hashlib.sha256(target.read_bytes()).hexdigest() == item['sha256'], item['path']
print(json.dumps({'status':'pass', 'files_verified':len(paths), 'version':manifest['version']}))
