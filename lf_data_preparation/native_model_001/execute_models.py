"""Single native-model construction run; no response, assembly or solve."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

import psutil

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
SOURCE_PATHS = (
    "hf_repo/src/hf_eval/native_project.py", "hf_repo/src/hf_eval/native_map.py",
    "hf_repo/src/hf_eval/data.py", "hf_repo/src/hf_eval/regions.py",
    "hf_repo/src/hf_eval/project.py", "hf_repo/src/hf_eval/tmc.py",
    "hf_repo/src/hf_eval/tmc_kernel.py", "hf_repo/src/hf_eval/__init__.py",
    "hf_repo/scripts/prepare_native_project.py", "hf_repo/scripts/plot_native_project.py",
    "hf_repo/tests/test_native_project.py",
    "lf_data_preparation/native_model_001/review_models.py",
    "lf_data_preparation/native_model_001/execute_models.py",
)
SECONDS = 120
RSS_LIMIT = 8 * 1024**3


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    receipt_path = STAGE / "execution_receipt.json"
    if receipt_path.exists() or (STAGE / "models").exists() or (STAGE / "sources").exists():
        raise RuntimeError("Production destinations must be new")
    inventory_path = STAGE / "input_inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    cases = inventory["cases"]
    if [c["alias"] for c in cases] != ["inverter_canonical", "gripper_canonical", "gripper_native_fine"]:
        raise RuntimeError("Unexpected production cases")
    inputs = {}
    for case in cases:
        for path_key, sha_key in (("geometry_file", "geometry_file_sha256"),
                                  ("task_file", "task_file_sha256"),
                                  ("old_model_file", "old_model_sha256"),
                                  ("old_parameter_task_file", "old_parameter_task_file_sha256")):
            name = case[path_key]
            inputs[name] = case[sha_key]
        geometry_path = ROOT / case["geometry_file"]
        geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
        npz_name = geometry_path.with_name(geometry["arrays"]["path"]).relative_to(ROOT).as_posix()
        inputs[npz_name] = case["geometry_npz_sha256"]
    for name, expected in inputs.items():
        if digest(ROOT / name) != expected:
            raise RuntimeError("Changed input: " + name)
    sources = {name: digest(ROOT / name) for name in SOURCE_PATHS}
    frozen = STAGE / "sources"
    frozen.mkdir()
    for name in sources:
        (frozen / Path(name).name).write_bytes((ROOT / name).read_bytes())
    record = dict(schema_version="native-model-construction-execution-1.0", status="running",
        baseline_commit=inventory["baseline_commit"], started_utc=datetime.now(timezone.utc).isoformat(),
        input_inventory_sha256=digest(inventory_path), sources=sources, inputs=inputs, cases=[],
        process_seconds_limit=SECONDS, sampled_RSS_limit_bytes=RSS_LIMIT,
        budget_mode="Cooperative production elapsed/RSS samples, not hard OS supervision",
        scope="Three explicit TEST tasks construct native models only; no study H2/H3 policy or response qualification",
        LF_imports=0, mechanics_assembly_calls=0, force_calls=0, HP_calls=0, solver_calls=0)
    started = perf_counter()
    peak = 0

    def sample():
        nonlocal peak
        peak = max(peak, psutil.Process().memory_info().rss)
        if perf_counter() - started > SECONDS or peak > RSS_LIMIT:
            raise RuntimeError("Production elapsed/RSS bound exceeded")

    try:
        sys.path.insert(0, str(ROOT / "hf_repo" / "src"))
        from hf_eval.data import canonical_hash
        from hf_eval.native_project import build_native_project, write_native_project
        sample()
        for case in cases:
            sample()
            begin = perf_counter()
            task = json.loads((ROOT / case["task_file"]).read_text(encoding="utf-8"))
            project = build_native_project(ROOT / case["geometry_file"], task)
            if project.geometry.geometry_id != case["geometry_id"] or project.task_hash != canonical_hash(task):
                raise RuntimeError("Constructed geometry/task identity differs")
            output = STAGE / "models" / case["alias"]
            descriptor = write_native_project(project, output)
            sample()
            record["cases"].append(dict(alias=case["alias"], status="pass", invocations=1,
                elapsed_seconds=perf_counter()-begin, model_descriptor=descriptor.relative_to(STAGE).as_posix(),
                model_descriptor_sha256=digest(descriptor), model_npz_sha256=digest(output / "model.npz"),
                geometry_id=project.geometry.geometry_id, task_sha256=project.task_hash,
                cells=project.model.ne, nodes=len(project.model.coordinates), dofs=project.model.ndof,
                fixed_dofs=len(project.model.fixed_dofs), free_dofs=len(project.model.free),
                input_dofs=int((project.bin != 0).sum()), output_dofs=int((project.bout != 0).sum())))
        for name, expected in sources.items():
            if digest(ROOT / name) != expected or digest(frozen / Path(name).name) != expected:
                raise RuntimeError("Changed execution source: " + name)
        for name, expected in inputs.items():
            if digest(ROOT / name) != expected:
                raise RuntimeError("Input changed during construction: " + name)
        sample()
        record.update(status="pass", input_and_source_identity_checked=True)
    except Exception as error:
        record.update(status="fail", error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-started, peak_sampled_RSS_bytes=peak,
                      completed_cases=len(record["cases"]), completed_utc=datetime.now(timezone.utc).isoformat())
        with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps(dict(status=record["status"], cases=len(record["cases"]),
                         elapsed_seconds=record["elapsed_seconds"], mechanics_calls=0)))


if __name__ == "__main__":
    main()
