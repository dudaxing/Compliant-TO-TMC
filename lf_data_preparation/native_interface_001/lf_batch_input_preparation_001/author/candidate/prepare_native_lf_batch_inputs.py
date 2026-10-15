"""Prepare native batch inputs from a source manifest; no evaluation."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from hf_eval.lf_native_batch_inputs import prepare_native_lf_batch_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True, help='Base for every relative input and output path')
    parser.add_argument('--manifest', type=Path, required=True, help='Ordinary LF source-manifest JSON')
    parser.add_argument('--output', type=Path, required=True, help='New preparation directory; partial artifacts retained')
    args = parser.parse_args()
    try:
        result = prepare_native_lf_batch_inputs(args.manifest, args.output, repo_root=args.repo)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Native LF batch-input preparation failed; partial artifacts are retained: {error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
