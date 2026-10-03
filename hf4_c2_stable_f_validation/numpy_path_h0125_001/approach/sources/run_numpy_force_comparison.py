"""Compare complete NumPy split forces with saved HP80/120; no HP or FE solve.

The input directory is a frozen near-rotation case. Five small source files
are copied for a portable result. Decimal strings remain the force authority;
the original scales and thresholds are preserved. Run one case per invocation.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval import split_kernel_invariants_hu as kernel
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import TMCModel

COMPONENTS = ("total_force", "material_force", "regularization_force")
FIELDS = ("residual", "material_residual", "regularization_residual")
HP_FIELDS = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal")
LIMITS = (Decimal("1e-11"), Decimal("1e-9"), Decimal("1e-9"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False,
                               default=str) + "\n", encoding="utf-8")


def load_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def norm(vector):
    return sum((x*x for x in vector), Decimal(0)).sqrt()


def compare(vector, reference, scale):
    difference = [Decimal.from_float(float(a)) - b for a, b in zip(vector, reference)]
    return norm(difference)/scale, difference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    begin = perf_counter()
    args.output.mkdir(parents=True, exist_ok=False)
    inputs = args.output / "inputs"
    inputs.mkdir()
    bindings = []
    for name in ("inputs.npz", "input_freeze.json", "hp_0.json", "production_0.npz", "result.json"):
        origin = args.input / name
        shutil.copyfile(origin, inputs / name)
        bindings.append(dict(name=name, bytes=origin.stat().st_size, sha256=sha(origin)))
        assert sha(inputs / name) == bindings[-1]["sha256"]
    fixture = load_npz(inputs / "inputs.npz")
    freeze = read(inputs / "input_freeze.json")
    original = read(inputs / "result.json")
    hp = read(inputs / "hp_0.json")
    baseline = load_npz(inputs / "production_0.npz")
    assert freeze["input_sha256"] == sha(inputs / "inputs.npz")
    assert freeze["physical_authority"] == "exact D(lift)+D(fluctuation)"
    model = TMCModel(fixture["coordinates"], fixture["connectivity"], fixture["lam"],
                     fixture["mu"], float(fixture["kr"]), float(fixture["hx"]),
                     float(fixture["hy"]), float(fixture["thickness"]),
                     fixture["solid"], fixture["fixed_dofs"])
    for key in ("grad", "hessian", "weights"):
        assert np.array_equal(model.ops[key], fixture[key])
    L, w = fixture["u_lift"], fixture["u_fluctuation"]
    started = perf_counter()
    matrix, internal, fields = kernel.assemble_split_numpy(model, SplitDisplacement(L, w))
    assert matrix is None
    force_seconds = perf_counter() - started
    forces = {name: np.bincount(model.edofs.ravel(), weights=fields[key].ravel(), minlength=model.ndof)
              for name, key in zip(COMPONENTS, FIELDS)}
    np.testing.assert_array_equal(internal, forces["total_force"])
    arrays = dict(coordinates=model.coordinates, connectivity=model.connectivity, u_lift=L,
                  u_fluctuation=w, edofs=model.edofs, **forces,
                  **{key: value for key, value in fields.items() if key != "timing_seconds"})
    rows = []
    with localcontext() as context:
        context.prec = 120
        reference = {name: [Decimal(x) for x in hp["80"][key]] for name, key in zip(COMPONENTS, HP_FIELDS)}
        sf = Decimal(original["directions"][0]["force_scale"])
        fixed = set(map(int, fixture["fixed_dofs"]))
        total = reference["total_force"]
        assert sf == max(norm([x for i, x in enumerate(total) if i in fixed]),
                         norm([x for i, x in enumerate(total) if i not in fixed]),
                         Decimal("1e-8") * Decimal.from_float(freeze["force_scale_per_length"]) *
                         max(Decimal.from_float(freeze["level"]), Decimal("1e-6")))
        for name, hp_key, limit in zip(COMPONENTS, HP_FIELDS, LIMITS):
            ref = reference[name]
            assert len(ref) == model.ndof
            scale = sf if name == "total_force" else max(norm(ref), Decimal("1e-12")*sf)
            agreement = norm([a-Decimal(b) for a, b in zip(ref, hp["120"][hp_key])])/scale
            assert agreement <= Decimal("1e-40")
            error, difference = compare(forces[name], ref, scale)
            old_error, _ = compare(baseline[name], ref, scale)
            rows.append(dict(component=name, scale_N=scale, threshold=limit,
                             normalized_error=error, old_stable_F_normalized_error=old_error,
                             hp80_hp120_normalized_agreement=agreement, pass_gate=error <= limit))
            arrays["reference_" + name] = np.array([float(x) for x in ref])
            arrays["difference_" + name] = np.array([float(x) for x in difference])
            arrays["baseline_" + name] = baseline[name]
        decomposition = forces["total_force"] - (forces["material_force"] + forces["regularization_force"])
        # Bound rounding from the element outputs and separate global sums,
        # using absolute contributions before cancellation at shared nodes.
        magnitude = sum(np.abs(fields[key]) for key in FIELDS)
        absolute_sum = np.bincount(model.edofs.ravel(), weights=magnitude.ravel(), minlength=model.ndof)
        count = np.bincount(model.edofs.ravel(), minlength=model.ndof)
        rho = (count + 4)*np.finfo(float).eps
        bound = rho/(1-rho)*absolute_sum
        assert np.all(np.abs(decomposition) <= bound)
    arrays["normalized_error"] = np.array([float(row["normalized_error"]) for row in rows])
    arrays["thresholds"] = np.array([float(x) for x in LIMITS])
    np.savez_compressed(args.output / "arrays.npz", **arrays)
    with (args.output / "force_components.csv").open("w", newline="", encoding="utf-8") as stream:
        table = csv.writer(stream)
        table.writerow(["dof", "node", "axis", "component", "candidate_N", "HP80_N_decimal", "difference_N_decimal"])
        for name in COMPONENTS:
            for i, (a, ref) in enumerate(zip(forces[name], reference[name])):
                with localcontext() as context:
                    context.prec = 120
                    table.writerow([i, i//2, "xy"[i%2], name, format(a, ".17g"), str(ref),
                                    str(Decimal.from_float(float(a))-ref)])
    sources = [Path(kernel.__file__), Path(kernel.ci.__file__),
               Path(__file__), Path(kernel.__file__).with_name("compensated_kinematics.py")]
    (args.output / "sources").mkdir()
    for path in sources:
        shutil.copyfile(path, args.output / "sources" / path.name)
    summary = dict(case=original["case"], status="pass" if all(row["pass_gate"] for row in rows) else "fail",
                   kernel_version=kernel.KERNEL_VERSION, entry="assemble_split_numpy",
                   nodes=len(model.coordinates), elements=model.ne, dofs=model.ndof,
                   comparisons=rows, min_J=float(np.min(fields["J"])),
                   small_branch_points=int(np.count_nonzero(fields["small_branch"])),
                   quadrature_points=int(fields["J"].size), arithmetic_supported=True,
                   decomposition_rounding_bound_pass=True, decomposition_max_abs_N=float(np.max(np.abs(decomposition))),
                   force_seconds=force_seconds, total_seconds=perf_counter()-begin,
                   numpy_version=np.__version__, python_version=sys.version,
                   compiled_force_executed=False, tangent_executed=False, equilibrium_solved=False,
                   reference_regenerated=False, input_source=args.input.as_posix(),
                   inputs=bindings, sources=[dict(name=p.name, sha256=sha(p)) for p in sources])
    write(args.output / "summary.json", summary)
    print(json.dumps(dict(case=summary["case"], status=summary["status"], force_seconds=force_seconds,
                          errors=arrays["normalized_error"].tolist()), ensure_ascii=False))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
