"""Wall-time of the legacy and the compensated split kernels on one saved state (no solve, no admission).

Engineering measurement for planning a later path re-test: the compensated F costs extra floating-point
work. Each kernel is compiled once (warm-up, recorded separately) and then timed on the unchanged saved
state with and without the tangent. Nothing is compared against a gate.

Usage (restored S0 baseline tree required):
    python hf_repo/scripts/time_contact_c2_split_kernels.py --baseline <tree> --output <new json>
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

REPO = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("choose a new output path")
    os.environ["JAX_PLATFORMS"] = "cpu"
    import numpy as np
    import jax
    jax.config.update("jax_enable_x64", True)
    sys.path.insert(0, str(REPO / "src"))
    from hf_eval import split_kernel, split_kernel_compensated
    from hf_eval.split_state import SplitDisplacement
    from hf_eval.tmc import TMCModel

    stage = args.baseline / "hf4_c2_diagnostics/experiments/mesh_h00625/stages/uniform_tmc"
    metadata = json.loads((stage / "metadata.json").read_text(encoding="utf-8"))
    entry = next(e for e in json.loads((stage / "steps/index.json").read_text(encoding="utf-8"))["steps"] if e["index"] == 20)
    with np.load(stage / "model.npz", allow_pickle=False) as archive:
        fixture = {key: archive[key] for key in archive.files}
    with np.load(stage / "steps" / entry["file"], allow_pickle=False) as archive:
        state = SplitDisplacement(archive["u_lift"], archive["u_fluctuation"])
    h = float(metadata["h"])
    model = TMCModel(fixture["coordinates"], fixture["connectivity"], fixture["lam"], fixture["mu"], float(fixture["kr"]), h, h,
                     float(fixture.get("thickness", 1.0)), fixture.get("solid"), fixture["fixed_dofs"])
    rows = []
    for name, kernel in (("legacy", split_kernel), ("compensated", split_kernel_compensated)):
        for tangent in (False, True):
            begin = time.perf_counter()
            kernel.assemble_split(model, state, tangent=tangent)
            first = time.perf_counter() - begin
            samples = []
            for _ in range(args.repeats):
                begin = time.perf_counter()
                _, _, fields = kernel.assemble_split(model, state, tangent=tangent)
                samples.append(time.perf_counter() - begin)
            rows.append(dict(kernel=name, kernel_version=kernel.KERNEL_VERSION, tangent=tangent, first_call_seconds_including_compile=first,
                             repeated_seconds=samples, median_seconds=statistics.median(samples),
                             median_kernel_seconds=statistics.median([fields["timing_seconds"]["kernel_and_transfer"]])))
    record = dict(schema="contact-c2-split-kernel-timing-1", created_utc=datetime.now(timezone.utc).isoformat(),
                  state="hf4_c2_diagnostics/experiments/mesh_h00625/stages/uniform_tmc/steps/" + entry["file"], elements=int(model.ne),
                  dofs=int(model.ndof), repeats=args.repeats, python=platform.python_version(), numpy=np.__version__, jax=jax.__version__,
                  threads={k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
                  scope="wall-time of force (and tangent) assembly on one unchanged saved state; no solve, no gate", rows=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    print(json.dumps([(r["kernel"], r["tangent"], round(r["median_seconds"], 4), round(r["first_call_seconds_including_compile"], 2)) for r in rows]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
