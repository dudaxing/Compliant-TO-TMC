"""Prepare one LF v2 package and an explicit native task; no evaluation."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from hf_eval.lf_native_inputs import prepare_native_lf_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, help='Base for relative paths; otherwise current working directory')
    parser.add_argument('--source-descriptor', type=Path, required=True, help='Ordinary LF v2 design.json')
    parser.add_argument('--task-template', type=Path, required=True, help='Complete explicit native task1.0/1.1 JSON; physics preserved')
    parser.add_argument('--output', type=Path, required=True, help='New case directory; errors retain actual partial outputs')
    parser.add_argument('--right-medium-width-mm', type=float, help='None or zero keeps native; positive exact integer native dx columns')
    parser.add_argument('--expected-descriptor-sha256', help='Optional original LF descriptor raw SHA256')
    args = parser.parse_args()
    try:
        result = prepare_native_lf_inputs(args.source_descriptor, args.task_template, args.output,
            repo_root=args.repo, right_medium_width_mm=args.right_medium_width_mm,
            expected_descriptor_sha256=args.expected_descriptor_sha256)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Native LF input preparation failed; partial artifacts are retained: {error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
