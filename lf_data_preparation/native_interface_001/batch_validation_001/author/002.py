"""Run a sequential native batch from any cwd with explicit --repo."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.native_batch import evaluate_native_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="Base of every relative path; otherwise caller cwd")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New directory for index.json")
    args = parser.parse_args()
    try:
        index = evaluate_native_batch(args.manifest, args.output, repo_root=args.repo)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Native batch could not start or save its index: {error}\n")
    print(json.dumps(index, indent=2, ensure_ascii=False, allow_nan=False))
    return 0 if index["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
