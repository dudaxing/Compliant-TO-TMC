"""Adversarial inventory checks and independent scalar-reference properties."""
from copy import deepcopy
from decimal import Decimal, localcontext
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_contact_reference_a0 import (
    D, TARGETS, analytic_uniform_force, nonuniform_metrics, safe_state_path,
    validate_inventory,
)


def inventory():
    entries = [dict(index=i, file=f"state_{i:03d}.npz", d=d, is_original_target=True,
                    original_target_displacement=d, bisection_depth=0)
               for i, d in enumerate(TARGETS)]
    result = dict(status="success", target_reached=True, reached_displacement=TARGETS[-1],
                  target_metrics=dict(d=TARGETS[-1]), accepted_steps=deepcopy(entries))
    return dict(steps=entries), result


def test_complete_original_target_inventory_is_required():
    index, result = inventory()
    assert validate_inventory(index, result)["status"] == "pass"
    index["steps"].pop()
    result["accepted_steps"].pop()
    with pytest.raises(ValueError, match="every frozen original target"):
        validate_inventory(index, result)


@pytest.mark.parametrize("field,value", [("d", .01), ("is_original_target", False),
                                          ("bisection_depth", 2), ("original_target_displacement", .125)])
def test_scalar_record_cannot_disagree_with_index(field, value):
    index, result = inventory()
    result["accepted_steps"][1][field] = value
    with pytest.raises(ValueError, match="index/result disagree"):
        validate_inventory(index, result)


def test_bisection_evidence_must_be_preserved_in_order():
    index, result = inventory()
    middle = dict(index=1, file="substep.npz", d=.015625, is_original_target=False,
                  original_target_displacement=.03125, bisection_depth=1)
    index["steps"].insert(1, middle)
    for i, entry in enumerate(index["steps"]):
        entry["index"] = i
    result["accepted_steps"] = deepcopy(index["steps"])
    assert validate_inventory(index, result)["accepted_count"] == 6
    index["steps"][1]["bisection_depth"] = 0
    result["accepted_steps"][1]["bisection_depth"] = 0
    with pytest.raises(ValueError, match="positive depth"):
        validate_inventory(index, result)


def test_duplicate_evidence_file_is_rejected():
    index, result = inventory()
    index["steps"][1]["file"] = index["steps"][0]["file"]
    with pytest.raises(ValueError, match="duplicate state filename"):
        validate_inventory(index, result)


def test_failed_solver_status_cannot_be_upgraded_by_complete_inventory():
    index, result = inventory()
    result.update(status="failed", target_reached=False, target_metrics=None)
    assert validate_inventory(index, result)["status"] == "not_pass"


@pytest.mark.parametrize("name", ["../state.npz", "..\\state.npz", "/state.npz", "state.json"])
def test_state_paths_are_confined_to_saved_steps(tmp_path, name):
    with pytest.raises(ValueError):
        safe_state_path(tmp_path, name)


def test_uniform_unloaded_reference_is_exactly_stress_free():
    answer = analytic_uniform_force(57.69230769230769, 38.46153846153846, 0.)
    assert answer["lambda_x"] == answer["lambda_y"] == 1
    assert answer["Pxx"] == answer["Pyy"] == answer["normal_force"] == 0
    assert answer["lam_exact_promoted"] == Decimal.from_float(57.69230769230769)


def test_uniform_scalar_reference_satisfies_zero_lateral_traction_and_compressive_work():
    lam, mu = 57.69230769230769, 38.46153846153846
    with localcontext() as context:
        context.prec = 80
        previous = Decimal(0)
        for d in TARGETS[1:]:
            answer = analytic_uniform_force(lam, mu, d)
            assert answer["lambda_x"] > 1 and answer["lambda_y"] < 1
            assert abs(answer["Pxx"])/D(100) < Decimal("1e-75")
            # Eliminate logJ with Pxx=0: Pyy=mu*(ly-lx^2/ly).
            independent_force = -D(mu)*(answer["lambda_y"]-answer["lambda_x"]**2/answer["lambda_y"])*2
            assert abs(answer["normal_force"]-independent_force) < Decimal("1e-74")
            assert answer["normal_force"] > previous
            previous = answer["normal_force"]


def test_nonuniform_metrics_measure_cross_gradients_and_hessian():
    g = [[[[Decimal(1), Decimal(2)], [Decimal(-3), Decimal(4)]],
          [[Decimal(2), Decimal(-1)], [Decimal(1), Decimal(6)]]]]
    hu = np.zeros((1, 2, 2, 2), dtype=object)
    hu[:] = Decimal(0)
    hu[0, 0, 0, 1] = Decimal("0.25")
    measured = nonuniform_metrics(dict(G_decimal=g, Hu_decimal=hu.tolist()))
    assert measured["Gxy_max_abs"] == 2
    assert measured["Gyx_max_abs"] == 3
    assert measured["Hu_max_abs"] == Decimal("0.25")
    assert measured["Gxx_range"] == 1 and measured["Gyy_range"] == 2
