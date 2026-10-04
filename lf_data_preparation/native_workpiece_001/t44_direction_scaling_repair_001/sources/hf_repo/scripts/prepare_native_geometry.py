"""Save native Q1 geometry, ports and candidate nodes without a physical task."""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.native_map import prepare_native_geometry, write_native_geometry_map


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True, help="ordinary HF geometry.json")
    parser.add_argument("--output", type=Path, required=True, help="new native mapping directory")
    args = parser.parse_args()
    try:
        mapping = prepare_native_geometry(args.geometry)
        write_native_geometry_map(mapping, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Native geometry preparation failed: {error}\n")
    print(json.dumps(dict(map_file="map.json", source_geometry_id=mapping.metadata["source_geometry_id"],
                         counts=mapping.metadata["counts"], analysis_grid_policy="not_selected",
                         constraints_applied=False, material_assigned=False, task_created=False), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
