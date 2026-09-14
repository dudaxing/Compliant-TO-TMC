"""Portable CLI; all inputs are explicit files, independent of current directory."""
import argparse
import json
from .evaluation import evaluate, inspect_geometry


def main(argv=None):
    parser = argparse.ArgumentParser(description="Independent HF linear and project displacement evaluation")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Validate geometry and report qualification measurements")
    inspect.add_argument("geometry")
    run = sub.add_parser("evaluate", help="Evaluate one geometry with an explicit task and solver")
    run.add_argument("geometry")
    run.add_argument("--task", required=True)
    run.add_argument("--solver", required=True)
    run.add_argument("--output", required=True)
    benchmark = sub.add_parser("tmc-cshape", help="Run the single source-numeric HF-2 C-shape code benchmark")
    benchmark.add_argument("--output", required=True)
    benchmark.add_argument("--source-setup", help="Optional ordinary NPZ containing source-exported targets")
    benchmark.add_argument("--time-limit", type=float, default=1200.0)
    args = parser.parse_args(argv)
    if args.command == "inspect":
        result = inspect_geometry(args.geometry)
        success = result["readability"]["status"] == "pass"
    elif args.command == "evaluate":
        import os
        os.environ['JAX_ENABLE_X64'] = 'true'
        os.environ['JAX_PLATFORMS'] = 'cpu'
        result = evaluate(args.geometry, args.task, args.solver, args.output)
        success = result["numerics"]["status"] == "success"
    else:
        import os
        os.environ['JAX_ENABLE_X64'] = 'true'
        os.environ['JAX_PLATFORMS'] = 'cpu'
        from .tmc_benchmark import run_cshape, validate_source_setup
        targets = None
        if args.source_setup:
            targets = validate_source_setup(args.source_setup)
        result = run_cshape(args.output, source_targets=targets,time_limit_seconds=args.time_limit)
        success = result['status'] == 'success'
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
