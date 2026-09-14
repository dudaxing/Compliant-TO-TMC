"""Pure-array MATLAB parity fixtures; no MATLAB installation is required."""
import importlib.util
import json
from pathlib import Path
import shutil

import jax
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "validation/hf2/validation_spec.json"
FIXTURES = ROOT / "tests/fixtures/hf2"
module_spec = importlib.util.spec_from_file_location("hf2_independent_validation", ROOT / "scripts/validate_hf2.py")
validation = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(validation)
comparison_spec = importlib.util.spec_from_file_location("hf2_cshape_comparison", ROOT / "scripts/compare_cshape.py")
comparison = importlib.util.module_from_spec(comparison_spec)
comparison_spec.loader.exec_module(comparison)


@pytest.fixture(scope="module")
def references():
    return validation.load_fixtures(FIXTURES, SPEC)


CASES = validation.case_definitions(json.loads(SPEC.read_text(encoding="utf-8")))


@pytest.mark.parametrize("case", CASES, ids=[case["case_id"] for case in CASES])
def test_frozen_matlab_case(case, references):
    spec, _, data = references
    checks = validation.Checks()
    assert jax.default_backend() == "cpu"
    with jax.enable_x64(True):
        _, _, timing = validation.validate_case(case, data[case["case_id"]], spec, checks,
                                                finite_differences=False)
    failed = [row for row in checks.rows if row["status"] != "pass"]
    assert not failed, json.dumps(failed, indent=2)
    assert timing["wall_seconds"] > 0


def test_corrupted_reference_is_rejected_before_kernel(tmp_path):
    shutil.copytree(FIXTURES, tmp_path / "fixtures")
    path = next((tmp_path / "fixtures").glob("*.npz"))
    data = bytearray(path.read_bytes())
    data[len(data)//2] ^= 0x01
    path.write_bytes(data)
    with pytest.raises(ValueError, match="hash mismatch"):
        validation.load_fixtures(tmp_path / "fixtures", SPEC)


def test_incomplete_reference_set_is_rejected(tmp_path):
    folder = tmp_path / "fixtures"
    folder.mkdir()
    index = json.loads((FIXTURES / "small_reference_index.json").read_text(encoding="utf-8"))
    index["cases"].pop()
    (folder / "small_reference_index.json").write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(ValueError, match="all and only the 16"):
        validation.load_fixtures(folder, SPEC)


def test_changed_validation_spec_is_rejected(tmp_path):
    altered = tmp_path / "spec.json"
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    spec["matlab_residual_tangent_tolerance"] = 1.
    altered.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(ValueError, match="spec hash"):
        validation.load_fixtures(FIXTURES, altered)


@pytest.mark.parametrize("case", CASES, ids=[case["case_id"] for case in CASES])
def test_independent_piola_postprocessor_at_frozen_small_states(case, references):
    spec, _, data = references
    _, reference = data[case["case_id"]]
    local_spec = {"material": spec["material"], "cshape": {
        "cells": [case["nx"], case["ny"]], "domain": [case["Lx"], case["Ly"]],
        "thickness_factor": case["thickness"]}}
    model = {"connectivity": reference["connectivity"].astype(int), "gamma": reference["gamma"].ravel()}
    state = comparison.independent_state(reference["u_canonical"].ravel(), model, local_spec)
    checks = validation.Checks()
    checks.compare(case["case_id"], "direct_Piola_global_residual", state["internal"],
                   reference["residual_canonical"].ravel(), spec["matlab_residual_tangent_tolerance"],
                   case["E"]*validation.norm(case["gamma"])*(case["hx"]*case["hy"])**.5)
    checks.compare(case["case_id"], "direct_Piola_J", state["J"], reference["J"],
                   spec["matlab_operator_J_tolerance"])
    checks.compare(case["case_id"], "direct_Piola_energy", state["energy"],
                   reference["material_energy"].ravel(), spec["matlab_residual_tangent_tolerance"],
                   case["E"]*validation.norm(case["gamma"])*case["hx"]*case["hy"])
    assert all(row["status"] == "pass" for row in checks.rows), checks.rows
