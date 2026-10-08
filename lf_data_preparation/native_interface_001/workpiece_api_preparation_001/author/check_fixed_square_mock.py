"""Candidate only: real batch/API transport with three mocked science delegates."""
from time import perf_counter
STARTED = perf_counter()
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import argparse
import json
import sys

FIXTURE = "lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_right4col_response.json"
INVENTORY = "lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/run_001/input_inventory.json"
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True, help="Product manifest; relative paths use --repo")
    parser.add_argument("--output", type=Path, required=True, help="New external mock-check directory")
    args = parser.parse_args()
    root, output = args.repo.resolve(), args.output.resolve()
    assert not output.is_relative_to(root) and not output.exists()
    manifest_file = (args.manifest if args.manifest.is_absolute() else root / args.manifest).resolve()
    manifest, fixture, inventory = read(manifest_file), read(root / FIXTURE), read(root / INVENTORY)
    original_task = read(root / manifest["cases"][0]["task"])
    assert len(manifest["cases"]) == 1 and manifest["options"]["settings"] == inventory["settings"]
    assert set(manifest["options"]) == {"settings", "response_mode", "tangent_mode", "initial_guess"}
    assert manifest["options"]["settings"]["minimum_increment"] == .00625
    assert manifest["options"]["settings"]["time_limit_seconds"] == 4500.
    assert fixture["path"]["accepted_states"] == len(original_task["path"]["targets_mm"]) == 24
    fixture_descriptor = root / fixture["identity"]["result"]["path"]
    token, observed = object(), {}
    test_manifest = deepcopy(manifest)
    test_manifest["cases"][0]["output"] = str(output / "fixed_square")
    assert test_manifest["options"] == manifest["options"]
    assert all(test_manifest["cases"][0][key] == manifest["cases"][0][key] for key in ("label", "geometry", "task"))

    def mock_solve(geometry, task, targets, **options):
        assert geometry == (root / manifest["cases"][0]["geometry"]).resolve() and task == original_task
        assert list(targets) == original_task["path"]["targets_mm"]
        assert asdict(options["settings"]) == inventory["settings"]
        assert {key: options[key] for key in ("response_mode", "tangent_mode", "initial_guess")} == {
            key: manifest["options"][key] for key in ("response_mode", "tangent_mode", "initial_guess")}
        observed.update(targets=list(targets), settings=asdict(options["settings"]),
                        modes={key: options[key] for key in ("response_mode", "tangent_mode", "initial_guess")})
        return token

    def mock_save(value, directory):
        assert value is token and directory == output / "fixed_square"
        return fixture_descriptor  # An explicit old fixture pointer; no new result/NPZ is created.

    def mock_summary(descriptor, *, repo_root):
        assert descriptor == fixture_descriptor and repo_root == root
        response = deepcopy(fixture)
        response.update(mock_response=True, fixture_only=True,
            mock_fixture=dict(path=FIXTURE, sha256=sha(root / FIXTURE), new_scientific_result=False),
            qualification_scope="MOCK batch/API transport only; copied old saved values are fixtures, no new solve, audit or view qualification")
        response["producer_flags"] = {key: False for key in fixture["producer_flags"]}
        response["independent_reference"] = dict(status="not_provided", accepted_reference_pass=False,
            full_path_reference_pass=False, source_bindings_verified=False, report=None,
            HP_all_columns_qualified=False, contact_qualified=False, clamp_qualified=False,
            pressure_qualified=False, HF5_qualified=False, reasons=["Mock fixture; no new independent reference"])
        response["views"] = dict(status="not_provided", manifest=None, links=[], reasons=["Mock fixture; no new view"])
        response["call_counts"] = dict(force_calls=0, force_calls_completed=0, tangent_calls=0,
            tangent_calls_completed=0, solver_invocations=0, JIT_calls=0, HP_calls=0)
        response["timing_seconds"] = dict(mock_fixture_only=0.)
        return response

    # These runtime imports are part of a future approved mock check, not this authoring step.
    sys.path.insert(0, str(root / "hf_repo/src"))
    from hf_eval import native_batch, native_evaluate
    output.mkdir(parents=True)
    test_file = output / "test_manifest.json"
    write(test_file, test_manifest)
    with patch.object(native_evaluate, "solve_native_mean", side_effect=mock_solve) as solve, \
         patch.object(native_evaluate, "write_native_mean", side_effect=mock_save) as save, \
         patch.object(native_evaluate, "summarize_saved_native_result", side_effect=mock_summary) as summarize, \
         patch.object(native_batch, "evaluate_native", wraps=native_evaluate.evaluate_native) as api:
        index = native_batch.evaluate_native_batch(test_file, output / "batch", repo_root=root)
        assert api.call_count == solve.call_count == save.call_count == summarize.call_count == 1
    response = read(output / "fixed_square/response.json")
    saved_index = read(output / "batch/index.json")
    assert index == saved_index and index["status"] == "success" and len(index["cases"]) == 1
    entry = index["cases"][0]
    assert response["mock_response"] is response["fixture_only"] is True
    assert response["invocation"]["settings"] == observed["settings"] == inventory["settings"]
    assert response["invocation"]["targets_mm"] == observed["targets"] == original_task["path"]["targets_mm"]
    for key in ("target_response", "requested_endpoint_response", "maximum_loading_stroke", "last_accepted"):
        assert response[key] == entry[key] == fixture[key]
        assert response[key]["workpiece"] == fixture[key]["workpiece"]
    assert response["target_response"]["d_mm"] == response["maximum_loading_stroke"]["d_mm"] == 1.2
    assert response["requested_endpoint_response"]["d_mm"] == response["last_accepted"]["d_mm"] == 0.
    assert all(value is False for value in response["producer_flags"].values())
    assert response["independent_reference"]["accepted_reference_pass"] is response["independent_reference"]["full_path_reference_pass"] is False
    assert response["views"]["status"] == "not_provided" and not response["views"]["links"]
    write(output / "mock_check_receipt.json", dict(status="pass_mock_transport_only", mock_response=True,
        real_batch_calls=1, real_API_calls=1, mocked_solve_calls=1, mocked_save_calls=1, mocked_summary_calls=1,
        scientific_solver_calls=0, F=0, T=0, HP=0, NPZ_loads=0, new_qualification=False,
        actual_accepted_states=0, fixture_accepted_states=fixture["path"]["accepted_states"],
        through_helper_elapsed_seconds=perf_counter() - STARTED,
        elapsed_scope="Imports, mock batch/API execution, saved-response/index checks; excludes final receipt write/stdout",
        source_manifest_sha256=sha(manifest_file), fixture_response_sha256=sha(root / FIXTURE),
        observed=observed, warning="Old fixture numbers and body fields validate transport shape only; not a new physical run"))
    print(json.dumps(dict(status="pass_mock_transport_only", new_qualification=False), ensure_ascii=False))


if __name__ == "__main__":
    main()
