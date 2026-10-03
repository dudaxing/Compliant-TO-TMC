"""Extract a compact C1 task from immutable ordinary files; no FE calculation."""
import argparse
from pathlib import Path
import shutil

import numpy as np

from run_numpy_force_comparison import load_npz, read, sha, write


def native(path):
    path = path.resolve()
    return Path("\\\\?\\" + str(path)) if path.drive and not str(path).startswith("\\\\?\\") else path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--scope-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = native(args.reference)
    metadata = read(source / "metadata.json")
    stage = source / "stages/uniform_tmc"
    stage_metadata = read(stage / "metadata.json")
    index = read(args.scope_input / "index.json")
    run = args.reference.name
    rows = [r for r in index["cases"] if r.get("run") == run and r["kind"] == "saved"]
    terminal = max(rows, key=lambda r: r["entry"]["index"])
    model, state = (args.scope_input / terminal[key] for key in ("model_file", "state_file"))
    assert sha(model) == terminal["model_sha256"] == sha(stage / "model.npz")
    assert sha(state) == terminal["state_sha256"]
    assert sha(source / "audit.json") == terminal["source_files"][f"hf4_c1_results/{run}/audit.json"]
    assert metadata["h"] == stage_metadata["h"] == terminal["metadata"]["h"]
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(model, args.output / "model.npz")
    write(args.output / "metadata.json", metadata)
    write(args.output / "stage_metadata.json", stage_metadata)
    saved = load_npz(state)
    np.savez_compressed(args.output / "tangent_direction.npz", tangent_direction=saved["tangent_direction"])
    audit = read(source / "audit.json")
    write(args.output / "baseline_curve.json", dict(original_audit_sha256=sha(source / "audit.json"),
          comparison_only=True, states=[dict(d=s["physical_mean_drive"],
          normal_force_N=float(s["measurements"]["normal_force"]), original_status=s["status"])
          for s in audit["states"]]))
    paths = [args.scope_input / "index.json", model, state, source / "metadata.json",
             stage / "metadata.json", source / "audit.json"]
    write(args.output / "bindings.json", dict(scope="task extraction only; no candidate/HP/solve",
          sources=[dict(path=p.as_posix(), sha256=sha(p), bytes=p.stat().st_size) for p in paths],
          outputs=[dict(name=p.name, sha256=sha(p), bytes=p.stat().st_size)
                   for p in sorted(args.output.iterdir())],
          preparer_sha256=sha(Path(__file__))))
    shutil.copyfile(__file__, args.output / "preparer_source.py")
    print(f"extracted {run}, h={metadata['h']}, historical curve={len(audit['states'])} records")


if __name__ == "__main__":
    main()
