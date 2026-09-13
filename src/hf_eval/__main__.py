"""Portable CLI; all inputs are explicit files, independent of current directory."""
import argparse
import json
from .evaluation import evaluate, inspect_geometry


def main(argv=None):
    parser = argparse.ArgumentParser(description="HF-1 independent solid linear diagnostics")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Validate geometry and report qualification measurements")
    inspect.add_argument("geometry")
    run = sub.add_parser("evaluate", help="Evaluate one geometry with an explicit task and solver")
    run.add_argument("geometry")
    run.add_argument("--task", required=True)
    run.add_argument("--solver", required=True)
    run.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "inspect":
        result = inspect_geometry(args.geometry)
        success = result["readability"]["status"] == "pass"
    else:
        result = evaluate(args.geometry, args.task, args.solver, args.output)
        success = result["numerics"]["status"] == "success"
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
