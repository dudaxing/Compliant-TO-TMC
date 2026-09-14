"""Read-only verification of HF-0 deliverable references and original file hashes."""
from pathlib import Path
import hashlib
import json
import re

root = Path(__file__).resolve().parents[1]
sources = json.loads((root / 'hf0_audit/environment/source_inventory.json').read_text(encoding='utf-8'))
hashes = []
for source in sources:
    path = Path(source['source_path_record_only'])
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    hashes.append({'path_record_only': str(path), 'sha256': actual, 'unchanged': actual == source['sha256']})
broken = []
checked = 0
for document in sorted((root / 'docs').glob('*.md')):
    for match in re.finditer(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
        href = match.group(1).strip('<>')
        if href.startswith(('http:', 'https:', '#')):
            continue
        checked += 1
        if not (document.parent / href).exists():
            broken.append({'document': str(document.relative_to(root)), 'target': href})
lf = json.loads((root / 'hf0_audit/lf/audit_summary.json').read_text(encoding='utf-8'))
tmc = json.loads((root / 'hf0_audit/tmc/probe_tmc_results.json').read_text(encoding='utf-8'))
checks = {
    'five_supplied_files_unchanged': all(x['unchanged'] for x in hashes),
    'all_six_delivery_documents_present': all((root / 'docs' / x).is_file() for x in [
        'HF0_REPORT.md', 'DATA_CONTRACT_DRAFT.md', 'HF1_PLAN.md', 'LF_SNAPSHOT_AUDIT.md',
        'PAPER_FORMULATION_AUDIT.md', 'TMC_SOURCE_AUDIT.md']),
    'all_local_markdown_links_resolve': not broken,
    'lf_strict_data_refs_resolve': not lf['strict_data_reference_failures'],
    'lf_two_mapping_samples_match_source': all(x['mask_source_match'] and x['mask_digest_matches'] for x in lf['selected']),
    'lf_outlines_closed_and_area_matches': lf['all_outlines_closed'] and lf['all_outline_areas_match_masks'],
    'latest_handoff_18_plus_12': lf['handoff_counts']['v2/inverter'] == 18 and lf['handoff_counts']['v2/gripper'] == 12,
    'cshape_equilibrium_not_run': tmc['cshape_setup']['full_Cshape_solve_run'] is False,
}
report = {'scope': 'HF-0 artifact verification only; not scientific or HF evaluator validation',
          'checks': checks, 'source_hashes': hashes, 'local_links_checked': checked, 'broken_links': broken}
(root / 'hf0_audit/delivery_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'checks': checks, 'broken_links': broken, 'local_links_checked': checked}, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
