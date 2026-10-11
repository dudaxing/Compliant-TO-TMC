"""Archive an actual human M-BOUND1 approval before one numerical invocation.

This script is an audit writer, not a source of authorization. Root must first
receive a direct human reply in the current thread; an automatic goal
continuation, an existing file or an approval of another card is insufficient.
Do not invoke this script during source/tool preparation.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
STAGE = ROOT/REL
BASE = 'eb68c00d50b28de89a475c18a0879be4a4482f68'
SOURCE = Path('D:/hf-native-workpiece-api-author-20261009/MBOUND1_source_prepare_001/publication_receipt.json')
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
git = lambda *args: subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--human-evidence',type=Path,required=True,
        help='Root-provided JSON of the actual direct human reply, never a generated approval.')
    args = parser.parse_args()
    evidence = read(args.human_evidence)
    assert evidence['card'] == 'M-BOUND1' and evidence['approved_source_commit'] == BASE
    assert evidence['authorization_from_direct_human_reply'] is True
    assert evidence['direct_human_answer'].strip() and evidence['reply_context'].strip()
    assert git('rev-parse','HEAD') == BASE and not git('status','--porcelain')
    assert git('branch','--show-current') == 'main'
    assert git('remote','get-url','origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
    protocol = read(STAGE/'protocol.json')
    assert sha(STAGE/'protocol.json') == 'f27d201b01efc5c49212a43536e928ba6ac88ba4346ac6949dccdfcac8d94e33'
    assert len(protocol['bindings']) == 45
    assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
    assert not (ROOT/protocol['output_directory']).exists()
    assert not any((STAGE/name).exists() for name in ('hu_boundary_launch.json','hu_boundary_stdout.log','stop_requested.txt'))
    prior = read(SOURCE)
    assert prior['status'] == 'published_and_incrementally_restored_pass' and prior['published_commit'] == BASE
    assert prior['source_and_restore_clean'] and not prior['authorized'] and not prior['executed']
    authorization = dict(status='direct_human_authorization_recorded_before_one_execution',
        recorded_utc=datetime.now(timezone.utc).isoformat(),approved_source_commit=BASE,
        direct_human_answer=evidence['direct_human_answer'],reply_context=evidence['reply_context'],
        questionItemId=evidence.get('questionItemId'),human_evidence_sha256=sha(args.human_evidence),
        card=protocol['card'],card_sha256=sha(ROOT/protocol['card']),protocol_sha256=sha(STAGE/'protocol.json'),
        authorized=True,executed_at_record=False,
        resource=dict(helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=8589934592),
        scope='Original loading states6/13; nine original files/two saved Hu fields/two public observations; body-only original C-order scatter, old nodal-L1 and distinct new selected-local-L1; 1444/10/2/1406/24/14 rows and two reference PNGs.',
        stop_rule='Once, first error, no retry/repair-rerun/extension/force; no force-kernel/tangent/HP/equilibrium/pressure/grip qualification',
        historical_protocol_false_flags='Frozen preparation history; actual approval is this separate direct-human record.')
    assert not (STAGE/'author/M_BOUND1_source_publication_receipt.json').exists()
    assert not (STAGE/'author/direct_human_reply.json').exists()
    with (STAGE/'author/authorization.json').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(authorization,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (STAGE/'author/direct_human_reply.json').write_bytes(args.human_evidence.read_bytes())
    (STAGE/'author/M_BOUND1_source_publication_receipt.json').write_bytes(SOURCE.read_bytes())
    print(json.dumps(dict(status=authorization['status'],approved_source_commit=BASE,bindings_checked=45)))

if __name__ == '__main__':
    main()
