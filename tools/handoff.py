"""Portable handoff verification, evidence retrieval and independent replay setup.

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
    if not isinstance(name, str):
        raise ValueError(f'Invalid relative path: {name!r}')
    rel = PurePosixPath(name)
    if rel.is_absolute() or not rel.parts or rel.as_posix() != name or '..' in rel.parts or '\\' in name or any(':' in p for p in rel.parts):
        raise ValueError(f'Invalid relative path: {name}')
    target = base.joinpath(*rel.parts)
    if not target.resolve().is_relative_to(base.resolve()):
        raise ValueError(f'Path escapes selected root: {name}')
    return target

def check_file(path, record):
    if not path.is_file() or path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
        raise ValueError(f'Missing or modified file: {path}')

def repository_records(root):
    manifest = read(root / 'handoff/repository_manifest.json')
    paths = set()
    for item in manifest['files']:
        if item['path'] in paths:
            raise ValueError('Duplicate manifest path')
        paths.add(item['path'])
        safe_path(root, item['path'])
    return manifest['files']

def select_assets(root, requested=None):
    """Validate the whole index, then return a dependency-first closure.

    Missing ``requires`` is the historical index's empty dependency list.
    Invalid unrelated entries are rejected as well: selection must not hide a
    malformed dependency graph in the published evidence index.
    """
    index = read(root / 'handoff/evidence_assets.json')
    by_name = {}
    for asset in index['assets']:
        name = asset['name']
        safe_path(root, name)
        if name in by_name:
            raise ValueError(f'Duplicate asset name: {name}')
        if asset['mode'] not in ('save_archive', 'restore_relative_files'):
            raise ValueError(f'Unknown asset mode: {asset["mode"]}')
        requires = asset.get('requires', [])
        if not isinstance(requires, list) or any(not isinstance(n, str) for n in requires):
            raise ValueError(f'Invalid requires for asset: {name}')
        if len(set(requires)) != len(requires):
            raise ValueError(f'Duplicate dependency in asset: {name}')
        if asset['mode'] == 'save_archive':
            safe_path(root, asset['destination'])
        else:
            records = asset['files']
            if len({item['path'] for item in records}) != len(records):
                raise ValueError(f'Duplicate asset manifest entry: {name}')
            for item in records:
                safe_path(root, item['path'])
        by_name[name] = asset
    for name, asset in by_name.items():
        for dependency in asset.get('requires', []):
            if dependency not in by_name:
                raise ValueError(f'Unknown dependency {dependency} required by {name}')
    if requested is not None:
        if len(set(requested)) != len(requested):
            raise ValueError('Duplicate --asset selection')
        for name in requested:
            if name not in by_name:
                raise ValueError(f'Unknown --asset: {name}; see handoff/evidence_assets.json')

    visiting, visited = set(), set()
    def visit(name, ordered):
        if name in visiting:
            raise ValueError(f'Asset dependency cycle at: {name}')
        if name in visited:
            return
        visiting.add(name)
        for dependency in by_name[name].get('requires', []):
            visit(dependency, ordered)
        visiting.remove(name)
        visited.add(name)
        ordered.append(by_name[name])
    # Check the complete graph before any download or restoration.
    for name in by_name:
        visit(name, [])
    visited.clear()
    ordered = []
    for name in (by_name if not requested else requested):
        visit(name, ordered)
    return ordered

def asset_destinations(asset):
    if asset['mode'] == 'save_archive':
        return [(asset['destination'], asset)]
    return [(item['path'], item) for item in asset['files']]

def preflight_destinations(root, assets):
    """Reject existing conflicts across the complete closure before any write."""
    records = {}
    for asset in assets:
        for name, item in asset_destinations(asset):
            target = safe_path(root, name)
            previous = records.get(name)
            if previous and (previous['bytes'], previous['sha256']) != (item['bytes'], item['sha256']):
                raise ValueError(f'Conflicting asset destination records: {name}')
            records[name] = item
            if target.exists():
                check_file(target, item)
            for parent in target.parents:
                if parent == root:
                    break
                if parent.exists() and not parent.is_dir():
                    raise ValueError(f'Asset destination parent is not a directory: {parent}')
    for name in records:
        if any(parent.as_posix() in records for parent in PurePosixPath(name).parents):
            raise ValueError(f'Asset destination is nested inside another file: {name}')

def verify(full=False, assets=None, root=None):
    root = ROOT if root is None else Path(root)
    if full and assets:
        raise ValueError('Use either --full or --asset, not both')
    records = repository_records(root)
    for item in records:
        check_file(safe_path(root, item['path']), item)
    historical = 0
    selected = select_assets(root, None if full else assets) if full or assets else []
    for asset in selected:
        for name, item in asset_destinations(asset):
            check_file(safe_path(root, name), item)
            historical += int(asset['mode'] != 'save_archive')
    return dict(status='pass', repository_files=len(records), restored_historical_files=historical,
                asset_closure=[a['name'] for a in selected],
                saved_archives_checked=sum(a['mode'] == 'save_archive' for a in selected),
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
    target.parent.mkdir(parents=True, exist_ok=True)
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

def fetch(assets, cache, source, root=None):
    root = ROOT if root is None else Path(root)
    selected = select_assets(root, assets)
    preflight_destinations(root, selected)
    results = []
    for asset in selected:
        archive = download(asset, cache, source)
        if asset['mode'] == 'save_archive':
            target = safe_path(root, asset['destination'])
            if target.exists():
                check_file(target, asset)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open('rb') as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
                check_file(target, asset)
            results.append(dict(name=asset['name'], restored=0, saved=asset['destination']))
            continue
        records = {f['path']:f for f in asset['files']}
        with zipfile.ZipFile(archive) as z:
            if len(z.namelist()) != len(records) or set(z.namelist()) != set(records):
                raise ValueError('Archive membership differs from published manifest')
            # Validate every member before writing the first. Reading in chunks
            # also bounds memory for large frozen audit files.
            for name, item in records.items():
                target = safe_path(root, name)
                if target.exists():
                    check_file(target, item)
                size, member_digest = 0, hashlib.sha256()
                with z.open(name) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        size += len(block)
                        member_digest.update(block)
                if size != item['bytes'] or member_digest.hexdigest() != item['sha256']:
                    raise ValueError(f'Archive member failed verification: {name}')
            for name, item in records.items():
                target = safe_path(root, name)
                if target.exists():
                    check_file(target, item)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(name) as src, target.open('xb') as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                    check_file(target, item)
        results.append(dict(name=asset['name'], restored=len(records)))
        print(f"Verified and restored {asset['name']}", flush=True)
    return dict(status='pass', assets=results, asset_closure=[a['name'] for a in selected],
                scope='verified evidence restoration only; existing different files are never overwritten')

def prepare_replay(destination, assets, cache, source=None, root=None):
    """Prepare a separate evidence root. No evaluator or audit is executed."""
    root = (ROOT if root is None else Path(root)).resolve()
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Replay destination already exists; choose a new directory')
    if destination.is_relative_to(root):
        raise ValueError('Replay destination must be outside the source checkout')
    if not assets:
        raise ValueError('prepare-replay requires at least one explicit --asset')
    selected = select_assets(root, assets)
    source_verification = verify(root=root)
    records = repository_records(root)
    names = {item['path'] for item in records}
    manifest_name = 'handoff/repository_manifest.json'
    if manifest_name in names:
        raise ValueError('Repository manifest must not list itself')
    if 'handoff/evidence_assets.json' not in names:
        raise ValueError('Replay requires a manifest-bound evidence_assets.json')
    manifest_path = root / manifest_name
    manifest_sha256 = digest(manifest_path)
    destination.mkdir(parents=True, exist_ok=False)
    for item in records:
        target = safe_path(destination, item['path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        with safe_path(root, item['path']).open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        check_file(target, item)
    copied_manifest = destination / manifest_name
    with manifest_path.open('rb') as src, copied_manifest.open('xb') as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)
    if digest(copied_manifest) != manifest_sha256:
        raise ValueError('Source manifest changed during replay preparation')
    restoration = fetch(assets, cache, source, root=destination)
    verification = verify(assets=assets, root=destination)
    return dict(status='pass', source_root=str(root), destination_root=str(destination),
                source_manifest_sha256=manifest_sha256,
                repository_files_copied=source_verification['repository_files'],
                manifest_copied_separately=True, asset_closure=[a['name'] for a in selected],
                restoration=restoration, verification=verification,
                mechanics_run=False, high_precision_run=False,
                scope='independent evidence preparation and file identity only; no mechanics or audit execution')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('verify')
    selection = p.add_mutually_exclusive_group()
    selection.add_argument('--full', action='store_true')
    selection.add_argument('--asset', action='append')
    p.add_argument('--output', type=Path)
    p = sub.add_parser('inspect'); p.add_argument('--output', type=Path)
    p = sub.add_parser('fetch-evidence'); p.add_argument('--asset', action='append')
    p.add_argument('--cache-dir', type=Path, default=ROOT / '.evidence_cache')
    p.add_argument('--from-dir', type=Path, help='Use already downloaded archives instead of the network')
    p.add_argument('--output', type=Path)
    p = sub.add_parser('prepare-replay')
    p.add_argument('--destination', type=Path, required=True, help='New directory outside the source checkout')
    p.add_argument('--asset', action='append', required=True)
    p.add_argument('--cache-dir', type=Path, default=ROOT / '.evidence_cache')
    p.add_argument('--from-dir', type=Path, help='Use already downloaded archives instead of the network')
    p.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error('Output already exists; choose a new path to preserve prior records')
    if args.command == 'verify':
        result = verify(args.full, args.asset)
    elif args.command == 'inspect':
        result = inspect()
    elif args.command == 'prepare-replay':
        result = prepare_replay(args.destination, args.asset, args.cache_dir.resolve(),
                                args.from_dir.resolve() if args.from_dir else None)
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
