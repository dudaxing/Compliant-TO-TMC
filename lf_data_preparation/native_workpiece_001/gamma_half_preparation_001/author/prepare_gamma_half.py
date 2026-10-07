"""Construct one gamma-only side18 model; no force, tangent, solve or HP call."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from time import perf_counter
import argparse
import json
import sys

BASELINE = "16ee4ebb67161e2c8bc9a27d8e44285308778171"
OLD = "lf_data_preparation/native_workpiece_001/enlarged_square_projection_001"
CONTROL = "lf_data_preparation/native_workpiece_001/gamma_half_preparation_001"
RSS_LIMIT = 8 * 1024**3
CHANGED = {"lam", "mu", "gamma"}
INPUTS = ["run_001/task.json", "run_001/result/model/model.json",
    "run_001/result/model/model.npz", "run_001/result/model/source_geometry/geometry.json",
    "run_001/result/model/source_geometry/geometry.npz", "run_001/source_freeze.json",
    "run_001/input_inventory.json", "run_001/execution_receipt.json", "run_001/result/result.json",
    "production_protocol.json", "production_launch.json", "reference_protocol.json",
    "reference_launch.json", "reference/summary.json"]
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def qualified_baseline(root):
    """Check this side18 predecessor only; its qualification is not transferred."""
    old = root / OLD
    task, model = (read(old / p) for p in INPUTS[:2])
    receipt = read(old / "run_001/execution_receipt.json")
    result = read(old / "run_001/result/result.json")
    reference = read(old / "reference/summary.json")
    assert task == model["task"] and task["third_medium"] == {"gamma": 1e-6}
    assert task["workpiece"] == dict(kind="fixed_rigid", shape="square", center_mm=[71., 40.],
        side_mm=18., fixed_components=[0, 1])
    assert receipt["status"] == "pass" and receipt["path_completed"]
    assert result["status"] == "success" and reference["status"] == "pass"
    assert reference["result_sha256"] == digest(old / "run_001/result/result.json")
    assert receipt["accepted_states"] == result["accepted_states"] == reference["accepted_states"] == 24
    assert reference["HP_calls_started"] == reference["HP_calls_completed"] == 48
    for phase in ("production", "reference"):
        launch = read(old / (phase + "_launch.json"))
        assert launch["status"] == "pass" and launch["exit_code"] == 0
        assert launch["invocations"] == 1 and launch["stop_reason"] is None
        assert launch["all_bindings_unchanged"]
        assert launch["protocol_sha256"] == digest(old / (phase + "_protocol.json"))
    assert model["arrays"]["sha256"] == digest(old / "run_001/result/model/model.npz")
    return task, model


def main():
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    protocol_file = args.protocol.resolve()
    protocol = read(protocol_file)
    control, output = root / CONTROL, root / CONTROL / "run_001"
    assert protocol_file == control / "preparation_protocol.json" and not output.exists()
    assert protocol["baseline_commit"] == BASELINE
    assert protocol["phases"]["prepare"]["helper_seconds"] == 120
    assert protocol["sampled_RSS_bytes"] == RSS_LIMIT
    assert all(digest(root / p) == pin for p, pin in protocol["bindings"].items())
    old_task, old_model = qualified_baseline(root)
    import psutil
    process = psutil.Process()
    peak = 0

    def checkpoint():
        nonlocal peak
        peak = max(peak, process.memory_info().rss)
        assert not (control / "stop_requested.txt").exists(), "Supervisor requested stop"
        assert perf_counter() - started <= 120 and peak <= RSS_LIMIT, "Preparation resource limit"

    checkpoint()
    task = deepcopy(old_task)
    task["third_medium"]["gamma"] = 5e-7
    task["task_id"] = "EXPLORATORY_fixed_workpiece_gripper_square_x71_side18_E1_gamma5em7_1p2mm"
    task["purpose"] = "gamma_half_single_factor_contact_force_exploration"
    task["parameter_origin"] = "Gamma-only preparation: 1e-6 to 5e-7; all other physical task values retained."
    assert {k for k in task if task[k] != old_task[k]} == {
        "third_medium", "task_id", "purpose", "parameter_origin"}
    output.mkdir()
    receipt = dict(status="running", invocations=1, model_constructions=0, model_constructions_completed=0,
        model_writes=0, force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        JIT_calls=0, LF_imports=0, qualification="Construction only; no new equilibrium or contact qualification.")
    try:
        write(output / "task.json", task)
        sys.path.insert(0, str(root / "hf_repo/src"))
        import numpy as np
        from hf_eval.native_project import build_native_project, write_native_project
        checkpoint()
        geometry = root / OLD / "run_001/result/model/source_geometry/geometry.json"
        receipt["model_constructions"] = 1
        project = build_native_project(geometry, task)
        receipt["model_constructions_completed"] = 1
        checkpoint()
        receipt["model_writes"] = 1
        model_file = write_native_project(project, output / "model")
        checkpoint()
        with np.load(model_file.with_suffix(".npz"), allow_pickle=False) as new, np.load(
                root / OLD / "run_001/result/model/model.npz", allow_pickle=False) as old:
            assert set(new.files) == set(old.files) and len(new.files) == 27
            unchanged = sorted(set(old.files) - CHANGED)
            assert len(unchanged) == 24 and all(new[k].dtype == old[k].dtype
                and new[k].shape == old[k].shape and new[k].tobytes() == old[k].tobytes() for k in unchanged)
            solid = old["solid"].astype(bool)
            for key in sorted(CHANGED):
                assert new[key].dtype == old[key].dtype and new[key].shape == old[key].shape
                assert new[key][solid].tobytes() == old[key][solid].tobytes()
                assert np.array_equal(new[key][~solid], old[key][~solid] * .5)
        metadata = read(model_file)
        assert metadata["region_metadata"]["workpiece"] == old_model["region_metadata"]["workpiece"]
        for filename in ("geometry.json", "geometry.npz"):
            assert digest(model_file.parent / "source_geometry" / filename) == digest(geometry.parent / filename)
        freeze = dict(schema_version="gamma-half-preparation-source-freeze-1.0", baseline_commit=BASELINE,
            sources=protocol["sources"], inputs=protocol["input_bindings"], helpers=protocol["helper_bindings"],
            protocol_sha256=digest(protocol_file), capsule_policy="Existing bound core and baseline files retained in place; no duplicate historical capsules.")
        write(output / "source_freeze.json", freeze)
        comparison = dict(total_fields=27, unchanged_fields=unchanged, changed_fields=sorted(CHANGED),
            medium_factor=.5, solid_values_byte_exact=True, comparison_model_file=OLD + "/run_001/result/model/model.npz")
        write(output / "input_inventory.json", dict(schema_version="gamma-half-preparation-inputs-1.0",
            baseline_commit=BASELINE, geometry_file=geometry.relative_to(root).as_posix(),
            task_file=(output / "task.json").relative_to(root).as_posix(),
            model_file=model_file.relative_to(root).as_posix(), model_sha256=digest(model_file.with_suffix(".npz")),
            source_freeze_sha256=digest(output / "source_freeze.json"), model_comparison=comparison,
            task_sha256=project.task_hash, initial_guess="port_projection",
            targets_mm=task["path"]["targets_mm"], qualification=receipt["qualification"]))
        checkpoint()
        assert all(digest(root / p) == pin for p, pin in protocol["bindings"].items())
        receipt.update(status="pass", model_comparison=comparison, model_sha256=digest(model_file.with_suffix(".npz")),
            task_sha256=project.task_hash, actual_counts=metadata["region_metadata"]["counts"], inputs_and_sources_unchanged=True)
    except Exception as error:
        receipt.update(status="failed", error=dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        receipt.update(elapsed_seconds=perf_counter() - started, peak_sampled_helper_RSS_bytes=peak,
            helper_seconds=120, sampled_RSS_limit_bytes=RSS_LIMIT)
        write(output / "preparation_receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
