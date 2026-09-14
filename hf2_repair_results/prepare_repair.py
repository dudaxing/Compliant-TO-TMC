"""Freeze exact primitive inputs and baseline identities, without a nonlinear solve."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'hf_repo'
OUT = ROOT / 'hf2_repair_results'
VALIDATION = REPO / 'validation/hf2_repair'
sys.path.insert(0, str(REPO / 'src'))
from hf_eval.tmc_benchmark import cshape_preset

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

VALIDATION.mkdir(parents=True, exist_ok=True)
assert not (VALIDATION / 'strong_inputs.npz').exists(), 'Do not overwrite frozen primitive inputs'
model, force, _, loaded, config = cshape_preset()
py_path = ROOT / 'hf2_results/cshape_python_001/cshape_path.npz'
ma_path = ROOT / 'reference_validation/matlab/cshape_001/cshape_path.npz'
with np.load(py_path, allow_pickle=False) as py, np.load(ma_path, allow_pickle=False) as ma:
    U = np.array([py['U'][72], ma['U'][75], ma['U'][98]])
    levels = np.array([py['lambda'][72], ma['targets'].ravel()[75], ma['targets'].ravel()[98]])
    targets = ma['original_targets'].ravel().copy()
indices = np.arange(1, model.ndof + 1, dtype=float)
directions = np.array([np.sin(indices), np.cos(indices)])
directions[:, model.fixed_dofs] = 0
directions *= (np.sqrt(model.hx * model.hy) / np.linalg.norm(directions, axis=1))[:, None]
fixture = dict(model.ops, lam=model.lam, mu=model.mu, kr=np.array(model.kr),
               connectivity=model.connectivity, coordinates=model.coordinates, F0=force,
               fixed_dofs=model.fixed_dofs, solid=model.solid, hx=np.array(model.hx), hy=np.array(model.hy),
               thickness=np.array(model.thickness), U=U, levels=levels, directions=directions,
               targets=targets, loaded_nodes=loaded)
np.savez_compressed(VALIDATION / 'strong_inputs.npz', **fixture)
baseline_dir = OUT / 'baseline'
baseline_dir.mkdir(exist_ok=True)
baseline_revision = '281368bc0efc9d6f09e3a01af2f749a45ad9982d'
legacy = subprocess.check_output(['git', '-C', str(REPO), 'show', baseline_revision + ':src/hf_eval/tmc_kernel.py'])
(baseline_dir / 'tmc_kernel_0_2_0.py').write_bytes(legacy)
files = [py_path, ma_path, ROOT / 'hf2_results/cshape_final_decision.json',
         ROOT / 'deliverables/HF2_independent_evaluator_and_evidence.zip',
         ROOT / 'deliverables/HF2_release_manifest.json', ROOT / 'geometry_dataset/file_manifest.json',
         REPO / 'dist/independent_hf_evaluator-0.2.0-py3-none-any.whl',
         REPO / 'validation/hf2/validation_spec.json',
         VALIDATION / 'precision_spec.json', VALIDATION / 'strong_inputs.npz',
         baseline_dir / 'tmc_kernel_0_2_0.py']
record = {'baseline_git_commit': baseline_revision, 'no_nonlinear_solve': True,
          'fixture_primitive_source': 'Actual binary64 operators and interpolated coefficients of unchanged source preset',
          'case_ids': ['python_073', 'matlab_076', 'matlab_099'],
          'fixture_arrays': {k: {'shape': list(v.shape), 'dtype': str(v.dtype)} for k, v in fixture.items()},
          'files': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in files]}
write(OUT / 'frozen_inputs.json', record)
write(VALIDATION / 'input_manifest.json', record)
print(json.dumps({'status': 'prepared', 'fixture_sha256': sha(VALIDATION / 'strong_inputs.npz'),
                  'spec_sha256': sha(VALIDATION / 'precision_spec.json'), 'shapes': record['fixture_arrays']}, indent=2))
