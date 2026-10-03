"""Save an explicitly bound native-grid Q1 model without evaluating a response."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.native_project import build_native_project, write_native_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True, help="ordinary HF geometry.json")
    parser.add_argument("--task", type=Path, required=True, help="explicit hf-native-project-task-1.0 JSON")
    parser.add_argument("--output", type=Path, required=True, help="new native model directory")
    args = parser.parse_args()
    try:
        task = json.loads(args.task.read_text(encoding="utf-8"))
        project = build_native_project(args.geometry, task)
        write_native_project(project, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Native project preparation failed: {error}\n")
    print(json.dumps(dict(model_file="model.json", task_sha256=project.task_hash,
                         source_geometry_id=project.geometry.geometry_id,
                         counts=project.region_metadata["counts"], analysis_grid_policy="native",
                         stored_input_target_mm=project.task["input"]["target_mm"], response_evaluated=False), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
