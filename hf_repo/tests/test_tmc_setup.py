"""Read-only source-setup guards; these tests never run a nonlinear path."""

import numpy as np
import pytest

from hf_eval import tmc_benchmark as benchmark
from hf_eval.tmc import TMCError


def _source_arrays():
    model, force, targets, loaded, _ = benchmark.cshape_preset()
    return {
        "coordinates": model.coordinates.copy(),
        "connectivity": model.connectivity.copy(),
        "fixed_dofs": model.fixed_dofs.copy(),
        "loaded_nodes": loaded.copy(),
        "gamma": np.where(model.solid, 1., 1e-6),
        "F0": force.copy(), "targets": targets.copy(),
    }


def _write(tmp_path, arrays):
    path = tmp_path / "source_setup.npz"
    np.savez_compressed(path, **arrays)
    return path


def test_source_target_float_values_are_preserved_not_regenerated(tmp_path):
    arrays = _source_arrays()
    # A source arithmetic difference within the frozen matching allowance.
    arrays["targets"][37] = np.nextafter(arrays["targets"][37], np.inf)
    arrays["fixed_dofs"] = arrays["fixed_dofs"][::-1]
    result = benchmark.validate_source_setup(_write(tmp_path, arrays))
    np.testing.assert_array_equal(result, arrays["targets"])
    assert result.dtype == np.dtype("float64")
    assert result.shape == (100,)


@pytest.mark.parametrize("field", ["coordinates", "connectivity", "fixed_dofs", "loaded_nodes", "gamma", "F0", "targets"])
def test_physical_setup_mutations_are_rejected(tmp_path, field):
    arrays = _source_arrays()
    if field == "coordinates": arrays[field][1, 0] += 1e-5
    elif field == "connectivity": arrays[field][0, [0, 1]] = arrays[field][0, [1, 0]]
    elif field == "fixed_dofs": arrays[field] = arrays[field][:-1]
    elif field == "loaded_nodes": arrays[field][-1] -= 1
    elif field == "gamma": arrays[field][0] = 1e-6
    elif field == "F0": arrays[field][arrays["loaded_nodes"][0]*2+1] *= 10
    else: arrays[field][0] = .001
    with pytest.raises(TMCError, match="differs|differ"):
        benchmark.validate_source_setup(_write(tmp_path, arrays))


@pytest.mark.parametrize("field", ["coordinates", "F0", "targets"])
def test_nonfinite_reference_values_are_rejected(tmp_path, field):
    arrays = _source_arrays()
    arrays[field].flat[0] = np.nan
    with pytest.raises(TMCError):
        benchmark.validate_source_setup(_write(tmp_path, arrays))


@pytest.mark.parametrize("field", ["coordinates", "F0", "targets"])
def test_small_complex_reference_values_are_not_treated_as_real(tmp_path, field):
    arrays = _source_arrays()
    arrays[field] = arrays[field].astype(complex)
    arrays[field].flat[0] += 1e-16j
    with pytest.raises(TMCError):
        benchmark.validate_source_setup(_write(tmp_path, arrays))


def test_reference_target_column_shape_is_not_silently_flattened(tmp_path):
    arrays = _source_arrays()
    arrays["targets"] = arrays["targets"][:, None]
    with pytest.raises(TMCError):
        benchmark.validate_source_setup(_write(tmp_path, arrays))


def test_object_reference_field_cannot_trigger_pickle_loading(tmp_path):
    arrays = _source_arrays()
    arrays["targets"] = arrays["targets"].astype(object)
    with pytest.raises(ValueError):
        benchmark.validate_source_setup(_write(tmp_path, arrays))


@pytest.mark.parametrize("kind", ["complex", "nonfinite", "shape", "wrong_levels"])
def test_run_guard_rejects_bad_targets_before_any_solver_call(tmp_path, monkeypatch, kind):
    targets = _source_arrays()["targets"]
    if kind == "complex": targets = targets.astype(complex) + 1e-16j
    elif kind == "nonfinite": targets[1] = np.inf
    elif kind == "shape": targets = targets[:, None]
    else: targets[0] = .001
    def forbidden_solver(*args, **kwargs):
        raise AssertionError("Nonlinear solver must not run in setup-guard tests")
    monkeypatch.setattr(benchmark, "solve_path", forbidden_solver)
    with pytest.raises(TMCError):
        benchmark.run_cshape(tmp_path / "unused_run", source_targets=targets)
