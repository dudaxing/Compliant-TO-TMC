"""Regress the observed tiny-strain rejection against independent Decimal math."""
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
import pytest

from hf_eval import compensated_invariants as ci
from hf_eval import split_kernel_invariants_hu as kernel
from hf_eval.tmc import TMCModel


@pytest.mark.parametrize("high,low", [
    (float.fromhex("0x1.b3bbbbbbbbbbcp-115"), float.fromhex("-0x1.2222222222222p-174")),
    (2.**-8, 2.**-70), (-2.**-8, 2.**-70), (0., 0.), (-1., 2.**-56), (-1., 2.**-400),
])
def test_log1p_low_correction_and_retained_minus_one(high, low):
    actual = ci.dd_log1p((np.asarray(high), np.asarray(low)), np)
    assert bool(ci.pair_supported(actual))
    with localcontext() as context:
        context.prec = 180
        value = Decimal.from_float(high) + Decimal.from_float(low)
        expected = (1 + value).ln()
        observed = Decimal.from_float(float(actual[0])) + Decimal.from_float(float(actual[1]))
        assert abs(observed - expected) <= Decimal("3e-16") * abs(expected)


def test_log1p_rejects_original_domain_errors():
    for pair in ((-1., 0.), (-2., 0.), (ci.OPERAND_MIN / 2, 0.), (1., ci.OPERAND_MIN / 2)):
        actual = ci.dd_log1p(tuple(np.asarray(v) for v in pair), np)
        assert not bool(ci.pair_supported(actual))
        assert np.isnan(actual[0])


def test_stored_tiny_strain_keeps_nonzero_independent_energy(monkeypatch):
    path = Path(__file__).resolve().parents[2] / "hf4_c2_stable_f_validation/numpy_scope_001/inputs/manufactured/nondyadic_rect__tiny_strain.npz"
    with np.load(path, allow_pickle=False) as archive:
        fixture = {key: archive[key].copy() for key in archive.files}
    model = TMCModel(fixture["coordinates"], fixture["connectivity"], fixture["lam"], fixture["mu"],
                     float(fixture["kr"]), float(fixture["hx"]), float(fixture["hy"]),
                     float(fixture["thickness"]), fixture["solid"], fixture["fixed_dofs"])
    def forbidden(*args, **kwargs):
        raise AssertionError("NumPy regression must not execute JIT")
    monkeypatch.setattr(kernel, "_runtime", forbidden)
    monkeypatch.setattr(kernel, "_batch_with_tangent", forbidden)
    monkeypatch.setattr(kernel, "_batch_without_tangent", forbidden)
    lift, fluctuation = (fixture[k][model.edofs] for k in ("u_lift", "u_fluctuation"))
    actual = kernel.batch_response_split_numpy(lift, fluctuation, model.ops, model.lam, model.mu, model.kr)
    assert all(np.isfinite(value).all() for value in actual.values())
    assert np.all(actual["arithmetic_supported"] == 1.)
    assert np.all(actual["material_energy"] > 0.)
    # Reconstruct the real shadow independently from stored binary64 operands.
    # No DD operation or production energy expression evaluates this oracle.
    d = lambda x: Decimal.from_float(float(x))
    with localcontext() as context:
        context.prec = 180
        expected = []
        for e in range(model.ne):
            u = [[d(lift[e, 2*a+i]) + d(fluctuation[e, 2*a+i]) for i in range(2)] for a in range(4)]
            energy = Decimal(0)
            for q in range(9):
                F = [[Decimal(i == j) + sum(u[a][i] * d(model.ops["grad"][q, a, j]) for a in range(4))
                      for j in range(2)] for i in range(2)]
                J = F[0][0]*F[1][1] - F[0][1]*F[1][0]
                log_J = J.ln()
                density = (d(model.lam[e])*log_J**2 + d(model.mu[e]) *
                           (sum(value**2 for row in F for value in row) - 2 - 2*log_J)) / 2
                energy += d(model.ops["weights"][q]) * density
            expected.append(float(energy))
    np.testing.assert_allclose(actual["material_energy"], expected, rtol=2e-14, atol=0.)
