"""Record actual direct human L-REF1 approval; never an automatic continuation."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

REL = 'lf_data_preparation/native_interface_001/lf_reference_001'
HEAD = '799bdc9709fa2fc92f573f3801b243f24e370983'
PROTOCOL = 'd6512016bc169183e6f857d0bab18185aa66e1aec3847ccbdb30a9450b9a2125'
PROOF = '035d8cf368be89c345cdcd0629539e7cbbb94efe1a902d677bcf139b5181d131'
CONFIRMATION = 'aae7d12fcaf6d2220226a8d48fb7f03728fc186c772667d79ae2c8c23d200cd6'


def raw(path):
    assert path.suffix.lower() == '.json'
    return path.read_bytes()


def write(path, content):
    with path.open('xb') as stream:
        stream.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--source-publication-receipt', type=Path, required=True)
    parser.add_argument('--publication-confirmation', type=Path, required=True)
    parser.add_argument('--human-context', type=Path, required=True, help='Actual human answer and pending L-REF1 context')
    args = parser.parse_args()
    root = args.repo.resolve()
    stage, author = root / REL, root / REL / 'author'
    protocol_raw, proof_raw, confirmation_raw, human_raw = (raw(path) for path in
        (stage / 'protocol.json', args.source_publication_receipt, args.publication_confirmation, args.human_context))
    protocol, proof, confirmation, human = map(json.loads, (protocol_raw, proof_raw, confirmation_raw, human_raw))
    assert sha256(protocol_raw).hexdigest() == PROTOCOL and sha256(proof_raw).hexdigest() == PROOF
    assert sha256(confirmation_raw).hexdigest() == CONFIRMATION
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == HEAD
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip() == 'main'
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=root)
    assert protocol['card'] == proof['prepared_card'] == confirmation['card'] == 'L-REF1'
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == confirmation['published_commit'] == HEAD
    assert proof['protocol_sha256'] == confirmation['protocol_SHA256'] == PROTOCOL
    assert confirmation['source_publication_receipt_SHA256'] == PROOF
    assert confirmation['source_and_restore_clean'] is confirmation['remote_main_confirmed_equal'] is True
    assert confirmation['prepared'] is True and confirmation['authorized'] is confirmation['executed'] is confirmation['installed'] is False
    assert proof['previous_delivery_commit'] == protocol['source_baseline_commit']
    assert proof['prepared'] is protocol['prepared'] is True
    assert proof['authorized'] is proof['executed'] is protocol['authorized'] is protocol['executed'] is False
    phase = protocol['phases']['reference']
    assert (phase['helper_seconds'], phase['outer_seconds'], protocol['sampled_RSS_bytes']) == (900, 960, 8 * 1024**3)
    assert human['authorization_from_direct_human_reply'] is True
    answer, context = human['direct_human_answer'], human['reply_context']
    assert isinstance(answer, str) and answer.strip() and isinstance(context, dict) and context
    assert context['source'] in ('actual_user_send_user_message_question_reply', 'actual_user_message', 'direct_human_user_message')
    assert 'L-REF1' in answer or 'L-REF1' in json.dumps(context, ensure_ascii=False)
    assert human.get('card', 'L-REF1') == 'L-REF1' and 'codex_internal_context' not in human_raw.decode('utf-8')
    assert not any((stage / name).exists() for name in ('run_001', 'reference_launch.json', 'reference_stdout.log', 'stop_requested.txt'))
    assert not any((author / name).exists() for name in ('source_publication_receipt.json', 'root_publication_terminal_confirmation.json', 'direct_human_reply.json', 'authorization.json'))
    assert protocol['schema_version'] == 'partial-saved-state-independent-reference-card-1.0'
    assert protocol['installed'] is False and 'install_sources' not in protocol
    reply = dict(human, card='L-REF1', authorized_execution_source_commit=HEAD)
    reply_raw = (json.dumps(reply, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    authorization = dict(card='L-REF1', authorized=True, authorization_from_direct_human_reply=True,
        direct_human_answer=answer, reply_context=context, authorized_execution_source_commit=HEAD,
        source_commit_association='Actual published source; does not claim the human literally approved a commit hash',
        protocol_sha256=PROTOCOL, human_evidence_sha256=sha256(reply_raw).hexdigest(), original_human_context_sha256=sha256(human_raw).hexdigest(),
        source_publication_receipt_sha256=PROOF, root_publication_terminal_confirmation_sha256=CONFIRMATION,
        helper_seconds=900, outer_seconds=960, sampled_RSS_bytes=8 * 1024**3, one_invocation=True,
        created_utc=datetime.now(timezone.utc).isoformat())
    write(author / 'source_publication_receipt.json', proof_raw)
    write(author / 'root_publication_terminal_confirmation.json', confirmation_raw)
    write(author / 'direct_human_reply.json', reply_raw)
    write(author / 'authorization.json', (json.dumps(authorization, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(dict(status='actual_direct_human_authorization_recorded_not_launched', card='L-REF1', authorized_execution_source_commit=HEAD)))


if __name__ == '__main__':
    main()
