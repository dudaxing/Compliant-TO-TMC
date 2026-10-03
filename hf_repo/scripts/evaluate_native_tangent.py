"""Evaluate three complete NumPy tangents at an ordinary native split state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.native_tangent import evaluate_native_tangent, write_native_tangent
from hf_eval.split_state import SplitDisplacement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True, help="ordinary HF geometry.json")
    parser.add_argument("--task", type=Path, required=True, help="explicit native project task JSON")
    parser.add_argument("--state", type=Path, required=True, help="NPZ with exactly lift and fluctuation full-DOF arrays")
    parser.add_argument("--output", type=Path, required=True, help="new tangent result directory")
    args = parser.parse_args()
    try:
        task = json.loads(args.task.read_text(encoding="utf-8"))
        with np.load(args.state, allow_pickle=False) as archive:
            if set(archive.files) != {"lift", "fluctuation"}:
                raise ValueError("State NPZ must contain exactly lift and fluctuation")
            state = SplitDisplacement(archive["lift"], archive["fluctuation"])
        result = evaluate_native_tangent(args.geometry, task, state)
        write_native_tangent(result, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Native tangent evaluation failed: {error}\n")
    print(json.dumps(dict(result_file="result.json", counts=result.metadata["counts"], matrix_units="N/mm",
        matrix_statistics=result.metadata["matrix_statistics"], equilibrium_qualified=False,
        task_target_executed=False), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
