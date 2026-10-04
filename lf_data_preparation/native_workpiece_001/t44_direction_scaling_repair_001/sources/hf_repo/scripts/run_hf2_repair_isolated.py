"""Detached 0.2.1 acceptance: old small checks plus three fixed-state HP checks.

The added precision checks evaluate the same frozen U and binary64 operators.
They do not solve or repair those old states and do not require their equilibrium
residuals to pass. No strong-state directional sweep or full C-shape is run.
"""
from pathlib import Path
import argparse
import base64
from decimal import Decimal, localcontext
import hashlib
import importlib.abc
import importlib.metadata
import importlib.util
import json
import os
import sys
from time import perf_counter


parser = argparse.ArgumentParser()
parser.add_argument('--repository', required=True)
parser.add_argument('--dataset', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--forbid', action='append', required=True)
args = parser.parse_args()
if any(not p.strip() for p in args.forbid):
    parser.error('At least one nonempty original source path must be forbidden')
repository = Path(args.repository).resolve()
dataset = Path(args.dataset).resolve()
output = Path(args.output).resolve()
output.mkdir(parents=True, exist_ok=False)
forbidden = [os.path.normcase(os.path.abspath(p)) for p in args.forbid]
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
    if any(within(path, parent) for parent in forbidden):
        denied.append({'event': event, 'path': path})
        raise PermissionError('Detached HF-2 repair forbids original source access')
    if event == 'open':
        opened.add(path)


class BlockReferenceImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0].casefold() in {'dmftd', 'mma', 'auto', 'matlab'}:
            blocked.append(fullname)
            raise ImportError('LF/MATLAB import forbidden in detached HF acceptance')


