"""Archive a fixed selection of remaining source records after reviewed document install."""
from hashlib import sha256
from pathlib import Path
import argparse
import json

BASE = 'docs/evidence/workpiece_enlargement_20261007/right_margin4_source_context'
SOURCE_DIRS = [
    'lf_data_preparation/native_workpiece_001/right_margin4_preparation_001/author',
    'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/author',
    'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference_author',
    'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/author',
    'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/reference_author',
    'functional_views/right_margin4_20261007/geometry_001',
    'functional_views/right_margin4_20261007/complete_001',
    'functional_views/right_margin_20261007/geometry_001',
    'functional_views/right_margin_20261007/complete_001']
SUFFIXES = {'.py','.md','.json','.diff'}
sha = lambda data:sha256(data).hexdigest()
dump = lambda value:(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')


def existing_sources(root):
    paths=set()
    for name in SOURCE_DIRS:
        folder=root/name
        if folder.is_dir():paths.update(p for p in folder.iterdir() if p.is_file() and p.suffix in SUFFIXES)
    context=root/BASE
    paths.update(p for p in context.rglob('*') if p.is_file() and p.suffix in SUFFIXES)
    found={}
    for path in sorted(paths):found.setdefault(sha(path.read_bytes()),[]).append(path)
    return found


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--source-root',type=Path,help='external author root, default parent of this candidate')
    args=parser.parse_args();root=args.repo.resolve();author=Path(__file__).resolve().parent
    source_root=args.source_root.resolve() if args.source_root else author.parent
    assert not source_root.is_relative_to(root)
    context=root/BASE;target=context/'final_sources_001';assert context.is_dir() and not target.exists()
    install=json.loads((context/'closure_001/documentation_install.json').read_bytes())
    assert install['status']=='pass_reviewed_file_only_install' and install['new_scientific_calls']==0
    for entry in install['archive'].values():assert sha((root/entry['path']).read_bytes())==entry['sha256']
    saved_review=context/'closure_001/003.json'
    assert json.loads(saved_review.read_bytes())['status']=='pass_saved_only'
    selection=json.loads((author/'remaining_sources_selection.json').read_bytes())
    selected={name:(source_root/name).read_bytes() for name in selection['files']}
    assert all(sha(data)==selection['files'][name]['sha256'] for name,data in selected.items())
    found=existing_sources(root)
    archive={'001.py':Path(__file__).read_bytes(),'002.json':(author/'remaining_sources_selection.json').read_bytes(),
             '003.md':(author/'REMAINING_SOURCES_README.md').read_bytes(),'004.json':(author/'remaining_sources_author_checks.json').read_bytes()}
    copied,skipped,pending={},{},{}
    for name,data in selected.items():
        matches=[p for p in found.get(sha(data),[]) if p.read_bytes()==data]
        if matches:
            skipped[name]=dict(sha256=sha(data),existing_paths=[p.relative_to(root).as_posix() for p in matches]);continue
        if sha(data) in pending and archive[pending[sha(data)]]==data:
            skipped[name]=dict(sha256=sha(data),existing_paths=[BASE+'/final_sources_001/'+pending[sha(data)]]);continue
        short=f'{len(archive)+1:03d}{Path(name).suffix}';archive[short]=data
        copied[name]=dict(path=BASE+'/final_sources_001/'+short,sha256=sha(data),bytes=len(data))
        # Same-byte selections also deduplicate within this fixed small package.
        pending[sha(data)]=short
    target.mkdir()
    for short,data in archive.items():(target/short).write_bytes(data);assert (target/short).read_bytes()==data
    receipt=dict(status='pass_file_only_selected_source_archive',new_scientific_calls=0,selected_files=len(selected),
        copied_sources=copied,already_preserved_sources=skipped,archive_files=len(archive),archive_bytes=sum(map(len,archive.values())),
        archive={short:dict(path=BASE+'/final_sources_001/'+short,sha256=sha(data)) for short,data in archive.items()},
        saved_review_already_preserved=dict(path=BASE+'/closure_001/003.json',sha256=sha(saved_review.read_bytes())),
        role='Source-author/static-review and prefreeze history only; no scientific output/qualification or historical status rewritten')
    (target/'source_archive_receipt.json').write_bytes(dump(receipt))
    index='# Selected remaining 4 mm source records\n\nShort filenames preserve raw bytes; original names/SHA and same-byte skips are in source_archive_receipt.json. Scientific outputs stay in their formal stages. Old source-only/running/prefreeze statements are historical roles. The installed saved-only review remains closure_001/003.json. Historical author paths are provenance, not runtime dependencies.\n\n'
    index+='\n'.join(f"- [{Path(entry['path']).name}]({Path(entry['path']).name}): {name}" for name,entry in copied.items())+'\n'
    (target/'INDEX.md').write_text(index,encoding='utf-8')
    print(json.dumps(dict(status=receipt['status'],copied=len(copied),skipped=len(skipped),bytes=receipt['archive_bytes'])))


if __name__=='__main__':main()
