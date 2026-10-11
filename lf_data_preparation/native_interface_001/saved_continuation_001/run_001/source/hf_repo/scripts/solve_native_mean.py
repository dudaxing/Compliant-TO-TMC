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
from hf_eval.native_resume import saved_resume_defaults


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, help="Required for zero start; otherwise saved source geometry")
    parser.add_argument("--task", type=Path, help="Required for zero start; otherwise saved original task")
    parser.add_argument("--saved-result", type=Path, help="Original saved result to continue")
    parser.add_argument("--selected-state-index", type=int, help="Accepted row index; paired with --saved-result")
    parser.add_argument("--output", type=Path, required=True, help="New result directory")
    parser.add_argument("--targets", type=float, nargs="+", help="Explicit targets; must match a declared 1.1 path. Otherwise task path or [0, task target]")
    parser.add_argument("--time-limit", type=float, default=180.)
    parser.add_argument("--minimum-increment", type=float, help="Otherwise the first nonzero target / 16")
    parser.add_argument("--response-mode", choices=("complete", "mechanical"),
                        help="Mechanical mode explicitly omits auxiliary material energy")
    parser.add_argument("--tangent-mode", choices=("full", "chunk256"),
                        help="Optional element blocks retain the full-batch arithmetic selector")
    parser.add_argument("--initial-guess", choices=("tangent", "port_projection"),
                        help="Explicit Newton initialization; existing tangent default is retained")
    args = parser.parse_args()
    try:
        if (args.saved_result is None) != (args.selected_state_index is None):
            raise ValueError("--saved-result and --selected-state-index must be paired")
        restored = None if args.saved_result is None else saved_resume_defaults(args.saved_result,args.selected_state_index,
            time_limit_seconds=args.time_limit)
        task = json.loads(args.task.read_text(encoding="utf-8")) if args.task is not None else (restored["task"] if restored is not None else None)
        if task is None or (args.geometry is None and restored is None):
            raise ValueError("Zero-start solve requires --geometry and --task")
        targets = args.targets if args.targets is not None else (restored["targets"] if restored is not None else
            task.get("path",{}).get("targets_mm",[0.,task["input"]["target_mm"]]))
        if len(targets) < 2:
            raise ValueError("At least zero and one nonzero target are required")
        if restored is not None:
            if args.minimum_increment is not None:
                raise ValueError("Saved continuation preserves the parent's minimum increment")
            settings = restored["settings"]
        else:
            increment = targets[1]/16 if args.minimum_increment is None else args.minimum_increment
            settings = DisplacementSettings(minimum_increment=increment, time_limit_seconds=args.time_limit)
        result = solve_native_mean(args.geometry, task, targets, settings=settings,
                                   response_mode=args.response_mode, tangent_mode=args.tangent_mode,
                                   initial_guess=args.initial_guess,saved_result=args.saved_result,
                                   selected_state_index=args.selected_state_index)
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
