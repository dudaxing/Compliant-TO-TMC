"""Write a new HF analysis geometry with passive-void columns on its right."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.analysis_domain import write_right_medium_geometry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True, help="parent HF geometry.json or package directory")
    parser.add_argument("--output", type=Path, required=True, help="new derived HF geometry directory")
    parser.add_argument("--right-columns", type=int, required=True, help="positive count of passive-void columns")
    args = parser.parse_args()
    try:
        descriptor = write_right_medium_geometry(args.geometry, args.output, args.right_columns)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Analysis-domain preparation failed: {error}\n")
    print(json.dumps(dict(geometry_file=str(descriptor), right_columns=args.right_columns,
                         task_created=False, response_evaluated=False), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
