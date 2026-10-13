"""Record a future real M-PREF1 human approval after its actual source publication."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

REL = 'lf_data_preparation/native_interface_001/unload_reference_001'


def raw(path):
    assert path.suffix.lower() == '.json'
    return path.read_bytes()


def read(path):
    return json.loads(raw(path))


def sha(path):
    return sha256(raw(path)).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--source-publication-receipt',type=Path,required=True)
    parser.add_argument('--human-context',type=Path,required=True,help='Actual direct human reply and pending-card context; never an automatic goal continuation')
    args = parser.parse_args()
    root = args.repo.resolve()
    stage,author = root/REL,root/REL/'author'
    protocol = read(stage/'protocol.json')
    proof,human = read(args.source_publication_receipt),read(args.human_context)
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert protocol['card'] == proof['prepared_card'] == 'M-PREF1'
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == head
    assert proof['previous_delivery_commit'] == protocol['source_baseline_commit']
    assert proof['prepared'] is protocol['prepared'] is True
    assert proof['authorized'] is proof['executed'] is protocol['authorized'] is protocol['executed'] is False
    assert proof['protocol_sha256'] == sha(stage/'protocol.json')
    phase = protocol['phases']['reference']
    assert (phase['helper_seconds'],phase['outer_seconds'],protocol['sampled_RSS_bytes']) == (900,960,8*1024**3)
    assert human['authorization_from_direct_human_reply'] is True
    assert human['direct_human_answer'].strip() and human['reply_context']
    assert not (stage/'run_001').exists() and not (stage/'reference_launch.json').exists()
    assert not any((author/name).exists() for name in ('source_publication_receipt.json','direct_human_reply.json','authorization.json'))
    (author/'source_publication_receipt.json').write_bytes(raw(args.source_publication_receipt))
    reply = dict(human,card='M-PREF1',authorized_execution_source_commit=head)
    write(author/'direct_human_reply.json',reply)
    auth = dict(card='M-PREF1',authorized=True,authorization_from_direct_human_reply=True,
        direct_human_answer=human['direct_human_answer'],reply_context=human['reply_context'],authorized_execution_source_commit=head,
        source_commit_association='Bound to actual published source; this field does not assert that the human reviewed a commit hash',
        protocol_sha256=proof['protocol_sha256'],human_evidence_sha256=sha(author/'direct_human_reply.json'),
        source_publication_receipt_sha256=sha(author/'source_publication_receipt.json'),
        helper_seconds=phase['helper_seconds'],outer_seconds=phase['outer_seconds'],sampled_RSS_bytes=protocol['sampled_RSS_bytes'],
        planned_HP_calls=protocol['expected_new_HP_calls'],created_utc=datetime.now(timezone.utc).isoformat())
    write(author/'authorization.json',auth)
    print(json.dumps(dict(status='actual_direct_human_scope_bound',card='M-PREF1',authorized_execution_source_commit=head,
        actual_human_answer=human['direct_human_answer'],HP_executed=0),ensure_ascii=False))


if __name__ == '__main__':
    main()
