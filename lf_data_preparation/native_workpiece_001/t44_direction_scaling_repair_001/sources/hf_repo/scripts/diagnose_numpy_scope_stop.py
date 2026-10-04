"""Locate the first rejected DD result for one stored static scope input.

Instrument only this process, retain the original finish/check behavior, and
never evaluate JIT, high-precision reference mechanics, or equilibrium.
"""
import argparse
import inspect
from pathlib import Path
import shutil
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval import split_kernel_invariants_hu as kernel
from run_numpy_tangent_comparison import load_npz, make_model, read, sha, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--case", default="nondyadic_rect__tiny_strain")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    index = read(args.input / "index.json")
    row = next(r for r in index["cases"] if r["case"] == args.case)
    fixture, state = (load_npz(args.input / row[key]) for key in ("model_file", "state_file"))
    model = make_model(fixture, row["metadata"])
    ci, finish = kernel.ci, kernel.ci._finish
    rejections = []
    def number(value):
        value = float(value)
        return value if np.isfinite(value) else str(value)
    def observe(high, low, valid, xp):
        result = finish(high, low, valid, xp)
        failed = ~np.isfinite(result[0])
        if np.any(failed) and len(rejections) < 8:
            high, low, valid = np.broadcast_arrays(high, low, valid)
            position = tuple(np.argwhere(failed)[0])
            temporary = (np.isfinite(high) & np.isfinite(low) &
                         (np.abs(high) <= ci.TEMPORARY_MAX) & (np.abs(low) <= ci.TEMPORARY_MAX))
            normalized = ci._two_sum(np.where(temporary, high, 0.), np.where(temporary, low, 0.), np)
            calls = inspect.stack()[1:9]
            rejections.append(dict(position=list(map(int, position)),
                input_valid=bool(valid[position]), temporary_valid=bool(temporary[position]),
                high=number(high[position]), low=number(low[position]),
                normalized_high=number(normalized[0][position]), normalized_low=number(normalized[1][position]),
                normalized_pair_supported=bool(ci._pair_mask(normalized, np)[position]),
                stack=[dict(file=Path(frame.filename).name, line=frame.lineno, function=frame.function) for frame in calls]))
        return result
    ci._finish = observe
    try:
        _, fields = kernel._response(state["u_lift"][model.edofs], state["u_fluctuation"][model.edofs],
                                    model.ops["grad"], model.ops["hessian"], model.ops["weights"],
                                    model.lam, model.mu, model.kr, np)
    finally:
        ci._finish = finish
    args.output.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(args.output / "raw_response.npz", **fields)
    paths = [Path(__file__), Path(kernel.__file__), Path(ci.__file__)]
    (args.output / "sources").mkdir()
    for path in paths:
        shutil.copyfile(path, args.output / "sources" / path.name)
    summary = dict(case=args.case, input_index_sha256=sha(args.input / "index.json"),
                   original_model_sha256=row["model_sha256"], first_rejections=rejections,
                   operand_min=ci.OPERAND_MIN, operand_max=ci.OPERAND_MAX,
                   finite_fields={k: bool(np.isfinite(v).all()) for k, v in fields.items()},
                   arithmetic_supported=fields["arithmetic_supported"].tolist(),
                   sources=[dict(path=p.name, sha256=sha(p)) for p in paths],
                   instrumentation_changes_acceptance=False, equilibrium_solved=False, HP_generated=False)
    write(args.output / "summary.json", summary)
    print(summary["first_rejections"][0] if rejections else "No rejection observed")


if __name__ == "__main__":
    main()
