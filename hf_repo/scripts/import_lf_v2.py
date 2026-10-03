"""Convert one ordinary LF v2 JSON/NPZ package; no optimization or mechanics."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.data import GeometryError
from hf_eval.lf_v2 import convert_lf_v2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="ordinary LF v2 design.json")
    parser.add_argument("--output", type=Path, required=True, help="new HF geometry directory")
    parser.add_argument("--expected-descriptor-sha256", help="optional expected SHA256 of the original JSON bytes")
    args = parser.parse_args()
    try:
        result = convert_lf_v2(args.source, args.output, expected_descriptor_sha256=args.expected_descriptor_sha256)
    except (GeometryError, OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"LF v2 conversion failed: {error}\n")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
