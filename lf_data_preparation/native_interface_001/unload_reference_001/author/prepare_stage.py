"""Save frozen M-PREF1 ordinary sources and prepend two complete histories once."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import ast

from publisher_source import BASE, REL, MANIFEST, FRONTS, RUNTIME, ORIGIN
from publisher_source import raw, sha, read, git, path_in, old_manifest, check_protocol, write_new

HERE = Path(__file__).resolve().parent
AUTHOR_FILES = ('front_prefix.md','input_scope_review.json','input_scope_review.md',
    'physical_gate_review.json','physical_gate_review.md','SOURCE_AUTHOR_NOTES.md','source_author_receipt.json',
    'input_contract_seed.json','prepare_stage.py','publisher_source.py','record_authorization.py',
    'METADATA_TOOL_SOURCE_NOTES.md','metadata_tools_author_receipt.json','final_source_review.json','final_source_review.md')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--previous-publication-receipt',type=Path,required=True)
    parser.add_argument('--author-file',action='append',default=[],help='An additional explicitly named ordinary file in this external directory')
    args = parser.parse_args()
    root = args.repo.resolve()
    assert not HERE.is_relative_to(root)
    assert git(root,'rev-parse','HEAD').decode().strip() == BASE and git(root,'branch','--show-current').decode().strip() == 'main'
    assert not git(root,'status','--porcelain')
    assert git(root,'remote','get-url','origin').decode().strip() == git(root,'remote','get-url','--push','origin').decode().strip() == ORIGIN
    proof = read(args.previous_publication_receipt)
    oldraw,_,old = old_manifest(root,proof)
    assert raw(root/MANIFEST) == oldraw
    plan = {name:HERE/name for name in RUNTIME | {'protocol.json','M-PREF1_CARD.md','PREPARATION_RESULTS.md'}}
    plan.update({'author/'+name:path_in(HERE,name) for name in AUTHOR_FILES+tuple(args.author_file)})
    plan['author/previous_execution_publication_receipt.json'] = args.previous_publication_receipt.resolve()
    assert not (root/REL).exists()
    for source in plan.values():
        value = raw(source)
        if source.suffix == '.py':
            ast.parse(value.decode('utf-8'))
    protocol = read(HERE/'protocol.json')
    resolve = lambda name: plan[name[len(REL)+1:]] if name.startswith(REL+'/') else path_in(root,name)
    check_protocol(root,protocol,old,resolve)
    review = read(HERE/'final_source_review.json')
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    assert review['authorized'] is review['executed'] is False and review['protocol_SHA256'] == sha(HERE/'protocol.json')
    assert RUNTIME | {'protocol.json','M-PREF1_CARD.md','PREPARATION_RESULTS.md'} <= review['current_source_SHA256'].keys()
    assert all(sha(plan[name]) == pin for name,pin in review['current_source_SHA256'].items())
    prefix = raw(HERE/'front_prefix.md')
    assert prefix
    previous = {name:git(root,'show',BASE+':'+name) for name in FRONTS}
    assert all(raw(root/name) == value and (prefix+value).count(value) == 1 for name,value in previous.items())
    stage = root/REL
    for name,source in sorted(plan.items()):
        destination = path_in(stage,name)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(raw(source))
    history = []
    for name,value in sorted(previous.items()):
        current = prefix+value
        (root/name).write_bytes(current)
        history.append(dict(path=name,old_sha256=sha256(value).hexdigest(),new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix),history_end_byte_exclusive=len(current),old_raw_contiguous_once=True))
    artifacts = {path.relative_to(root).as_posix():sha(path) for path in stage.rglob('*') if path.is_file()
        and path != stage/'author/final_source_review.json'}
    receipt = dict(status='prepared_static_review_only',card='M-PREF1',source_baseline_commit=BASE,
        prepared=True,authorized=False,executed=False,installed=False,created_utc=datetime.now(timezone.utc).isoformat(),
        artifact_SHA256=artifacts,front_history=history,review_files=['author/final_source_review.json'],
        planned_new_HP_calls=4,default_runtime_changes=0,scientific_or_media_byte_reads_hashes_headers_decode=0,
        new_HF_API_HP_solver_tests_pixels_or_plots=0)
    write_new(stage/'author/preparation_receipt.json',receipt)
    print({'status':receipt['status'],'protocol_SHA256':sha(stage/'protocol.json'),'stage_files':len(artifacts)+2,'fronts':2,'executed':False})


if __name__ == '__main__':
    main()
