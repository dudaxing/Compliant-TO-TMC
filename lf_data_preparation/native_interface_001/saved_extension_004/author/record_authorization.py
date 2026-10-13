"""Archive actual future human reply and actual prepared-source proof; never invent them."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import json
from preparation_common import REL,CARD,git,raw,read,sha,new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--source-publication-receipt',type=Path,required=True)
    parser.add_argument('--human-reply',type=Path,required=True)
    args = parser.parse_args(); root = args.repo.resolve(); stage = root/REL
    proof_file,reply_file = args.source_publication_receipt.resolve(),args.human_reply.resolve()
    proof,reply,protocol = read(proof_file),read(reply_file),read(stage/'protocol.json')
    head = git(root,'rev-parse','HEAD').decode().strip(); assert not git(root,'status','--porcelain')
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared_card'] == CARD
    assert proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    assert proof['published_commit'] == reply['approved_source_commit'] == head
    assert proof['protocol_sha256'] == sha(stage/'protocol.json')
    assert reply['card'] == CARD and reply['authorization_from_direct_human_reply'] is True
    assert isinstance(reply['direct_human_answer'],str) and reply['direct_human_answer'].strip() and reply['reply_context']
    assert protocol['card'] == CARD and protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert not any((stage/name).exists() for name in ('run_001','production_launch.json','production_stdout.log','stop_requested.txt'))
    for name in ('authorization.json','direct_human_reply.json','source_publication_receipt.json'): assert not (stage/'author'/name).exists()
    new(stage/'author/source_publication_receipt.json',raw(proof_file)); new(stage/'author/direct_human_reply.json',raw(reply_file))
    new(stage/'author/authorization.json',dict(card=CARD,authorized=True,authorization_from_direct_human_reply=True,
        approved_source_commit=head,protocol_sha256=sha(stage/'protocol.json'),direct_human_answer=reply['direct_human_answer'],
        controller_seconds=9000,viewer_seconds=600,helper_seconds=10200,outer_seconds=10260,sampled_RSS_bytes=8*1024**3,
        human_evidence_sha256=sha(stage/'author/direct_human_reply.json'),source_publication_receipt_sha256=sha(proof_file),recorded_utc=datetime.now(timezone.utc).isoformat(),
        selected_state_index=1,original_target_indices=list(range(16,25)),targets_mm=protocol['targets_mm'],expected_API_calls=1,
        expected_accepted_states_minimum=9,expected_new_PNGs=3,actual_N_GIF_frames=True,postrun_new_PNG_pixel_QA_maximum=3,new_GIF_postrun_decode=0,
        tests_candidate_copies_installations_HP=0,no_retry_repair_extension_force_rollback_delete=True,
        full_original_path_completed=False,full_extended_path_completed=False,pressure_or_effective_grip_qualification=False))
    print(json.dumps(dict(status='actual_human_authorization_recorded',card=CARD,approved_source_commit=head,files=3,science_execution=0)))


if __name__ == '__main__': main()
