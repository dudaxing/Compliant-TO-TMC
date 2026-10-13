"""Save reviewed ordinary packet and front prefix once; no scientific action."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
from preparation_common import REL,CARD,git,raw,read,sha,new


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--repo',type=Path,required=True)
    args = parser.parse_args(); root = args.repo.resolve(); here = Path(__file__).resolve().parent
    packet,stage = here/'frozen_packet',root/REL; frozen = read(here/'frozen_preparation_receipt.json')
    base = frozen['source_baseline_commit']
    assert git(root,'rev-parse','HEAD').decode().strip() == base and not git(root,'status','--porcelain') and not stage.exists()
    assert frozen['prepared'] is True and frozen['authorized'] is frozen['executed'] is False
    assert all(sha(packet/name) == pin for name,pin in frozen['artifact_SHA256'].items())
    for name in ('candidate_static_review.json','final_protocol_scope_review.json'):
        review = read(here/name)
        assert review['authorized'] is review['executed'] is False and review['blocking_findings'] == []
        assert review['protocol_SHA256'] == sha(packet/'protocol.json')
        assert all(sha(packet/path) == pin for path,pin in review['current_source_SHA256'].items())
    for path in sorted(packet.rglob('*')):
        if path.is_file(): new(stage/path.relative_to(packet),raw(path))
    for name in ('frozen_preparation_receipt.json','candidate_static_review.json','candidate_static_review.md',
                 'final_protocol_scope_review.json','final_protocol_scope_review.md','freeze_package.py',
                 'prepare_formal_stage.py','deliver_preparation.py','preparation_common.py','record_authorization.py'):
        new(stage/'author'/name,raw(here/name))
    prefix = raw(packet/'author/front_prefix.md'); history = []
    for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
        old = git(root,'show',base+':'+name); assert raw(root/name) == old
        current = prefix+old; assert current.count(old) == 1; (root/name).write_bytes(current)
        history.append(dict(path=name,old_sha256=sha256(old).hexdigest(),new_sha256=sha(root/name),history_start_byte=len(prefix),history_end_byte_exclusive=len(current)))
    new(stage/'author/preparation_receipt.json',dict(status='prepared_static_review_only',card=CARD,source_baseline_commit=base,
        prepared=True,authorized=False,executed=False,installed=False,default_runtime_changes=0,front_history=history,
        artifact_SHA256={path.relative_to(root).as_posix():sha(path) for path in stage.rglob('*') if path.is_file()},
        HF_import_tests_science_arrays_gzip_media_pixels_or_plots=0))
    print(json.dumps(dict(status='prepared_static_review_only',card=CARD,protocol_SHA256=sha(stage/'protocol.json'),fronts=2,science_execution=0)))


if __name__ == '__main__': main()
