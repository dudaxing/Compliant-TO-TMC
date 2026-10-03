"""Solve and save an ordinary native NumPy mean-displacement path."""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from hf_eval.displacement import DisplacementSettings
from hf_eval.native_mean import solve_native_mean, write_native_mean


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New result directory")
    parser.add_argument("--targets", type=float, nargs="+", help="Explicit targets; must match a declared 1.1 path. Otherwise task path or [0, task target]")
    parser.add_argument("--time-limit", type=float, default=180.)
    parser.add_argument("--minimum-increment", type=float, help="Otherwise the first nonzero target / 16")
    args = parser.parse_args()
    try:
        task = json.loads(args.task.read_text(encoding="utf-8"))
        targets = (task["path"]["targets_mm"] if "path" in task else [0., task["input"]["target_mm"]]) if args.targets is None else args.targets
        if len(targets) < 2:
            raise ValueError("At least zero and one nonzero target are required")
        increment = targets[1]/16 if args.minimum_increment is None else args.minimum_increment
        settings = DisplacementSettings(minimum_increment=increment, time_limit_seconds=args.time_limit)
        result = solve_native_mean(args.geometry, task, targets, settings=settings)
        descriptor = write_native_mean(result, args.output)
        elapsed = perf_counter()-STARTED
        if elapsed > args.time_limit:
            raise ValueError("Native mean CLI wall-time bound exceeded; saved path remains available")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Native mean path failed: {error}\n")
    print(json.dumps(dict(result_file=str(descriptor), status=result.metadata["status"],
        accepted_states=len(result.accepted), call_counts=result.metadata["call_counts"],
        reached_displacement=result.metadata["reached_displacement"], elapsed_seconds=elapsed,
        equilibrium_qualified=False), indent=2))
    return 0 if result.path["target_reached"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
