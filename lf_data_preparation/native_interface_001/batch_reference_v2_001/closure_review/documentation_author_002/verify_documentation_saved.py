"""Narrow stdlib-only documentation review; no candidate or scientific imports."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from urllib.parse import unquote

REPO = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
PREIMAGE_COMMIT = '30fcce9c41ceeb04b4490d6249e171f79f56e0ba'
BASE = 'lf_data_preparation/native_interface_001/'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def subset(expected, actual):
    if isinstance(expected, dict):
        assert isinstance(actual, dict)
        for key, value in expected.items():
            assert key in actual, key
            subset(value, actual[key])
    else:
        assert expected == actual, (expected, actual)

manifest = read_json(AUTHOR / 'manifest.json')
snapshot = read_json(AUTHOR / 'data_snapshot.json')
assert sha((AUTHOR / 'manifest.json').read_bytes()) == '90d743ee0390fa99fe0223450261369708c5cf6c272134f41585727b1422fe6a'
assert sha((AUTHOR / 'data_snapshot.json').read_bytes()) == manifest['data_snapshot_sha256']
assert sha((AUTHOR / 'RESULTS.md').read_bytes()) == manifest['report_sha256']

fronts = {}
links = []
for relative, identity in manifest['front_updates'].items():
    old = subprocess.run(['git', 'show', f'{PREIMAGE_COMMIT}:{relative}'], cwd=REPO, check=True, capture_output=True).stdout
    candidate = (AUTHOR / 'fronts' / relative).read_bytes()
    prefix = (AUTHOR / 'prefixes' / relative).read_bytes()
    assert sha(old) == identity['preimage_sha256'], relative
    assert sha(candidate) == identity['candidate_sha256'], relative
    assert candidate.startswith(prefix), relative
    assert candidate.count(old) == 1, relative
    offset = candidate.index(old)
    assert b'<details>' in candidate[len(prefix):offset], relative
    assert candidate[offset:offset + len(old)] == old
    assert b'</details>' in candidate[offset + len(old):]
    assert (REPO / relative).read_bytes() == candidate, relative
    decoded = candidate.decode('utf-8', errors='strict')
    assert '\ufffd' not in decoded, relative
    fronts[relative] = {**identity, 'preimage_commit': PREIMAGE_COMMIT,
        'old_byte_length': len(old), 'old_contiguous_offset': offset,
        'old_occurrences': 1, 'formal_current_matches_candidate': True,
        'strict_utf8': True, 'replacement_codepoint_present': False}
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', prefix.decode('utf-8')):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        resolved = ((REPO / relative).parent / unquote(target.strip('<>').split('#', 1)[0])).resolve()
        assert resolved.exists(), (relative, target)
        links.append({'document': relative, 'target': target, 'exists': True})

# External report remains archive only; links resolve against its declared target.
for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', (AUTHOR / 'RESULTS.md').read_text(encoding='utf-8')):
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
        continue
    assert ((REPO / manifest['report_target']).parent / unquote(target.strip('<>').split('#', 1)[0])).resolve().exists(), target
    links.append({'document': 'RESULTS.md', 'target': target, 'exists': True})
assert len(links) == 63
assert links == snapshot['relative_links'] or sorted(links, key=lambda x: (x['document'], x['target'])) == sorted(snapshot['relative_links'], key=lambda x: (x['document'], x['target']))

ref_review_rel = BASE + 'batch_reference_v2_001/closure_review/dual_saved_review.json'
view_review_rel = BASE + 'batch_saved_view_v2_001/closure_review/saved_closure_review.json'
actual_sources = {}
for relative in (ref_review_rel, view_review_rel,
                 BASE + 'batch_forward_001/run_001/view_execution_receipt.json',
                 BASE + 'batch_saved_view_v2_001/view_launch.json'):
    raw = (REPO / relative).read_bytes()
    actual_sources[relative] = sha(raw)
    assert actual_sources[relative] == snapshot['source_pins'][relative]
subset(snapshot['closed_review'], read_json(REPO / ref_review_rel))
subset(snapshot['view_closed_review'], read_json(REPO / view_review_rel))
subset(snapshot['view'], read_json(REPO / (BASE + 'batch_forward_001/run_001/view_execution_receipt.json')))
subset(snapshot['view_outer'], read_json(REPO / (BASE + 'batch_saved_view_v2_001/view_launch.json')))

case_facts = {}
for label, case in snapshot['cases'].items():
    receipt_rel = BASE + f'batch_reference_v2_001/run_001/audit/{label}/execution_receipt.json'
    response_rel = BASE + f'batch_forward_001/run_001/qualified_response_{label}.json'
    metadata_rel = BASE + f'batch_forward_001/run_001/view/{label}/view_metadata.json'
    for relative in (receipt_rel, response_rel, metadata_rel):
        actual_sources[relative] = sha((REPO / relative).read_bytes())
        assert actual_sources[relative] == snapshot['source_pins'][relative]
    receipt = read_json(REPO / receipt_rel)
    subset(case['reference_receipt'], receipt)
    response = read_json(REPO / response_rel)
    for key in ('target_response', 'independent_reference', 'views'):
        subset(case[key], response[key])
    metadata = read_json(REPO / metadata_rel)
    subset(case['display'], metadata['display'])
    subset(case['media'], metadata['media'])
    case_facts[label] = {'reference_receipt': case['reference_receipt'],
        'target_response': case['target_response'], 'display_frames': case['display']['actual_frame_count'],
        'display_scales': [case['display']['geometry_scale'], case['display']['supplementary_displacement_scale']],
        'independent_reference_status': response['independent_reference']['status'],
        'view_status': response['views']['status'], 'own_link_count': len(response['views']['links'])}

report = {
    'schema_version': 'native-batch-v2-documentation-peer-review-1.0',
    'status': 'pass_saved_only', 'blocking_findings': [],
    'reviewed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'proposal_manifest_sha256': sha((AUTHOR / 'manifest.json').read_bytes()),
    'data_snapshot_sha256': sha((AUTHOR / 'data_snapshot.json').read_bytes()),
    'external_results_sha256': sha((AUTHOR / 'RESULTS.md').read_bytes()),
    'front_updates': fronts, 'local_links_checked': len(links),
    'actual_closed_records_sha256': actual_sources, 'case_facts': case_facts,
    'findings': [
        'All five original preimages from Git 30fcce9 remain exactly once as contiguous bytes inside their folded historical sections; installed fronts equal the reviewed candidates.',
        'Five current prefixes and external report have 63 existing local links. All candidate front bytes are strict UTF-8 without replacement codepoints.',
        'Per-case four states, eight new HP calls and four saved frames, two own links, and documented timings match actual terminal records and existing closed reviews; no previous scientific identity sweep was repeated.',
        'Fine reference execution-receipt helper time 420.870184 s is distinct from lifecycle time 420.713510 s; the report uses the stated execution-receipt field.',
        'Current no-workpiece examples do not grant mesh convergence, rankings, contact/clamping, pressure, all-column HP, energy/stress/strain HP or complete HF5 qualification. Existing fixed-body capabilities and their separate historical evidence are correctly distinguished.',
        'External RESULTS.md is for raw archiving only and does not replace the actual formal phase reports; Git publication is not claimed before the parent publication step.'
    ],
    'scope': 'Text, JSON and ordinary byte/hash review only; zero candidate imports, arrays, HF/model/F/T/solver/HP, observations, plotting/rendering, or formal writes.',
    'activities': {'scientific_recheck': False, 'formal_writes': 0, 'prior_290_or_347_identity_sweep_repeated': False}
}
(AUTHOR / 'peer_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'report_path': str(AUTHOR / 'peer_review.json'),
    'report_sha256': sha((AUTHOR / 'peer_review.json').read_bytes()), 'local_links_checked': len(links),
    'fronts_reviewed': len(fronts)}, ensure_ascii=False))
