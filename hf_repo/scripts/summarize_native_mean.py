"""Summarize a saved native result without reading arrays or solving mechanics."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.native_response import summarize_saved_native_result, write_native_response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="Base for relative paths; otherwise cwd")
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New response JSON file")
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--view-manifest", type=Path)
    args = parser.parse_args()
    def resolve(path):
        if path is None:
            return None
        return (path if path.is_absolute() else (args.repo or Path.cwd()) / path).resolve()
    try:
        response = summarize_saved_native_result(resolve(args.result), repo_root=args.repo,
            reference_file=resolve(args.reference), view_manifest=resolve(args.view_manifest))
        response_file = write_native_response(response, resolve(args.output))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Saved native response failed: {error}\n")
    print(json.dumps(dict(response_file=str(response_file), status=response["status"]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
