from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json
import sys
from time import perf_counter

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "hf_repo/src"))
from hf_eval.native_map import prepare_native_geometry, write_native_geometry_map

LIMIT_SECONDS = 120
LIMIT_BYTES = 8 * 1024**3
SOURCE_FILES = (
    "hf_repo/src/hf_eval/native_map.py", "hf_repo/src/hf_eval/data.py",
    "hf_repo/src/hf_eval/regions.py", "hf_repo/src/hf_eval/__init__.py",
    "hf_repo/scripts/prepare_native_geometry.py",
    "hf_repo/scripts/plot_native_geometry_map.py", "hf_repo/tests/test_native_map.py",
    "lf_data_preparation/native_q1_001/review_mapping.py",
    "lf_data_preparation/native_q1_001/execute_mapping.py",
)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    inventory_path = STAGE / "input_inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inputs = {row["alias"]: row for row in inventory["inputs"]}
    assert tuple(inputs) == ("inverter_canonical", "gripper_canonical", "gripper_native_fine")
    assert inventory["baseline_commit"] == "ccbd902aad73abebeb171795e3d37b98d88dd1b8"
    sources = {name: digest(ROOT / name) for name in SOURCE_FILES}
    frozen = STAGE / "sources"
    frozen.mkdir(exist_ok=False)
    for name in SOURCE_FILES:
        (frozen / Path(name).name).write_bytes((ROOT / name).read_bytes())
    for row in inputs.values():
        assert digest(ROOT / row["descriptor"]) == row["descriptor_sha256"]
        assert digest(ROOT / row["array"]) == row["array_sha256"]
    record = {
        "schema_version": "native-q1-mapping-execution-1.0",
        "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_commit": inventory["baseline_commit"],
        "input_inventory_sha256": digest(inventory_path),
        "continuous_seconds": LIMIT_SECONDS, "sampled_RSS_limit_bytes": LIMIT_BYTES,
        "sources": sources, "cases": [], "LF_imports": 0,
        "mechanics_assembly_calls": 0, "force_calls": 0, "HP_calls": 0, "solver_calls": 0,
        "scope": "Native geometry map only; no materials, applied constraints, task or HF analysis policy selected",
        "budget_mode": "Cooperative elapsed/RSS checks; not hard OS supervision",
    }
    process = psutil.Process()
    peak_rss = 0
    start = perf_counter()

    def checkpoint():
        nonlocal peak_rss
        peak_rss = max(peak_rss, process.memory_info().rss)
        if peak_rss > LIMIT_BYTES or perf_counter() - start > LIMIT_SECONDS:
            raise RuntimeError("Native mapping cooperative budget exceeded")

    try:
        checkpoint()
        for alias, row in inputs.items():
            case_start = perf_counter()
            mapped = prepare_native_geometry(ROOT / row["descriptor"])
            assert mapped.geometry.geometry_id == row["HF_geometry_id"]
            assert mapped.metadata["constraints_applied"] is False
            assert mapped.metadata["material_assigned"] is False
            assert mapped.metadata["task_created"] is False
            assert mapped.metadata["analysis_grid_policy"] == "not_selected"
            output = write_native_geometry_map(mapped, STAGE / "mapped" / alias)
            with np.load(output.with_suffix(".npz"), allow_pickle=False) as archive:
                assert set(archive.files) == set(mapped.arrays)
                for name, value in mapped.arrays.items():
                    np.testing.assert_array_equal(archive[name], value)
            record["cases"].append({
                "alias": alias, "status": "pass", "invocations": 1,
                "elapsed_seconds": perf_counter() - case_start,
                "map_descriptor": output.relative_to(STAGE).as_posix(),
                "descriptor_sha256": digest(output),
                "array_sha256": digest(output.with_suffix(".npz")),
                "HF_geometry_id": mapped.geometry.geometry_id,
                "native_shape_yx": mapped.geometry.grid["shape_yx"],
                "cells": len(mapped.arrays["connectivity"]),
                "nodes": len(mapped.arrays["coordinates_mm"]),
                "dofs": len(mapped.arrays["input_vector"]),
                "input_nodes": len(mapped.arrays["input_nodes"]),
                "output_nodes": len(mapped.arrays["output_nodes"]),
            })
            checkpoint()
        for name, expected in sources.items():
            assert digest(ROOT / name) == expected, name
        assert digest(inventory_path) == record["input_inventory_sha256"]
        for row in inputs.values():
            assert digest(ROOT / row["descriptor"]) == row["descriptor_sha256"]
            assert digest(ROOT / row["array"]) == row["array_sha256"]
        assert not any(name == "dmftd" or name.startswith("dmftd.") or
                       name.startswith(("hf_eval.tmc", "hf_eval.project", "hf_eval.split", "jax"))
                       for name in sys.modules)
        record.update(status="pass", input_and_source_identity_checked=True)
    except Exception as error:
        record.update(status="fail", error_type=type(error).__name__, error=str(error))
    finally:
        record.update(elapsed_seconds=perf_counter() - start, peak_sampled_RSS_bytes=peak_rss,
                      completed_cases=len(record["cases"]))
        with (STAGE / "execution_receipt.json").open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
    print(json.dumps({"status": record["status"], "cases": record["completed_cases"],
                      "elapsed_seconds": record["elapsed_seconds"]}))
    return 0 if record["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
