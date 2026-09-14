"""Write the reviewed validation rules once, before new mechanics computations."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
original_path = ROOT / 'hf_repo/validation/hf2/validation_spec.json'
original = json.loads(original_path.read_text(encoding='utf-8'))
destination = ROOT / 'hf_repo/validation/hf2_repair/precision_spec.json'
assert not destination.exists(), 'Never overwrite the frozen repair specification'
spec = {
    'schema_version': 'hf2-precision-repair-1.0',
    'frozen_date': '2026-09-13',
    'authorization': 'User requested reviewed diagnosis and execution before HF3; conditional single corrected path after local gates',
    'implementation_version': '0.2.1', 'kernel_version': 'p26_q1_direct_piola_huhu_v2',
    'solver_profile': 'hf2_precision_v2', 'internal_newton_tolerance': 1e-9,
    'external_residual_tolerance': 1e-8,
    'case_ids': ['python_073', 'matlab_076', 'matlab_099'],
    'direction_ids': ['canonical_sin_free_normalized_sqrt_hxhy', 'canonical_cos_free_normalized_sqrt_hxhy'],
    'direction_definition': 'one-based DOF radians; fixed DOFs zero; Euclidean norm then scale sqrt(hx*hy); stored binary64 arrays are authoritative',
    'fd_multipliers': [1, .1, .01, .001, .0001],
    'fd_base_step': '.99*min(1, min_q J0/(8*abs(a)), min_q sqrt(J0/(8*abs(b)))); ignore zero denominators; a=cof(F):dF,b=det(dF); Decimal50 ideal inputs',
    'positive_J_ratio': .5,
    'precision': 50, 'reference_precision_check': 80,
    'reference_precision_tolerance': 1e-30,
    'directional_tolerance': 1e-8,
    'residual_force_budget': 1e-9,
    'component_force_tolerance': 1e-8,
    'component_denominator': 'max(norm(HP component),1e-8*norm(load_multiplier*F0))',
    'force_budget_applies_to': ['full', 'free'],
    'fd_double_best_tolerance': 1e-6, 'fd_decimal_best_tolerance': 1e-8,
    'fd_early_reduction': 20, 'fd_early_applies_above': 1e-9,
    'force_scale': 'Euclidean norm of exact binary64 multiplier times exact binary64 F0, formed in reference precision',
    'input_contract': 'Decimal.from_float on saved actual primitive grad/hessian/weights/lam/mu/kr/u/direction; no promotion of precomputed binary64 F,J,or element forces as full reference',
    'path_validation': {
        'high_precision_digits': 50, 'crosscheck_precision_digits': 80,
        'crosscheck_indices': [0, 49, 99], 'crosscheck_force_tolerance': '1e-30',
        'external_residual_tolerance': 1e-8, 'evaluation_error_tolerance': 1e-9,
        'expected_original_targets': 100,
        'include_all_new_accepted_substeps': True,
        'old_paths_scope': 'All 100 original Python and all 100 original MATLAB states; report actual failures without hardcoding the old failure count',
        'closure': 'New complete path, all new high-precision validity and force-budget gates, original seven response-parity gates; old reference failures retained separately',
    },
    'original_cshape_tolerances': original['cshape'],
    'original_validation_spec': original,
    'original_validation_spec_sha256': hashlib.sha256(original_path.read_bytes()).hexdigest(),
    'resource_limits': {
        'total_numerical_seconds': 3000, 'small_cumulative_seconds': 1200,
        'small_process_seconds': 300, 'corrected_python_path_attempts': 1,
        'corrected_python_path_seconds': 1200, 'postprocess_cumulative_seconds': 600,
        'sampled_process_tree_rss_soft_limit_bytes': 4294967296,
        'installation_counted_separately': True,
    },
    'scope': 'Close numerical expression and equilibrium accuracy of the specified discrete source-numeric benchmark; no HF3 or physical contact validation',
}
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(spec, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
print(hashlib.sha256(destination.read_bytes()).hexdigest())

# Keep the previous monitor and ledger immutable. The new runner enforces this stage's caps.
monitor = (ROOT / 'hf2_results/run_budgeted.py').read_text(encoding='utf-8')
monitor = monitor.replace("ROOT / 'hf2_results/resource_jobs'", "ROOT / 'hf2_repair_results/resource_jobs'")
monitor = monitor.replace("['small','compile','matlab_cshape','python_cshape','isolated']", "['small','compile','python_cshape','isolated','postprocess']")
monitor = monitor.replace("if j['category'] == 'small'", "if j['category'] in ['small','compile','isolated']")
monitor = monitor.replace("category_cap = 300 if args.category in ['small','isolated'] else 600 if args.category == 'compile' else 1200", "category_cap = 300 if args.category in ['small','compile','isolated'] else 600 if args.category == 'postprocess' else 1200")
monitor = monitor.replace('3600 - used', '3000 - used')
monitor = monitor.replace("if args.category == 'small':", "if args.category in ['small','compile','isolated']:")
monitor = monitor.replace("if limit <= 0:", "if args.category == 'postprocess':\n    limit = min(limit, 600 - sum(j.get('wall_seconds', j.get('reserved_limit_seconds',0)) for j in prior if j['category']=='postprocess'))\nif args.category == 'python_cshape' and any(j['category']=='python_cshape' for j in prior):\n    raise SystemExit('The single corrected full-path attempt has already been used')\nif limit <= 0:")
(ROOT / 'hf2_repair_results/run_budgeted.py').write_text(monitor, encoding='utf-8')
