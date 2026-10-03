"""Measure actual Q1 exterior distances from an existing saved native path.

This saved-state reader imports only the pure geometry module and NumPy. It
does not construct a model or evaluate forces, tangents, solvers or references.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from hf_eval.boundary_geometry import measure_native_workpiece_boundaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Saved result directory or result.json")
    parser.add_argument("--output", type=Path, required=True, help="New exclusive measurement directory")
    args = parser.parse_args()
    result_file = args.input if args.input.is_file() else args.input/"result.json"
    directory = result_file.parent
    pins = {}

    def bind(path, expected=None):
        value = sha256(path.read_bytes()).hexdigest()
        if expected is not None and value != expected:
            raise ValueError("Saved file identity differs: "+path.name)
        pins[path.resolve()] = value

    def read(path, expected=None):
        bind(path, expected)
        return json.loads(path.read_text(encoding="utf-8"))

    def archive(path, expected):
        bind(path, expected)
        with np.load(path, allow_pickle=False) as saved:
            return {name: saved[name].copy() for name in saved.files}

    try:
        result = read(result_file)
        model_file = directory/result["model"]["descriptor_path"]
        metadata = read(model_file, result["model"]["descriptor_file_sha256"])
        model = archive(model_file.parent/metadata["arrays"]["path"], metadata["arrays"]["sha256"])
        if (metadata["descriptor_sha256"] != result["model"]["descriptor_sha256"]
                or metadata["arrays"]["sha256"] != result["model"]["arrays_sha256"]
                or metadata["task_sha256"] != result["task_sha256"]):
            raise ValueError("Saved model and result bindings differ")
        rows = []
        for index, record in enumerate(result["states"]):
            state = archive(directory/record["state"]["path"], record["state"]["sha256"])
            if set(state) != {"lift", "fluctuation"}:
                raise ValueError("Expected saved lift and fluctuation vectors")
            geometry = measure_native_workpiece_boundaries(model, metadata, state["lift"], state["fluctuation"])
            rows.append(dict(accepted_index=index, d_mm=record["d"], leg=record["leg"],
                original_target_index=record["original_target_index"], state_sha256=record["state_sha256"],
                node_window_clearance_mm=record["workpiece"]["node_window_clearance_mm"],
                node_window_scope=record["workpiece"]["clearance_scope"], geometry=geometry))
        bind(Path(__file__))
        bind(Path(sys.modules["hf_eval.boundary_geometry"].__file__))
        if any(sha256(path.read_bytes()).hexdigest() != value for path, value in pins.items()):
            raise ValueError("Saved inputs changed during geometry measurement")
        report = dict(schema_version="native-workpiece-boundary-path-1.0", production_status=result["status"],
            task_sha256=result["task_sha256"], accepted_states=rows,
            input_files_sha256={str(path): value for path, value in pins.items()}, input_files_unchanged=True,
            scope="Saved accepted states only; unsigned Q1 exterior geometry; no mechanics/contact qualification",
            force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0)
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
        (output/"boundary_measurements.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        parser.exit(1, f"Saved boundary measurement failed: {error}\n")
    print(json.dumps(dict(accepted_states=len(rows), output=str(output), new_mechanics_calls=0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
