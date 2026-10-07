"""Construct the three declared fixed-workpiece models, without any response."""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "hf_repo" / "src"))
from hf_eval import tmc, tmc_kernel
from hf_eval.native_project import build_native_project, write_native_project


SOURCES = (
    "hf_repo/src/hf_eval/native_project.py", "hf_repo/src/hf_eval/native_map.py",
    "hf_repo/src/hf_eval/data.py", "hf_repo/src/hf_eval/regions.py",
    "hf_repo/src/hf_eval/project.py", "hf_repo/src/hf_eval/tmc.py",
    "hf_repo/src/hf_eval/tmc_kernel.py", "hf_repo/src/hf_eval/__init__.py",
    "hf_repo/scripts/prepare_native_workpieces.py",
)
FACTS = {
    "gripper_coarse_square": (128, 153, 376, 17),
    "gripper_fine_square": (512, 561, 1258, 33),
    "gripper_fine_circle": (406, 455, 1046, 33),
}
BODY_FIELDS = {
    "workpiece_cells", "workpiece_nodes", "workpiece_dofs",
    "workpiece_background_symmetry_overlap_dofs",
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, record):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def inspect_model(descriptor, prior, case):
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    original = json.loads(prior.with_suffix(".json").read_text(encoding="utf-8"))
    task = json.loads((ROOT/case["task_file"]).read_text(encoding="utf-8"))
    body = saved["region_metadata"]["workpiece"]
    expected_cells, expected_nodes, expected_fixed, expected_overlap = FACTS[case["alias"]]
    check(saved["schema_version"] == "hf-native-project-model-1.1" and not saved["response_evaluated"],
          "Construction model schema/response declaration differs")
    check(saved["task"] == task and saved["source_geometry"] == original["source_geometry"]
          and saved["grid"] == original["grid"] and saved["model_extent"] == original["model_extent"],
          "Saved task or original geometry identity differs")
    check(saved["material"] == original["material"] and saved["qualification"] == original["qualification"],
          "Original material or geometry qualification changed")
    for name in ("support", "entity_symmetry", "background_symmetry", "ports"):
        check(saved["region_metadata"][name] == original["region_metadata"][name], "Original region changed: "+name)
    fields = {}
    with np.load(prior, allow_pickle=False) as old, np.load(descriptor.parent / "model.npz", allow_pickle=False) as new:
        check(len(old.files) == 23 and set(new.files) == set(old.files) | BODY_FIELDS and len(new.files) == 27,
              "Expected original 23 and workpiece 27 model arrays")
        unchanged = sorted(set(old.files) - {"fixed_dofs", "free_dofs"})
        for name in unchanged:
            a, b = old[name], new[name]
            check(a.dtype == b.dtype and a.shape == b.shape and a.tobytes(order="C") == b.tobytes(order="C"),
                  "Original non-boundary array changed: "+name)
        for name in BODY_FIELDS:
            array = new[name]
            check(array.dtype == np.dtype("int64") and np.array_equal(array, body[name.removeprefix("workpiece_")]),
                  "Saved workpiece indices differ: "+name)
        nodes, cells, dofs = new["workpiece_nodes"], new["workpiece_cells"], new["workpiece_dofs"]
        overlap = new["workpiece_background_symmetry_overlap_dofs"]
        fixed, free = new["fixed_dofs"], new["free_dofs"]
        check((len(cells), len(nodes), len(fixed), len(overlap)) == FACTS[case["alias"]]
              and len(fixed) == case["expected_fixed_DOFs"], "Workpiece counts differ from declared construction")
        check(np.array_equal(nodes, np.unique(new["connectivity"][cells]))
              and np.array_equal(dofs, (2*nodes[:, None]+np.arange(2)).ravel()), "Workpiece nodes/uxuy DOFs differ")
        check(not np.intersect1d(nodes, new["solid_nodes"]).size, "Workpiece shares original mechanism nodes")
        check(np.array_equal(fixed, np.union1d(old["fixed_dofs"], dofs)), "Merged fixed DOFs differ")
        check(np.array_equal(free, np.setdiff1d(np.arange(2*len(new["coordinates"])), fixed)), "Free DOFs differ")
        background = np.asarray(saved["region_metadata"]["background_symmetry"]["dofs"], dtype=np.int64)
        check(np.array_equal(overlap, np.intersect1d(dofs, background)), "Background overlap differs")
        for name in new.files:
            array = new[name]
            fields[name] = dict(dtype=array.dtype.name, shape=list(array.shape), sha256=sha256(array.tobytes(order="C")).hexdigest())
        check(fields == saved["arrays"]["fields"], "Saved model array declarations differ")
    return dict(schema_version="native-workpiece-construction-inspection-1.0", alias=case["alias"], status="pass",
        model_descriptor_sha256=digest(descriptor), model_descriptor_semantic_sha256=saved["descriptor_sha256"],
        model_arrays_sha256=digest(descriptor.parent/"model.npz"),
        task_sha256=saved["task_sha256"], source_geometry=saved["source_geometry"],
        original_non_boundary_arrays_byte_identical=unchanged, original_non_boundary_array_count=len(unchanged),
        model_array_count=len(fields), model_array_fields=fields, counts=saved["region_metadata"]["counts"],
        workpiece=dict(cells=expected_cells, nodes=expected_nodes, fixed_dofs=2*expected_nodes,
                       background_overlap_dofs=expected_overlap, merged_fixed_dofs=expected_fixed,
                       initial_gaps_mm=body["initial_gaps_mm"], definition=body["definition"],
                       cell_selection=body["cell_selection"], boundary_representation=body["boundary_representation"]),
        task_path=saved["task"]["path"], path_executed=False, response_evaluated=False,
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0, contact_qualified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT/"lf_data_preparation/native_workpiece_001/input_inventory.json")
    args = parser.parse_args()
    inventory_path = args.inventory.resolve()
    stage = inventory_path.parent
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    freeze_path = stage/"source_freeze.json"
    frozen_context = json.loads(freeze_path.read_text(encoding="utf-8"))
    cases = inventory["cases"]
    check([case["alias"] for case in cases] == list(FACTS), "Expected the three declared workpiece cases")
    summary_path, capsule = stage/"construction_summary.json", stage/"construction_sources"
    outputs = [stage/case["model_directory"] for case in cases]
    check(not summary_path.exists() and not capsule.exists() and all(not path.exists() for path in outputs),
          "Construction outputs must all be new")
    inputs = dict(inventory["input_bindings"])
    for path in (inventory_path, freeze_path):
        inputs[path.relative_to(ROOT).as_posix()] = digest(path)
    for case in cases:
        prior = ROOT/case["original_native_model"]
        metadata_path = prior.with_suffix(".json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        inputs[case["original_native_model"]] = metadata["arrays"]["sha256"]
        inputs[metadata_path.relative_to(ROOT).as_posix()] = digest(metadata_path)
    check(all(digest(ROOT/name) == expected for name, expected in inputs.items()), "An original task/input/model binding changed")
    sources = {name: digest(ROOT/name) for name in SOURCES}
    check(all(sources[name] == frozen_context["sources"][name] for name in SOURCES[:-1]),
          "A construction dependency differs from the declared source freeze")
    capsule.mkdir()
    for name in sources:
        (capsule/Path(name).name).write_bytes((ROOT/name).read_bytes())
    guard_calls = {}

    def guard(name):
        guard_calls[name] = 0
        def forbidden(*args, **kwargs):
            guard_calls[name] += 1
            raise RuntimeError("Construction attempted a forbidden response: "+name)
        return forbidden

    for module, names in ((tmc, ("assemble", "solve_path", "batch_response")), (tmc_kernel, ("batch_response", "_runtime"))):
        for name in names:
            setattr(module, name, guard(module.__name__+"."+name))
    record = dict(schema_version="native-workpiece-construction-execution-1.0", status="running",
        started_utc=datetime.now(timezone.utc).isoformat(), baseline_commit=inventory["baseline_commit"],
        inventory_sha256=digest(inventory_path), source_context_sha256=digest(freeze_path),
        sources=sources, input_bindings=inputs, cases=[], construction_invocations=0, write_invocations=0,
        guard_calls=guard_calls, response_evaluated=False, path_executed=False,
        force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0, LF_imports=0,
        qualification_scope="construction only; no pressure, clamping, unloading, H2/H3 or HF qualification",
        process_seconds_limit=inventory["construction_outer_seconds"], sampled_RSS_limit_bytes=inventory["sampled_RSS_limit_bytes"],
        budget_mode="Cooperative elapsed/current RSS and Windows process peak samples; root supplies the outer launch limit")
    process, peak = psutil.Process(), 0

    def sample():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        check(perf_counter()-STARTED <= record["process_seconds_limit"] and peak <= record["sampled_RSS_limit_bytes"],
              "Construction elapsed/RSS budget exceeded")

    try:
        sample()
        for case, output in zip(cases, outputs):
            sample()
            record["active_case"] = case["alias"]
            task = json.loads((ROOT/case["task_file"]).read_text(encoding="utf-8"))
            check(task["path"]["targets_mm"] == case["path_instruction_mm"] and not case["path_executed_by_construction"],
                  "Construction path instruction differs")
            record["construction_invocations"] += 1
            project = build_native_project(ROOT/case["geometry_file"], task)
            sample()
            record["write_invocations"] += 1
            descriptor = write_native_project(project, output)
            sample()
            inspection = inspect_model(descriptor, ROOT/case["original_native_model"], case)
            check(not any(guard_calls.values()), "Response guard was invoked")
            inspection_path = output/"inspection.json"
            write_json(inspection_path, inspection)
            record["cases"].append(dict(alias=case["alias"], status="pass", model_directory=case["model_directory"],
                model_descriptor_sha256=inspection["model_descriptor_sha256"], model_arrays_sha256=inspection["model_arrays_sha256"],
                inspection_sha256=digest(inspection_path), counts=inspection["counts"], workpiece=inspection["workpiece"]))
        check(all(digest(ROOT/name) == expected for name, expected in inputs.items()), "Input changed during construction")
        check(all(digest(ROOT/name) == expected and digest(capsule/Path(name).name) == expected for name, expected in sources.items()),
              "Source/capsule changed during construction")
        sample()
        record.update(status="pass", original_inputs_and_sources_unchanged=True)
    except Exception as error:
        record.update(status="failed", error=repr(error))
        raise
    finally:
        record.update(completed_cases=len(record["cases"]), elapsed_seconds=perf_counter()-STARTED,
                      peak_sampled_RSS_bytes=peak, completed_utc=datetime.now(timezone.utc).isoformat())
        write_json(summary_path, record)
    print(json.dumps(dict(status=record["status"], cases=len(record["cases"]), elapsed_seconds=record["elapsed_seconds"],
                          response_evaluated=False, path_executed=False)))


if __name__ == "__main__":
    main()
