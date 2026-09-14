"""Portable handoff verification, environment inspection and evidence retrieval.

Standard library only except `inspect`, which reads two geometries with an already
installed hf_eval. Never edits historical evidence or starts a mechanics solve.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def safe_path(base, name):
    rel = PurePosixPath(name)
    if rel.is_absolute() or not rel.parts or '..' in rel.parts or '\\' in name or any(':' in p for p in rel.parts):
        raise ValueError(f'Invalid relative path: {name}')
    target = base.joinpath(*rel.parts)
    if not target.resolve().is_relative_to(base.resolve()):
        raise ValueError(f'Path escapes selected root: {name}')
    return target

def check_file(path, record):
    if not path.is_file() or path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
        raise ValueError(f'Missing or modified file: {path}')

def verify(full=False):
    manifest = read(ROOT / 'handoff/repository_manifest.json')
    paths = set()
    for item in manifest['files']:
        if item['path'] in paths:
            raise ValueError('Duplicate manifest path')
        paths.add(item['path'])
        check_file(safe_path(ROOT, item['path']), item)
    historical = 0
    if full:
        for asset in read(ROOT / 'handoff/evidence_assets.json')['assets']:
            if asset['mode'] == 'save_archive':
                check_file(safe_path(ROOT, asset['destination']), asset)
            else:
                for item in asset['files']:
                    check_file(safe_path(ROOT, item['path']), item)
                    historical += 1
    return dict(status='pass', repository_files=len(paths), restored_historical_files=historical,
                full_evidence_checked=full, scope='file identity, not a new mechanics validation')

def inspect():
    import hf_eval
    from hf_eval.data import load_geometry
    package_names = ('independent-hf-evaluator', 'numpy', 'scipy', 'matplotlib', 'jax', 'jaxlib', 'pytest', 'psutil')
    versions = {}
    for name in package_names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    records = []
    for item in read(ROOT / 'geometry_dataset/dataset_index.json')['current_canonical_subset']:
        path = safe_path(ROOT / 'geometry_dataset', item['geometry'])
        geometry = load_geometry(path)
        if geometry.geometry_id != item['geometry_id']:
            raise ValueError('Canonical geometry identity differs from index')
        records.append(dict(case_family=item['case_family'], geometry_id=geometry.geometry_id,
                            shape_yx=list(geometry.solid.shape), relative_path=path.relative_to(ROOT).as_posix()))
    return dict(status='pass', python=sys.version, executable=sys.executable, os=platform.platform(),
                machine=platform.machine(), processor=platform.processor(), versions=versions,
                installed_hf_path=str(Path(hf_eval.__file__).resolve()), geometries=records,
                environment={k:os.environ.get(k) for k in ('JAX_ENABLE_X64', 'JAX_PLATFORMS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'MPLBACKEND')},
                scope='installed package import and two ordinary geometry reads; no solve or cross-platform numerical claim')

def download(asset, cache, source=None):
    cache.mkdir(parents=True, exist_ok=True)
    target = safe_path(cache, asset['name'])
    if target.exists():
        check_file(target, asset)
        return target
    partial = target.with_suffix(target.suffix + '.partial')
    if partial.exists():
        raise ValueError(f'Incomplete download preserved at {partial}; use a fresh --cache-dir to retry')
    if source:
        original = safe_path(source, asset['name'])
        check_file(original, asset)
        with original.open('rb') as src, partial.open('xb') as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
    else:
        print(f"Downloading {asset['name']} ({asset['bytes'] / 2**20:.1f} MiB)", flush=True)
        request = urllib.request.Request(asset['url'], headers={'User-Agent':'Compliant-TO-TMC-handoff'})
        with urllib.request.urlopen(request, timeout=60) as src, partial.open('xb') as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
    check_file(partial, asset)
    if target.exists():
        raise ValueError('Cache target appeared during download; refusing to replace it')
    partial.rename(target)
    return target

def fetch(assets, cache, source):
    index = read(ROOT / 'handoff/evidence_assets.json')
    selected = [a for a in index['assets'] if not assets or a['name'] in assets]
    if assets and set(assets) != {a['name'] for a in selected}:
        raise ValueError('Unknown --asset; see handoff/evidence_assets.json')
    results = []
    for asset in selected:
        archive = download(asset, cache, source)
        if asset['mode'] == 'save_archive':
            target = safe_path(ROOT, asset['destination'])
            if target.exists():
                check_file(target, asset)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open('rb') as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
            results.append(dict(name=asset['name'], restored=0, saved=asset['destination']))
            continue
        records = {f['path']:f for f in asset['files']}
        if len(records) != len(asset['files']):
            raise ValueError('Duplicate asset manifest entry')
        with zipfile.ZipFile(archive) as z:
            if len(z.namelist()) != len(records) or set(z.namelist()) != set(records):
                raise ValueError('Archive membership differs from published manifest')
            # Preflight all existing destinations before writing any member.
            for name, item in records.items():
                target = safe_path(ROOT, name)
                if target.exists():
                    check_file(target, item)
            for name, item in records.items():
                target = safe_path(ROOT, name)
                data = z.read(name)
                if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                    raise ValueError(f'Archive member failed verification: {name}')
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open('xb') as stream:
                        stream.write(data)
        results.append(dict(name=asset['name'], restored=len(records)))
        print(f"Verified and restored {asset['name']}", flush=True)
    return dict(status='pass', assets=results, scope='verified evidence restoration only; existing different files are never overwritten')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('verify'); p.add_argument('--full', action='store_true'); p.add_argument('--output', type=Path)
    p = sub.add_parser('inspect'); p.add_argument('--output', type=Path)
    p = sub.add_parser('fetch-evidence'); p.add_argument('--asset', action='append')
    p.add_argument('--cache-dir', type=Path, default=ROOT / '.evidence_cache')
    p.add_argument('--from-dir', type=Path, help='Use already downloaded archives instead of the network')
    p.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error('Output already exists; choose a new path to preserve prior records')
    if args.command == 'verify':
        result = verify(args.full)
    elif args.command == 'inspect':
        result = inspect()
    else:
        result = fetch(args.asset, args.cache_dir.resolve(), args.from_dir.resolve() if args.from_dir else None)
    result['created_utc'] = datetime.now(timezone.utc).isoformat()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
