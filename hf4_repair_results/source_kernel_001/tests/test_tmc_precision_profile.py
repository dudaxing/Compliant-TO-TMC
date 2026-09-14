"""The precision margin belongs to the benchmark and archived states stay explicit."""
import numpy as np

from hf_eval.tmc import NewtonSettings, rectangular_model, solve_path
from hf_eval.tmc_benchmark import cshape_settings, SOLVER_PROFILE
from hf_eval.tmc_kernel import KERNEL_VERSION


def test_precision_profile_preserves_generic_tolerance_and_budget():
    assert NewtonSettings().tolerance == 1e-8
    profile = cshape_settings(123)
    assert profile.tolerance == 1e-9
    assert profile.time_limit_seconds == 123
    assert profile.max_checks == 25 and profile.max_backtracks == 12
    assert SOLVER_PROFILE == 'hf2_precision_v2'
    assert KERNEL_VERSION == 'p26_q1_incremental_piola_huhu_v3'


def test_stored_internal_force_defines_the_recorded_residual_and_is_isolated():
    model = rectangular_model(2, 1, 2, 1, fixed_dofs=[0, 1, 6, 7])
    force = np.zeros(model.ndof)
    force[[5, 11]] = -.1
    def callback(record):
        record['internal_force'][:] = 999
    result = solve_path(model, force, [.01, .02], cshape_settings(30), on_accept=callback)
    assert result['status'] == 'success'
    assert result['linear_solve_diagnostics']
    for step in result['accepted_steps']:
        external = step['lambda']*force
        measured = np.linalg.norm((step['internal_force']-external)[model.free])/np.linalg.norm(external)
        assert measured == step['relative_residual']
        assert measured <= 1e-9
    assert max(r['normwise_backward_error'] for r in result['linear_solve_diagnostics']) < 1e-12
