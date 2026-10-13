"""Bind a real general continuation instruction to the reviewed display source."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

REL = 'functional_views/native_alpha_composed_20261013/complete_001'


def read(path):
    assert path.suffix == '.json'
    return json.loads(path.read_bytes())


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--source-publication-receipt',type=Path,required=True)
    parser.add_argument('--human-context',type=Path,required=True)
    args = parser.parse_args()
    root = args.repo.resolve(); stage = root/REL; author = stage/'author'
    protocol = read(stage/'protocol.json')
    proof, human = read(args.source_publication_receipt),read(args.human_context)
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert protocol['card'] == proof['prepared_card'] == 'M-PATH1'
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == head
    assert proof['previous_delivery_commit'] == protocol['source_baseline_commit']
    assert proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    assert proof['protocol_sha256'] == sha256((stage/'protocol.json').read_bytes()).hexdigest()
    assert human['authorization_from_direct_human_reply'] is True and human['direct_human_answer'] == '继续' and human['reply_context']
    assert human['new_HP_authorized_by_this_record'] is False
    assert human['human_explicitly_named_M_PATH1'] is human['human_explicitly_approved_a_future_commit'] is False
    assert not (stage/'run_001').exists() and not (stage/'path_launch.json').exists()
    for name in ('source_publication_receipt.json','direct_human_reply.json','authorization.json'):
        assert not (author/name).exists()
    (author/'source_publication_receipt.json').write_bytes(args.source_publication_receipt.read_bytes())
    reply = dict(human,card='M-PATH1',authorized_execution_source_commit=head)
    write(author/'direct_human_reply.json',reply)
    write(author/'authorization.json',dict(card='M-PATH1',authorized=True,authorization_from_direct_human_reply=True,
        direct_human_answer=human['direct_human_answer'],authorization_scope=human['authorized_scope'],
        authorized_execution_source_commit=head,source_commit_association='Root freezes reviewed source within the directly authorized reversible scope; no claim of a human commit review',
        protocol_sha256=proof['protocol_sha256'],
        human_evidence_sha256=sha256((author/'direct_human_reply.json').read_bytes()).hexdigest(),
        source_publication_receipt_sha256=sha256((author/'source_publication_receipt.json').read_bytes()).hexdigest(),
        created_utc=datetime.now(timezone.utc).isoformat(),new_HP_authorized=False))
    print(json.dumps(dict(status='actual_continue_scope_bound',card='M-PATH1',execution_source_commit=head,actual_human_answer=human['direct_human_answer'],new_HP_authorized=False),ensure_ascii=False))


if __name__ == '__main__':
    main()
