"""Bind the final verdict to its final provenance-enriched summary; no computation."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hf2_results'
decision_path = OUT / 'cshape_final_decision.json'
summary_path = OUT / 'residual_sensitivity_001/summary.json'
original = OUT / 'cshape_final_decision_initial.json'
decision = json.loads((original if original.exists() else decision_path).read_text(encoding='utf-8'))
summary = json.loads(summary_path.read_text(encoding='utf-8'))
old_sha = 'ed870004e41835a9be0da99a4373f4c74142f49cb1a0b219857f465df58d88d2'
current_sha = hashlib.sha256(summary_path.read_bytes()).hexdigest()
assert current_sha == 'e6884c74d7d0253ecc87e3fd1c4f630b2277c45e8463648c16d77f16cdc08872'
for failure, case in zip(decision['independent_equilibrium_failures'], summary['cases'], strict=True):
    for key in ('side', 'target_index', 'load_multiplier', 'stored_relative_free_residual'):
        assert failure[key] == case[key], key
    assert failure['independent_decimal50_relative_free_residual'] == case['decimal50']['relative_free_residual']
    assert failure['maximum_C_condition_number'] == case['conditioning']['max_cond_C']
if not original.exists():
    shutil.copy2(decision_path, original)
recovered = json.loads(summary_path.read_text(encoding='utf-8'))
recovered.pop('source_zip_sha256')
recovered.pop('provenance_note')
for key in (
    'reference_validation/matlab/source/assembleKtFi.m',
    'hf_repo/src/hf_eval/tmc_kernel.py',
    'hf_repo/scripts/compare_cshape.py',
    'hf2_results/residual_sensitivity_001/probe.py',
):
    recovered['inputs_sha256'].pop(key)
old_bytes = (json.dumps(recovered, indent=2, allow_nan=False) + '\n').replace('\n', '\r\n').encode('utf-8')
assert hashlib.sha256(old_bytes).hexdigest() == old_sha
recovered_path = summary_path.with_name('summary_before_provenance.json')
if recovered_path.exists():
    assert recovered_path.read_bytes() == old_bytes
else:
    recovered_path.write_bytes(old_bytes)
record = next(r for r in decision['evidence'] if r['path'] == 'hf2_results/residual_sensitivity_001/summary.json')
assert record['sha256'] == old_sha
record['sha256'] = current_sha
decision['evidence'].append({'path': recovered_path.relative_to(ROOT).as_posix(), 'sha256': old_sha})
history = {
    'initial_decision_record': original.relative_to(ROOT).as_posix(),
    'initial_decision_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
    'summary_sha256_recorded_before_provenance_enrichment': old_sha,
    'current_summary_sha256': current_sha,
    'change': 'Summary author added source_zip_sha256, provenance_note and four inputs_sha256 entries, with PowerShell JSON reserialization, after the initial verdict was written.',
    'verified_unchanged': 'All three case identities, stored residuals, exact Decimal50 residual strings and maximum C condition numbers match the earlier verdict. No path or raw array changed in this metadata reconciliation.',
    'recovered_original_summary': recovered_path.relative_to(ROOT).as_posix(),
    'recovery': 'Removing the added provenance fields and restoring the original Python JSON formatting with Windows CRLF exactly reproduces the old SHA-256. Original numerical fields are preserved.',
    'scientific_verdict_changed': False,
}
decision['provenance_reconciliation'] = history
decision_path.write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding='utf-8')
(OUT / 'provenance_reconciliation.json').write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(history, ensure_ascii=False, indent=2))
