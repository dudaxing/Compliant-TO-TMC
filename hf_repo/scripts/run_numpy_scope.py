"""Compare full NumPy forces and assembled CSC actions with existing HP80/120.

Reads the compact, identity-bound corpus produced by prepare_numpy_scope_inputs.
Lift stays fixed. References are reused; no JIT, HP evaluation or solve occurs.
A failed original gate stops subsequent cases and retains completed results.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import gzip
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter

import numpy as np
import psutil
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval import split_kernel_invariants_hu as force_kernel
from hf_eval.split_numpy_tangent import batch_tangent_components_split_numpy
from hf_eval.split_state import SplitDisplacement
from run_numpy_tangent_comparison import load_npz, make_model, norm, read, sha, write

COMPONENTS = ("total", "material", "regularization")
HP_FORCE = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal")
HP_TANGENT = ("tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")
LIMITS = dict(total_force="1e-11", material_force="1e-9", regularization_force="1e-9",
              total_tangent="1e-10", material_tangent="1e-9", regularization_tangent="1e-9")


def forbidden(*args, **kwargs):
    raise RuntimeError("Compiled force/runtime execution is outside NumPy scope")


def evaluate(row, inputs, output):
    fixture, state = (load_npz(inputs / row[key]) for key in ("model_file", "state_file"))
    with gzip.open(inputs / row["reference_file"], "rt", encoding="utf-8") as stream:
        reference = json.load(stream)
    model = make_model(fixture, row.get("metadata"))
    lift, fluctuation = state["u_lift"], state["u_fluctuation"]
    directions = ([state[f"direction_{i}"] for i in range(2)] if row["kind"] == "manufactured"
                  else [state["tangent_direction"]])
    if len(reference["directions"]) != len(directions):
        raise ValueError("Reference direction count differs: " + row["case"])
    start = perf_counter()
    _, internal, fields = force_kernel.assemble_split_numpy(model, SplitDisplacement(lift, fluctuation))
    forces = {component + "_force": np.bincount(model.edofs.ravel(), weights=fields[key].ravel(),
              minlength=model.ndof) for component, key in
              zip(COMPONENTS, ("residual", "material_residual", "regularization_residual"), strict=True)}
    np.testing.assert_array_equal(internal, forces["total_force"])
    tangent = batch_tangent_components_split_numpy(lift[model.edofs], fluctuation[model.edofs],
                                                   model.ops, model.lam, model.mu, model.kr)
    matrices = {}
    for component in COMPONENTS:
        name = component + "_tangent"
        matrix = sparse.coo_matrix((tangent[name].ravel(), (model._rows, model._cols)),
                                   shape=(model.ndof, model.ndof)).tocsc()
        matrix.sum_duplicates()
        if not np.isfinite(matrix.data).all():
            raise ValueError("Nonfinite CSC matrix: " + name)
        matrices[name] = matrix
    candidate_seconds = perf_counter() - start
    output.mkdir()
    sparse.save_npz(output / "total_matrix.npz", matrices["total_tangent"])
    arrays = dict(u_lift=lift, u_fluctuation=fluctuation, J=fields["J"], Hu=fields["Hu"],
                  small_branch=fields["small_branch"], **forces)
    checks = []
    with localcontext() as context:
        context.prec = 120
        for i, (direction, hp) in enumerate(zip(directions, reference["directions"], strict=True)):
            if direction.shape != (model.ndof,) or not np.isfinite(direction).all():
                raise ValueError("Invalid saved tangent direction")
            if np.any(direction[model.fixed_dofs]):
                raise ValueError("Saved direction changes a fixed DOF")
            arrays[f"direction_{i}"] = direction
            sf = Decimal(hp.get("force_scale", reference["force_scale"]))
            for quantity, keys in (("force", HP_FORCE), ("tangent", HP_TANGENT)):
                for component, key in zip(COMPONENTS, keys, strict=True):
                    name = component + "_" + quantity
                    actual = forces[name] if quantity == "force" else matrices[name] @ direction
                    ref, other = ([Decimal(x) for x in hp[p][key]] for p in ("hp80", "hp120"))
                    if len(ref) != len(other) or len(ref) != model.ndof:
                        raise ValueError("Reference vector size differs: " + name)
                    denominator = (sf if name == "total_force" else max(norm(ref),
                                   Decimal("1e-10") if quantity == "tangent" else Decimal("1e-12") * sf))
                    agreement = norm([a-b for a, b in zip(ref, other, strict=True)]) / denominator
                    difference = [Decimal.from_float(float(a))-b for a, b in zip(actual, ref, strict=True)]
                    error = norm(difference) / denominator
                    limit = Decimal(LIMITS[name])
                    checks.append(dict(direction=i, component=name, denominator=denominator,
                        normalized_error=error, limit=limit, hp80_hp120_error=agreement,
                        reference_limit="1e-40", pass_gate=error <= limit and agreement <= Decimal("1e-40")))
                    prefix = f"direction_{i}_" + name
                    arrays[prefix] = actual
                    arrays[prefix + "_difference"] = np.array([float(x) for x in difference])
    np.savez_compressed(output / "arrays.npz", **arrays)
    matrix = matrices["total_tangent"]
    result = dict(case=row["case"], kind=row["kind"], status="pass" if all(c["pass_gate"] for c in checks) else "fail",
                  elements=model.ne, dofs=model.ndof, directions=len(directions), comparisons=checks,
                  min_J=float(fields["J"].min()), candidate_seconds=candidate_seconds,
                  matrix_relative_asymmetry=float(np.linalg.norm((matrix-matrix.T).data) /
                       max(np.linalg.norm(matrix.data), np.finfo(float).tiny)),
                  original_status=row.get("original_status"), original_audit_status=row.get("original_audit_status"), input_identity=row,
                  historical_equilibrium_readmitted=False, reference_regenerated=False,
                  semantics="full DOF forces; fixed-lift unsymmetrized CSC mechanical Jacobian actions")
    write(output / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kind", choices=("all", "manufactured", "saved"), default="all")
    parser.add_argument("--max-seconds", type=float, default=600.)
    args = parser.parse_args()
    start = perf_counter()
    index = read(args.input / "index.json")
    # Verify the prepared closure before any candidate mechanics. This does not
    # substitute for the preparer's checks against the original frozen corpus.
    for path, binding in index["files"].items():
        if sha(args.input / path) != binding["sha256"]:
            raise ValueError("Prepared input identity differs: " + path)
    selected = [row for row in index["cases"] if args.kind == "all" or row["kind"] == args.kind]
    expected = 96 if args.kind == "all" else 33 if args.kind == "manufactured" else 63
    if len(selected) != expected or len({row["case"] for row in selected}) != expected:
        raise ValueError("Case inventory differs from the declared 33 + 63 scope")
    args.output.mkdir(parents=True, exist_ok=False)
    source_dir = args.output / "sources"
    source_dir.mkdir()
    sources = [Path(__file__), Path(__file__).with_name("run_numpy_tangent_comparison.py")]
    sources += [Path(force_kernel.__file__).with_name(name + ".py") for name in
                ("split_kernel_invariants_hu", "split_numpy_tangent", "compensated_invariants",
                 "compensated_kinematics", "split_kernel_compensated", "tmc_kernel", "tmc", "split_state")]
    for source in sources:
        shutil.copyfile(source, source_dir / source.name)
    for name in ("_runtime", "_batch_without_tangent", "_batch_with_tangent"):
        getattr(force_kernel, name)
        setattr(force_kernel, name, forbidden)
    rows, stopped = [], None
    process = psutil.Process()
    sampled_peak_rss = process.memory_info().rss
    try:
        for row in selected:
            sampled_peak_rss = max(sampled_peak_rss, process.memory_info().rss)
            if perf_counter() - start > args.max_seconds or sampled_peak_rss > 8 * 1024**3:
                raise RuntimeError("Between-case time or sampled RSS budget exceeded")
            result = evaluate(row, args.input, args.output / row["case"])
            rows.append(result)
            print(row["case"], result["status"], f"{result['candidate_seconds']:.3f}s", flush=True)
            if result["status"] != "pass":
                raise ValueError("Original numerical gate failed: " + row["case"])
            sampled_peak_rss = max(sampled_peak_rss, process.memory_info().rss)
            if perf_counter() - start > args.max_seconds or sampled_peak_rss > 8 * 1024**3:
                raise RuntimeError("Completed-case time or sampled RSS budget exceeded")
    except Exception as error:
        stopped = dict(case=row["case"], type=type(error).__name__, message=str(error))
    sampled_peak_rss = max(sampled_peak_rss, process.memory_info().rss)
    summary = dict(status="pass" if stopped is None and len(rows) == expected else "stopped",
                   kind=args.kind, cases=len(rows), expected_cases=expected,
                   directions=sum(r["directions"] for r in rows),
                   candidate_gates=sum(len(r["comparisons"]) for r in rows),
                   reference_gates=sum(len(r["comparisons"]) for r in rows),
                   cases_summary=[{k: r[k] for k in ("case", "kind", "status", "elements", "dofs", "min_J", "candidate_seconds")}
                                  for r in rows],
                   elapsed_seconds=perf_counter()-start, sampled_peak_rss_bytes=sampled_peak_rss,
                   budget_sampling="between cases and final observation, not a hard process supervisor",
                   stop=stopped, input_index_sha256=sha(args.input / "index.json"), original_limits=LIMITS,
                   sources=[dict(path=p.name, sha256=sha(p)) for p in sources],
                   compiled_runtime_guard_installed=True, reference_regenerated=False, equilibrium_solved=False)
    write(args.output / "summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("status", "cases", "directions", "candidate_gates", "elapsed_seconds", "stop")}))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
