"""Explicit omitted-energy contract; small fixtures, no F16 qualification."""
import inspect

import numpy as np
import pytest

from hf_eval import split_kernel_invariants_hu as kernel
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import rectangular_model
from hf_eval.tmc_kernel import KernelError, operators


XY = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])


@pytest.fixture(autouse=True)
def forbid_compilation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Mechanical NumPy entry invoked compiled work")
    for name in ("_runtime", "_batch_with_tangent", "_batch_without_tangent"):
        monkeypatch.setattr(kernel, name, forbidden)


@pytest.mark.parametrize("amplitude", [2.0**-10, 1./8], ids=["near", "direct"])
def test_complete_and_mechanical_fields_match_bytewise(amplitude):
    lift, w = np.zeros((1, 8)), (amplitude*XY).reshape(1, 8)
    args = (lift, w, operators(1., 1.), 2., 3., 1./8)
    complete = kernel.batch_response_split_numpy(*args)
    mechanical = kernel.batch_response_split_mechanical_numpy(*args)
    assert set(mechanical) == set(complete)-{"material_energy"}
    for name, actual in mechanical.items():
        reference = complete[name]
        assert actual.dtype == reference.dtype == np.float64
        assert actual.shape == reference.shape
        assert actual.tobytes(order="C") == reference.tobytes(order="C"), name


def test_mechanical_skips_auxiliary_square_while_complete_executes_it(monkeypatch):
    original, calls = kernel._scaled_mul, []
    def reject_auxiliary_square(*args, **kwargs):
        caller = inspect.currentframe().f_back
        if caller.f_back.f_code.co_name == "scaled_square":
            calls.append("auxiliary square")
            raise KernelError("Synthetic auxiliary energy range trap", code="unsupported_arithmetic_range")
        return original(*args, **kwargs)
    monkeypatch.setattr(kernel, "_scaled_mul", reject_auxiliary_square)
    args = (np.zeros((1, 8)), (2.0**-10*XY).reshape(1, 8), operators(1., 1.), 2., 3., 1./8)
    mechanical = kernel.batch_response_split_mechanical_numpy(*args)
    assert not calls and "material_energy" not in mechanical
    with pytest.raises(KernelError, match="Synthetic auxiliary energy range trap") as caught:
        kernel.batch_response_split_numpy(*args)
    assert caught.value.code == "unsupported_arithmetic_range" and calls == ["auxiliary square"]


def test_default_complete_entry_still_rejects_nonfinite_energy(monkeypatch):
    original = kernel._response
    def inject_unavailable_energy(*args, **kwargs):
        residual, fields = original(*args, **kwargs)
        if "material_energy" in fields:
            fields = dict(fields, material_energy=np.full_like(fields["material_energy"], np.nan))
        return residual, fields
    monkeypatch.setattr(kernel, "_response", inject_unavailable_energy)
    args = (np.zeros((1, 8)), (2.0**-10*XY).reshape(1, 8), operators(1., 1.), 2., 3., 1./8)
    with pytest.raises(KernelError) as caught:
        kernel.batch_response_split_numpy(*args)
    assert caught.value.code == "nonfinite" and caught.value.details == {"field": "material_energy"}
    mechanical = kernel.batch_response_split_mechanical_numpy(*args)
    assert "material_energy" not in mechanical
    assert np.all(mechanical["arithmetic_supported"] == 1.)


@pytest.mark.parametrize("w,code", [(np.zeros((1, 7)), "invalid_shape"),
    (np.column_stack((-2*XY[:, 0], np.zeros(4))).reshape(1, 8), "invalid_J")])
def test_mechanical_keeps_shape_and_physical_J_gates(w, code):
    with pytest.raises(KernelError) as caught:
        kernel.batch_response_split_mechanical_numpy(np.zeros_like(w), w, operators(1., 1.), 2., 3., 0.)
    assert caught.value.code == code


def test_mechanical_assembler_preserves_total_scatter_and_state():
    model = rectangular_model(2, 1, 2., 1., E=7.8, nu=.3, alpha=0.)
    w = np.column_stack((model.coordinates[:, 1]/16., np.zeros(len(model.coordinates)))).ravel()
    state = SplitDisplacement(np.zeros_like(w), w)
    original_bytes = (state.lift.tobytes(), state.fluctuation.tobytes())
    _, reference, complete = kernel.assemble_split_numpy(model, state)
    matrix, actual, mechanical = kernel.assemble_split_mechanical_numpy(model, state)
    assert matrix is None and "material_energy" not in mechanical and "tangent" not in mechanical
    assert actual.dtype == reference.dtype and actual.shape == reference.shape
    assert actual.tobytes(order="C") == reference.tobytes(order="C")
    for name in ("residual", "material_residual", "regularization_residual", "J"):
        assert mechanical[name].tobytes(order="C") == complete[name].tobytes(order="C")
    assert set(mechanical["timing_seconds"]) == {"kernel_and_transfer", "assembly"}
    assert (state.lift.tobytes(), state.fluctuation.tobytes()) == original_bytes
