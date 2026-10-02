"""Opt-in NumPy equilibrium against an independent homogeneous stretch root."""
import numpy as np
from scipy.optimize import brentq

from hf_eval import split_affine
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_numpy_tangent import assemble_split_numpy
from hf_eval.tmc import rectangular_model


def test_affine_controller_uses_opt_in_assembler_and_recovers_free_stretch(monkeypatch):
    model = rectangular_model(2, 1, 2., 1., E=7.8, nu=.3, alpha=0.,
                              fixed_dofs=(1, 3, 5, 7, 9, 11, 2))
    direction = np.zeros(model.ndof)
    direction[[7, 9, 11]] = -1.
    lift_shape = np.zeros(model.ndof)
    lift_shape[1::2] = -model.coordinates[:, 1]
    flags = []
    def selected(model, state, *, tangent):
        flags.append(tangent)
        return assemble_split_numpy(model, state, tangent=tangent)
    def forbidden(*args, **kwargs):
        raise AssertionError("Opt-in controller used its default compiled assembler")
    monkeypatch.setattr(split_affine, "assemble_split", forbidden)
    result = split_affine.solve_split_affine_path(
        model, np.zeros(model.ndof), direction, np.zeros(model.ndof), lift_shape,
        [0., .01], force_scale_per_length=7.8, settings=PrescribedSettings(time_limit_seconds=15.),
        assembler=selected)
    assert result["target_reached"] and result["failure"] is None
    assert True in flags and False in flags
    lam, mu, vertical = model.lam[0], model.mu[0], .99
    horizontal = brentq(lambda a: mu*(a*a-1) + lam*np.log(a*vertical), .9, 1.1, xtol=1e-14)
    state = result["accepted_steps"][-1]
    u = state["u_lift"] + state["u_fluctuation"]
    np.testing.assert_allclose(u[0::2], (horizontal-1)*(model.coordinates[:, 0]-1), atol=2e-12, rtol=2e-10)
    np.testing.assert_allclose(u[1::2], -.01*model.coordinates[:, 1], atol=2e-12)
    assert state["relative_residual"] <= 1e-9
