"""Installed-wheel HF1/HF3 A–B–A acceptance under explicit source-access denial."""
from pathlib import Path
import argparse
import base64
from contextlib import redirect_stdout
import hashlib
import importlib.abc
import importlib.metadata
import json
import os
import sys

p = argparse.ArgumentParser()
p.add_argument('--repository', type=Path, required=True)
p.add_argument('--dataset', type=Path, required=True)
p.add_argument('--reference', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--forbid', action='append', required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
forbidden = [os.path.normcase(os.path.abspath(x)) for x in a.forbid]
opened, denied, blocked = set(), [], []
def within(path, parent):
    try:
        return os.path.commonpath([path, parent]) == parent
    except ValueError:
        return False
def audit(event, arguments):
    if event not in {'open', 'os.listdir', 'os.scandir'} or not arguments:
        return
    candidate = arguments[0]
    if not isinstance(candidate, (str, bytes, os.PathLike)):
        return
    path = os.path.normcase(os.path.abspath(os.fsdecode(candidate)))
    if any(within(path, x) for x in forbidden):
        denied.append({'event': event, 'path': path})
        raise PermissionError('Original LF/HF/source paths forbidden in detached HF3 acceptance')
    if event == 'open':
        opened.add(path)
class NoLF(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0].casefold() in {'dmftd', 'mma', 'auto', 'matlab'}:
            blocked.append(fullname)
            raise ImportError('LF/MATLAB imports forbidden')
sys.addaudithook(audit)
sys.meta_path.insert(0, NoLF())
import numpy as np
import hf_eval
from hf_eval.evaluation import implementation_hash

checks = []
def check(name, passed, detail=None):
    checks.append(dict(name=name, status='pass' if bool(passed) else 'not_pass', detail=detail))
check('installed_package_not_checkout', not within(str(Path(hf_eval.__file__).resolve()), str(a.repository.resolve())))
check('package_version', hf_eval.__version__ == '0.3.0')
check('distribution_version', importlib.metadata.version('independent-hf-evaluator') == '0.3.0')
index = json.loads((a.dataset/'dataset_index.json').read_text())
canonical = {r['case_family']: r for r in index['canonical_subset']}
for label, family in [('A1', 'inverter'), ('B', 'gripper'), ('A2', 'inverter')]:
    item = canonical[family]
    result = hf_eval.evaluate(a.dataset/item['geometry_path'], a.dataset/item['task_path'],
                              a.dataset/index['solver_path'], a.output/('linear_'+label))
    check('HF1_'+label+'_success', result['numerics']['status'] == 'success')
with np.load(a.output/'linear_A1/fields.npz', allow_pickle=False) as first, np.load(a.output/'linear_A2/fields.npz', allow_pickle=False) as last:
    check('HF1_A_B_A_bitwise', all(np.array_equal(first[k], last[k]) for k in first.files))
with np.load(a.reference, allow_pickle=False) as z:
    reference = {k: z[k] for k in z.files}
check('development_reference_source', implementation_hash() == str(reference['source_sha256']))

# The public CLI must explicitly enable x64, even if the incoming environment
# has disabled it. HF1 above has not imported the JAX-backed project modules.
os.environ['JAX_ENABLE_X64'] = 'false'
for label, family in [('A1', 'inverter'), ('B', 'gripper'), ('A2', 'inverter')]:
    task = json.loads((a.repository/f'configs/hf3/{family}_pilot_v1.json').read_text())
    task['input']['target_mm'] = 1e-5
    task['task_id'] += '_isolated_1e-5'
    solver = dict(schema_version='hf-project-solver-1.0', solver_id='hf3_isolated_v1',
        analysis='tmc_average_displacement', targets_mm=[1e-5],
        settings=dict(minimum_increment=1e-5/16, time_limit_seconds=30.))
    out = a.output/('project_'+label)
    if label == 'A1':
        from hf_eval.__main__ import main
        taskfile, solverfile = a.output/'task_A1.json', a.output/'solver_A1.json'
        taskfile.write_text(json.dumps(task)); solverfile.write_text(json.dumps(solver))
        with (a.output/'cli_stdout.json').open('w', encoding='utf-8') as handle, redirect_stdout(handle):
            code = main(['evaluate', str(a.dataset/canonical[family]['geometry_path']), '--task', str(taskfile),
                         '--solver', str(solverfile), '--output', str(out)])
        check('public_CLI_exit', code == 0)
        result = json.loads((out/'result.json').read_text())
    else:
        result = hf_eval.evaluate(a.dataset/canonical[family]['geometry_path'], task, solver, out)
    check('HF3_'+label+'_success', result['numerics']['status'] == 'success')
    check('HF3_'+label+'_qualification_pending', result['qualification']['status'] == 'pending')
    check('HF3_'+label+'_functionality_undefined', result['functionality']['status'] == 'not_evaluated')
    if result['numerics']['status'] == 'success':
        with np.load(out/'path.npz', allow_pickle=False) as z:
            for key in ('u', 'R_input', 'q_out', 'J'):
                actual, expected = np.asarray(z[key][-1]), reference[family+'_'+key]
                relative = float(np.linalg.norm(actual-expected)/max(np.linalg.norm(expected), 1e-30))
                check('HF3_'+label+'_'+key+'_vs_development', relative <= 1e-10, relative)
with np.load(a.output/'project_A1/path.npz', allow_pickle=False) as first, np.load(a.output/'project_A2/path.npz', allow_pickle=False) as last:
    # Timing columns intentionally differ; all physical fields are compared.
    names = ('u', 'J', 'R_input', 'q_in', 'q_out', 'input_force', 'spring_force_on_structure',
             'force_residual', 'support_reaction', 'internal_force', 'material_internal_force',
             'regularization_internal_force', 'material_energy')
    check('HF3_A_B_A_physical_arrays_bitwise', all(np.array_equal(first[k], last[k]) for k in names))
record_results = []
for package in ('independent-hf-evaluator', 'numpy', 'scipy', 'jax', 'jaxlib', 'matplotlib'):
    dist = importlib.metadata.distribution(package)
    failed, counted = [], 0
    for entry in dist.files or []:
        if entry.hash is None or entry.hash.mode != 'sha256':
            continue
        digest = hashlib.sha256(Path(dist.locate_file(entry)).read_bytes()).digest()
        counted += 1
        if base64.urlsafe_b64encode(digest).rstrip(b'=').decode() != entry.hash.value:
            failed.append(str(entry))
    record_results.append(dict(package=package, version=dist.version, checked=counted, failed=failed))
    check(package+'_installed_RECORD', counted > 0 and not failed)
check('no_original_file_access', not denied, denied)
check('no_LF_import_attempt', not blocked, blocked)
summary = dict(status='pass' if all(x['status'] == 'pass' for x in checks) else 'not_pass', checks=checks,
    installed_package=str(Path(hf_eval.__file__).resolve()), source_sha256=implementation_hash(),
    record_checks=record_results, opened_paths=sorted(opened), denied_accesses=denied, blocked_imports=blocked,
    scope='HF1 and real-project tiny HF3 repeatability/installation; no new full path or physical accuracy certification')
(a.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(status=summary['status'], checks=len(checks))))
raise SystemExit(0 if summary['status'] == 'pass' else 2)
