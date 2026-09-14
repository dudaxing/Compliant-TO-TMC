"""Prepare the existing independent-install workflow for the repaired wheel."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'hf2_results/detached_acceptance.py').read_text(encoding='utf-8')
source = source.replace('independent_hf_evaluator-0.2.0-', 'independent_hf_evaluator-0.2.1-')
source = source.replace("prefix='hf2_detached_'", "prefix='hf2_repair_detached_'")
source = source.replace('hf2_results/', 'hf2_repair_results/')
source = source.replace('run_hf2_isolated.py', 'run_hf2_repair_isolated.py')
source = source.replace("'--name','hf2_detached'", "'--name','hf2_repair_detached'")
source = source.replace('dirs_exist_ok=True', 'dirs_exist_ok=False')
source = source.replace('exact versions from runtime lock, offline uv cache; online require-hashes attempt retained separately after CDN timeout; installed RECORD hashes checked during replay',
                        'exact runtime lock versions from offline uv cache; third-party original archive hashes not reverified in this offline replay; installed RECORD hashes checked')
destination = ROOT / 'hf2_repair_results/detached_acceptance.py'
assert not destination.exists()
destination.write_text(source, encoding='utf-8')
print(destination)
