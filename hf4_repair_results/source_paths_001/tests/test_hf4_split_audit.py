"""Keep the production stopping gate separate from the external HP gate."""
from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_hf4_split_normal import validate_production_acceptance, derived_status


def fixture(relative=5e-10):
    model = dict(base=np.zeros(4),fixed_dofs=np.array([0,1,2]),connectivity=np.array([[0,1,0,1]]))
    arrays = dict(internal_force=np.array([1.,0.,0.,relative]),J=np.ones((1,9)))
    spec = dict(solver=dict(displacement_scale_floor=1e-6,force_scale_floor_factor=1e-8,tolerance=1e-9))
    record = dict(d=.125,relative_residual=relative,free_force_residual_norm=relative,
                  internal_free_norm=relative,reaction_fixed_norm=1.,residual_scale=1.,
                  force_scale_floor=1e-8*.125,displacement_scale=.125)
    return arrays,record,model,spec


def test_independently_reconstruct_valid_original_production_stop():
    arrays,record,model,spec = fixture()
    assert validate_production_acceptance(arrays,record,model,spec,1.)["relative_residual"] == 5e-10


def test_external_hp_threshold_cannot_qualify_a_failed_production_state():
    arrays,record,model,spec = fixture(1.84e-9)
    assert record["relative_residual"] < 1e-8
    with pytest.raises(ValueError,match="production stopping tolerance"):
        validate_production_acceptance(arrays,record,model,spec,1.)


@pytest.mark.parametrize("value", [float("nan"),float("inf"),0.,-1.])
def test_invalid_saved_j_is_rejected(value):
    arrays,record,model,spec = fixture()
    arrays["J"][0,0] = value
    with pytest.raises(ValueError,match="force/J"):
        validate_production_acceptance(arrays,record,model,spec,1.)


@pytest.mark.parametrize("field", ["relative_residual","residual_scale","internal_free_norm","reaction_fixed_norm"])
def test_edited_record_metric_cannot_override_actual_force(field):
    arrays,record,model,spec = fixture()
    record[field] = 0
    with pytest.raises(ValueError,match="archived production metric"):
        validate_production_acceptance(arrays,record,model,spec,1.)


def test_wrong_precision_array_is_rejected():
    arrays,record,model,spec = fixture()
    arrays["J"] = arrays["J"].astype(np.float32)
    with pytest.raises(ValueError,match="force/J"):
        validate_production_acceptance(arrays,record,model,spec,1.)


def test_model_and_numerical_cached_statuses_are_derived_separately():
    checks = [dict(kind="numerical",status="pass")]
    assert derived_status(checks) == ("pass","measurement_only","pass")
    checks.append(dict(kind="model",status="not_pass"))
    assert derived_status(checks) == ("pass","not_pass","not_pass")
    checks[0]["status"]="not_pass"
    checks[1]["status"]="pass"
    assert derived_status(checks) == ("not_pass","pass","not_pass")
