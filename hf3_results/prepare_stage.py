"""Freeze HF3 task/validation inputs before numerical execution."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess

root = Path(__file__).resolve().parents[1]
repo = root/'hf_repo'
out = root/'hf3_results'
config = repo/'configs/hf3'
config.mkdir(parents=True, exist_ok=True)
(out/'baseline').mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, x):
    assert not p.exists(), p
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for family in ('inverter','gripper'):
    old=json.loads((root/f'geometry_dataset/tasks/{family}_linear_interface_smoke.json').read_text())
    task={**old,'schema_version':'hf-project-task-1.0','task_id':f'hf3_{family}_pilot_v1',
          'purpose':'nonlinear_displacement_pilot',
          'units':{'length':'mm','force':'N','stress':'MPa','energy':'N mm'},
          'third_medium':{'gamma':1e-6},'regularization':{'alpha':1e-6,'length_mm':80.0},
          'input':{'tag':'input','control':'average_displacement','target_mm':1.0},
          'background_symmetry':{'points_mm':[[0.,40.],[80.,40.]],'components':[1]},
          'diagnostic_variant':'none'}
    write(config/f'{family}_pilot_v1.json',task)
spec={'schema_version':'hf3-validation-1.0','created_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'Project average displacement and two-layer bridge; full paths conditional on independent gates',
 'bridge_amplitudes_mm':[1e-3,1e-4,1e-5], 'full_path_targets_mm':[i/40 for i in range(1,41)],
 'internal_relative_force_tolerance':1e-9,'external_relative_force_tolerance':1e-8,
 'force_evaluation_relative_budget':1e-9,'constraint_relative_tolerance':1e-10,
 'displacement_scale_floor_mm':1e-6,'force_scale_floor_factor':1e-8,
 'force_scale':'max(norm(fint_free),norm(bin_free*R),norm(k*bout_free*(bout.T*u)),1e-8*E*t*max(abs(d),1e-6))',
 'HP_reference':'50-digit exact promotion of actual binary64 primitive/u/R/b/k; common validation SF computed from HP terms',
 'precision_digits':50,'crosscheck_precision_digits':80,'precision_layer_tolerance':'1e-30',
 'force_balance_relative_tolerance':1e-6,'fixed_displacement_tolerance_mm':8e-11,
 'bridge_relative_tolerance':1e-4,'bridge_trend_ratio':5.,'bridge_trend_exempt_first_error':1e-6,
 'bridge_displacement_gain_floor':1e-6,'bridge_stiffness_floor_factor':1e-8,
 'linear_stiffness_relative_tolerance':1e-11,'linear_response_relative_tolerance':1e-9,
 'model_bias_flag_threshold':.05,'repeated_response_relative_tolerance':1e-10,
 'local_analytic_tolerance':1e-10,'local_directional_tolerance':1e-8,
 'max_checks':25,'max_backtracks':12,'max_bisections':4,'armijo_c':1e-4,
 'minimum_increment_rule':'initial target increment / 16',
 'resource_limits':{'total_seconds':2400,'category_seconds':{'preflight':120,'tests':300,'bridge':300,'hp':600,'isolated':120,'inverter_path':480,'gripper_path':480},
 'small_process_seconds':300,'memory_soft_limit_bytes':4*1024**3},
 'next_gate':'All first-layer/solid-reference/HP checks; any sign-changing or dominant model bias requires interpretation before full path',
 'HF4_authorized':False}
write(config/'validation_spec.json',spec)
files=[root/'geometry_dataset/file_manifest.json',root/'deliverables/HF2_repaired_evaluator_and_evidence.zip',root/'deliverables/HF2_repair_release_manifest.json',repo/'dist/independent_hf_evaluator-0.2.1-py3-none-any.whl']
baseline=out/'baseline/tmc_kernel_0_2_1.py'
baseline.write_bytes((repo/'src/hf_eval/tmc_kernel.py').read_bytes())
write(out/'baseline_manifest.json',{'git_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
 'files':[{'path':str(p.relative_to(root)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],
 'original_dataset_files':{p.relative_to(root/'geometry_dataset').as_posix():sha(p) for p in (root/'geometry_dataset').rglob('*') if p.is_file()},
 'kernel_copy_sha256':sha(baseline),'frozen_configs':{p.name:sha(p) for p in config.glob('*.json')}})
print('HF3 configurations and baseline evidence frozen')
