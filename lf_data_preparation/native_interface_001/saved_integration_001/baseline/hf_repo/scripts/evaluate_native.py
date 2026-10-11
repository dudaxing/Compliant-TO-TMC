"""Evaluate one ordinary native geometry/task and print its compact response."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.native_evaluate import evaluate_native


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="Base for relative input/output paths; otherwise cwd")
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New evaluation directory")
    parser.add_argument("--targets", type=float, nargs="+")
    parser.add_argument("--time-limit", type=float, default=180., help="Controller limit, not total CLI wall time")
    parser.add_argument("--minimum-increment", type=float)
    parser.add_argument("--response-mode", choices=("complete", "mechanical"), default="complete")
    parser.add_argument("--tangent-mode", choices=("full", "chunk256"), default="full")
    parser.add_argument("--initial-guess", choices=("tangent", "port_projection"), default="tangent")
    args = parser.parse_args()
    try:
        response = evaluate_native(args.geometry, args.task, args.output, repo_root=args.repo,
            targets=args.targets, time_limit_seconds=args.time_limit,
            minimum_increment=args.minimum_increment, response_mode=args.response_mode,
            tangent_mode=args.tangent_mode, initial_guess=args.initial_guess)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Native evaluation could not save its response: {error}\n")
    print(json.dumps(response, indent=2, ensure_ascii=False, allow_nan=False))
    return 0 if response["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