def load_helper(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f'Cannot load portable development helper {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


sys.addaudithook(audit)
sys.meta_path.insert(0, BlockReferenceImports())
start = perf_counter()
import numpy as np
import jax
import hf_eval
from hf_eval.evaluation import evaluate, implementation_hash
from hf_eval.tmc import rectangular_model, solve_path, NewtonSettings, TMCModel, assemble
from hf_eval import tmc_kernel, tmc_benchmark


validation = load_helper('portable_hf2_repair_validation', repository/'scripts/validate_hf2.py')
small = validation.run_validation(repository/'tests/fixtures/hf2',
                                  repository/'validation/hf2/validation_spec.json', output/'small')
targets = tmc_benchmark.validate_source_setup(repository/'validation/hf2/reference/cshape_setup.npz')
index = json.loads((dataset/'dataset_index.json').read_text(encoding='utf-8'))
records = {r['case_family']: r for r in index['canonical_subset']}
linear = []
for name, case in [('A1', 'inverter'), ('B', 'gripper'), ('A2', 'inverter')]:
    record = records[case]
    result = evaluate(dataset/record['geometry_path'], dataset/record['task_path'],
                      dataset/index['solver_path'], output/name)
    linear.append(result)
with np.load(output/'A1/fields.npz', allow_pickle=False) as first, np.load(output/'A2/fields.npz', allow_pickle=False) as last:
    linear_equal = {name: bool(np.array_equal(first[name], last[name])) for name in first.files}
model = rectangular_model(2, 1, 2, 1, fixed_dofs=[0, 1, 6, 7])
force = np.zeros(model.ndof)
force[[5, 11]] = -.1
a = solve_path(model, force, [.01, .02])
b = solve_path(model, 2*force, [.02])
a2 = solve_path(model, force, [.01, .02])


def strong_same_input_precision():
    """Exactly three HP base-state evaluations; no direction or offset argument."""
    begin = perf_counter()
    spec_path = repository/'validation/hf2_repair/precision_spec.json'
    fixture_path = repository/'validation/hf2_repair/strong_inputs.npz'
    helper_path = repository/'scripts/hf2_precision_reference.py'
    expected_spec_hash = 'ba4909b19d369890b79af8db8dfa58b01672e904fe68e8dc3175c408e23ad663'
    expected_fixture_hash = '60832407c9b8c1c91e79e89d993e6f77c4e3c7a87f60c585c737217c49698f60'
    if digest(spec_path) != expected_spec_hash or digest(fixture_path) != expected_fixture_hash:
        raise ValueError('Detached precision specification or frozen strong fixture hash mismatch')
    specification = json.loads(spec_path.read_text(encoding='utf-8'))
    precision = specification['precision']
    budget = specification['residual_force_budget']
    if isinstance(precision, bool) or precision != 50 or budget != 1e-9:
        raise ValueError('Detached repair requires the frozen precision=50 and residual_force_budget=1e-9')
    state_names = ('python_073', 'matlab_076', 'matlab_099')
    if specification['case_ids'] != list(state_names) or specification['force_budget_applies_to'] != ['full', 'free']:
        raise ValueError('Detached precision state ordering or force-budget scope mismatch')
    with np.load(fixture_path, allow_pickle=False) as source:
        fixture = {key: source[key] for key in source.files}
    required = {'grad', 'hessian', 'weights', 'points', 'lam', 'mu', 'kr',
                'connectivity', 'F0', 'fixed_dofs', 'U', 'levels',
                'coordinates', 'hx', 'hy', 'thickness'}
    if not required <= fixture.keys():
        raise ValueError(f'Strong fixture lacks required fields: {sorted(required-fixture.keys())}')
    for name in required:
        value = fixture[name]
        if value.dtype.kind not in 'iuf' or not np.all(np.isfinite(value)):
            raise ValueError(f'Strong fixture field {name} must be finite real ordinary data')
    ndof = fixture['F0'].size
    if fixture['U'].shape != (3, ndof) or fixture['levels'].shape != (3,):
        raise ValueError('Strong acceptance requires exactly three full-DOF base states')
    expected_levels = np.array([.73, .76, .99])
    if not np.allclose(fixture['levels'], expected_levels, rtol=0, atol=2e-15):
        raise ValueError('Strong fixture levels differ from the three frozen source states')
    helper = load_helper('portable_hf2_precision_reference', helper_path)
    reference = helper.DecimalQ1Reference(fixture, precision=precision)
    strong_model = TMCModel(coordinates=fixture['coordinates'], connectivity=fixture['connectivity'],
                           lam=fixture['lam'], mu=fixture['mu'], kr=float(fixture['kr']),
                           hx=float(fixture['hx']), hy=float(fixture['hy']), thickness=float(fixture['thickness']),
                           solid=fixture['solid'], fixed_dofs=fixture['fixed_dofs'])
    same_operators = {key: bool(strong_model.ops[key].dtype == fixture[key].dtype
                               and strong_model.ops[key].shape == fixture[key].shape
                               and strong_model.ops[key].tobytes(order='C') == fixture[key].tobytes(order='C'))
                      for key in ('grad', 'hessian', 'weights', 'points')}
    if not all(same_operators.values()):
        raise ValueError('Installed model operators differ from the frozen HP binary64 primitives')
    if not np.array_equal(strong_model.free, reference.free):
        raise ValueError('Installed model free-DOF selection differs from HP reference')
    rows, numeric = [], {}
    hp_calls = 0
    for state_index, (case_id, u, level) in enumerate(zip(state_names, fixture['U'], fixture['levels'])):
        hp = reference.evaluate(u, float(level))
        hp_calls += 1
        force_scale = hp['force_scale_decimal']
        if force_scale <= 0:
            raise ValueError('Frozen strong-state external-force norm must be positive')
        # Rounded views are saved for plotting only, never used for the HP error.
        numeric[case_id+'_u'] = u.copy()
        numeric[case_id+'_HP_internal_float_view'] = hp['internal']
        for tangent in (True, False):
            _, internal, fields = assemble(strong_model, u, tangent=tangent)
            force_checks = {}
            for selection, indices in [('full', None), ('free', reference.free)]:
                measured = helper.compare_float_to_decimal(internal, hp['internal_decimal'],
                            floor=force_scale, indices=indices, precision=precision)
                with localcontext() as context:
                    context.prec = precision
                    absolute = Decimal(measured['absolute_error_decimal'])
                    expression_error = absolute/force_scale
                    passed = expression_error <= Decimal(str(budget))
                force_checks[selection] = {
                    'absolute_force_error': float(absolute), 'absolute_force_error_decimal': str(absolute),
                    'expression_error': float(expression_error), 'expression_error_decimal': str(expression_error),
                    'residual_force_budget': budget, 'status': 'pass' if passed else 'fail'}
            mode = 'tangent' if tangent else 'residual_only'
            numeric[case_id+'_'+mode+'_internal'] = internal
            row = {'case_id': case_id, 'state_index': state_index, 'load_multiplier': float(level),
                   'kernel_mode': mode, 'force_checks': force_checks,
                   'force_scale_decimal': str(force_scale),
                   'status': 'pass' if all(c['status'] == 'pass' for c in force_checks.values()) else 'fail',
                   'minimum_J': float(np.min(fields['J'])),
                   'old_state_HP_relative_equilibrium_residual_decimal': hp['relative_residual'],
                   'old_state_equilibrium_is_acceptance_criterion': False}
            rows.append(row)
    details = {'schema_version': 'hf2-repair-isolated-precision-1.0',
               'scope': 'same frozen binary64 inputs; expression error only; old states are not equilibrium acceptance cases',
               'status': 'pass' if len(rows) == 6 and all(row['status'] == 'pass' for row in rows) else 'fail',
               'precision': precision, 'residual_force_budget': budget,
               'comparison_formula': 'norm(D(production_internal_selection)-HP_internal_selection)/norm(D(level)*D(F0)); selection=full/free',
               'assembly': 'installed production TMCModel and assemble; each generated operator exactly matches the frozen binary64 primitive',
               'operators_bitwise_equal': same_operators,
               'HP_base_state_calls': hp_calls, 'HP_direction_calls': 0, 'full_Cshape_runs': 0,
               'fixture_sha256': digest(fixture_path), 'precision_spec_sha256': digest(spec_path),
               'helper_sha256': digest(helper_path), 'rows': rows, 'wall_seconds': perf_counter()-begin}
    np.savez_compressed(output/'strong_precision_numeric_views.npz', **numeric)
    (output/'strong_precision.json').write_text(json.dumps(details, indent=2, allow_nan=False), encoding='utf-8')
    return details


try:
    strong = strong_same_input_precision()
except Exception as error:
    strong = {'status': 'fail', 'exception_type': type(error).__name__, 'reason': str(error),
              'scope': 'three fixed-state expression checks; no equilibrium or full-path claim'}
    (output/'strong_precision.json').write_text(json.dumps(strong, indent=2, allow_nan=False), encoding='utf-8')

installed = {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}
record_files, record_failures = 0, []
for distribution in importlib.metadata.distributions():
    for entry in distribution.files or []:
        if entry.hash is None:
            continue
        with distribution.locate_file(entry).open('rb') as stream:
            entry_digest = hashlib.file_digest(stream, entry.hash.mode).digest()
        actual = base64.urlsafe_b64encode(entry_digest).decode().rstrip('=')
        record_files += 1
        if actual != entry.hash.value:
            record_failures.append(str(entry))

# These are the original helper's 17 checks, preserved separately for comparison.
legacy_checks = {
    'small_reference_all_checks_pass': small['status'] == 'pass',
    'source_setup_matches_independent_preset': len(targets) == 100 and targets[-1] == 1,
    'HF1_three_linear_analyses_succeed': all(r['numerics']['status'] == 'success' for r in linear),
    'HF1_A_B_A_all_arrays_bitwise_equal': all(linear_equal.values()),
    'HF1_fresh_evaluation_ids': len({r['evaluation_id'] for r in linear}) == 3,
    'TMC_small_three_paths_succeed': all(r['status'] == 'success' for r in [a, b, a2]),
    'TMC_A_B_A_displacement_bitwise_equal': bool(np.array_equal(a['u'], a2['u'])),
    'TMC_different_load_changes_result': not np.array_equal(a['u'], b['u']),
    'isolated_python': bool(sys.flags.isolated and sys.flags.no_user_site),
    'CPU_float64': jax.default_backend() == 'cpu' and bool(jax.config.read('jax_enable_x64')),
    'no_forbidden_path_in_sys_path': not any(any(within(os.path.normcase(os.path.abspath(p)), f) for f in forbidden) for p in sys.path),
    'no_global_site_packages': not any('site-packages' in p and not within(os.path.normcase(os.path.abspath(p)), os.path.normcase(sys.prefix)) for p in sys.path),
    'no_source_file_access_attempt': not denied,
    'no_LF_MATLAB_import_attempt': not blocked,
    'no_LF_MATLAB_installed': not any(n.casefold() in {'dmftd', 'mma', 'auto', 'matlab', 'matlabengine'} for n in installed),
    'installed_hf_module': 'site-packages' in hf_eval.__file__,
    'installed_distribution_RECORD_hashes_match': not record_failures and record_files > 0,
}
try:
    profile_settings = tmc_benchmark.cshape_settings(time_limit_seconds=1200)
    profile_tolerance = profile_settings.tolerance
except (AttributeError, TypeError, ValueError):
    profile_tolerance = None
repair_checks = {
    'installed_distribution_version_0_2_1': importlib.metadata.version('independent-hf-evaluator') == '0.2.1',
    'installed_module_version_0_2_1': getattr(hf_eval, '__version__', None) == '0.2.1',
    'stable_kernel_version': getattr(tmc_kernel, 'KERNEL_VERSION', None) == 'p26_q1_direct_piola_huhu_v2',
    'benchmark_precision_profile_explicit_1e_9': getattr(tmc_benchmark, 'SOLVER_PROFILE', None) == 'hf2_precision_v2' and profile_tolerance == 1e-9,
    'generic_Newton_default_preserved_1e_8': NewtonSettings().tolerance == 1e-8,
    'small_reference_976_checks_16_cases': len(small['checks']) == 976 and small['completed_cases'] == 16,
    'strong_three_base_states_HP_expression_budget': strong['status'] == 'pass' and strong.get('HP_base_state_calls') == 3 and len(strong.get('rows', [])) == 6,
}
checks = {key: bool(value) for key, value in {**legacy_checks, **repair_checks}.items()}
summary = {
    'status': 'pass' if all(checks.values()) else 'fail',
    'scope': 'installed 0.2.1; original 17 detached checks, HF1/TMC A-B-A, 976 small checks, three same-input HP expression states; no full Cshape rerun',
    'checks': checks, 'legacy_check_count': len(legacy_checks), 'repair_check_count': len(repair_checks),
    'small_checks': len(small['checks']), 'small_cases': small['completed_cases'],
    'strong_precision': strong, 'solver_profile': getattr(tmc_benchmark, 'SOLVER_PROFILE', None),
    'benchmark_internal_tolerance': profile_tolerance, 'external_equilibrium_tolerance': 1e-8,
    'source_sha256': implementation_hash(), 'python': sys.executable, 'sys_path': sys.path,
    'installed_distributions': installed, 'hf_module': hf_eval.__file__, 'wall_seconds': perf_counter()-start,
    'linear_array_comparisons': linear_equal, 'installed_record_files_checked': record_files,
    'installed_record_failures': record_failures,
}
(output/'acceptance.json').write_text(json.dumps(summary, indent=2, allow_nan=False), encoding='utf-8')
(output/'access_audit.json').write_text(json.dumps({'opened_paths': sorted(opened), 'denied': denied,
    'blocked_imports': blocked, 'forbidden_paths_record_only': args.forbid,
    'method': 'Python-level audit, not OS sandbox'}, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2, allow_nan=False))
raise SystemExit(0 if summary['status'] == 'pass' else 2)
