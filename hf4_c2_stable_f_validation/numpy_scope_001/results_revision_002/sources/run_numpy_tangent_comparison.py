"""Compare NumPy mechanical tangents with saved HP80/120 actions.

Lift stays fixed and the saved directions perturb fluctuation. The references
are read and copied, never recomputed. One invocation covers both directions
of three near-rotation cases and the existing C1 terminal direction. A failed
scientific gate stops later cases and preserves the completed output.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter

import numpy as np
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval.split_numpy_tangent import batch_tangent_components_split_numpy
from hf_eval.tmc import TMCModel

CASES = ("unit__near_rotation", "dyadic_rect__near_rotation", "nondyadic_rect__near_rotation")
COMPONENTS = ("total_tangent", "material_tangent", "regularization_tangent")
HP_KEYS = ("tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")
LIMITS = (Decimal("1e-10"), Decimal("1e-9"), Decimal("1e-9"))


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False,
                               default=str) + "\n", encoding="utf-8")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def norm(vector):
    return sum((x*x for x in vector), Decimal(0)).sqrt()


def copy_input(source, target, expected=None):
    digest = sha(source)
    if expected is not None and digest != expected:
        raise ValueError("Input identity differs: " + source.as_posix())
    shutil.copyfile(source, target)
    assert sha(target) == digest
    return dict(name=target.name, source=source.as_posix(), bytes=source.stat().st_size,
                sha256=digest)


def make_model(fixture, metadata=None):
    metadata = metadata or {}
    model = TMCModel(fixture["coordinates"], fixture["connectivity"], fixture["lam"],
                     fixture["mu"], float(fixture["kr"]),
                     float(fixture.get("hx", metadata.get("h", 0))),
                     float(fixture.get("hy", metadata.get("h", 0))),
                     float(fixture.get("thickness", 1.)), fixture["solid"], fixture["fixed_dofs"])
    for key in ("grad", "hessian", "weights"):
        assert np.array_equal(model.ops[key], fixture[key])
    return model


def compare_actions(model, lift, fluctuation, directions, references, output,
                    *, baseline_actions=None):
    started = perf_counter()
    fields = batch_tangent_components_split_numpy(lift[model.edofs], fluctuation[model.edofs],
                                                  model.ops, model.lam, model.mu, model.kr)
    tangent_seconds = perf_counter() - started
    for name in COMPONENTS:
        assert fields[name].shape == (model.ne, 8, 8)
        assert fields[name].dtype == np.dtype("float64") and np.isfinite(fields[name]).all()
    matrix = sparse.coo_matrix((fields["total_tangent"].ravel(), (model._rows, model._cols)),
                              shape=(model.ndof, model.ndof)).tocsc()
    matrix.sum_duplicates()
    sparse.save_npz(output / "total_matrix.npz", matrix)
    arrays = dict(edofs=model.edofs, coordinates=model.coordinates, connectivity=model.connectivity,
                  u_lift=lift, u_fluctuation=fluctuation, **{name: fields[name] for name in COMPONENTS})
    comparisons = []
    with localcontext() as context:
        context.prec = 120
        for direction_index, (direction, hp) in enumerate(zip(directions, references, strict=True)):
            assert direction.shape == (model.ndof,) and np.isfinite(direction).all()
            assert not np.any(direction[model.fixed_dofs])
            arrays[f"direction_{direction_index}"] = direction
            actions = {}
            for name, key, limit in zip(COMPONENTS, HP_KEYS, LIMITS, strict=True):
                local = np.einsum("eij,ej->ei", fields[name], direction[model.edofs])
                action = np.bincount(model.edofs.ravel(), weights=local.ravel(), minlength=model.ndof)
                ref = [Decimal(x) for x in hp["80"][key]]
                other = [Decimal(x) for x in hp["120"][key]]
                assert len(ref) == len(other) == model.ndof
                denominator = max(norm(ref), Decimal("1e-10"))
                agreement = norm([a-b for a, b in zip(ref, other, strict=True)]) / denominator
                assert agreement <= Decimal("1e-40")
                differences = [Decimal.from_float(float(a))-b for a, b in zip(action, ref, strict=True)]
                error = norm(differences) / denominator
                row = dict(direction=direction_index, component=name, denominator_N_per_mm=denominator,
                           threshold=limit, normalized_error=error,
                           hp80_hp120_normalized_agreement=agreement, pass_gate=error <= limit)
                if baseline_actions is not None:
                    old = baseline_actions[name]
                    row["old_saved_normalized_error"] = norm([
                        Decimal.from_float(float(a))-b for a, b in zip(old, ref, strict=True)]) / denominator
                comparisons.append(row)
                arrays[f"direction_{direction_index}_{name}_action"] = action
                arrays[f"direction_{direction_index}_{name}_reference"] = np.array([float(x) for x in ref])
                arrays[f"direction_{direction_index}_{name}_difference"] = np.array([float(x) for x in differences])
                actions[name] = action
            np.testing.assert_allclose(matrix @ direction, actions["total_tangent"], rtol=2e-14, atol=1e-14)
    np.savez_compressed(output / "arrays.npz", **arrays)
    return dict(status="pass" if all(row["pass_gate"] for row in comparisons) else "fail",
                elements=model.ne, dofs=model.ndof, directions=len(directions), comparisons=comparisons,
                tangent_seconds=tangent_seconds,
                matrix_relative_asymmetry=float(np.linalg.norm((matrix-matrix.T).data) /
                                                max(np.linalg.norm(matrix.data), np.finfo(float).tiny)),
                lift_fixed=True, tangent_semantics="mechanical residual Jacobian, unsymmetrized",
                reference_regenerated=False, compiled_force_executed=False, equilibrium_solved=False)


def near_rotation_case(case, force_root, original_root, original_index, output):
    output.mkdir()
    inputs = output / "inputs"
    inputs.mkdir()
    source = force_root / case / "inputs"
    original_summary = read(force_root / case / "summary.json")
    bound = {row["name"]: row["sha256"] for row in original_summary["inputs"]}
    bindings = [copy_input(source / name, inputs / name, bound[name])
                for name in ("inputs.npz", "input_freeze.json", "hp_0.json", "result.json")]
    hp1_relative = case + "/hp_1.json"
    bindings.append(copy_input(original_root / hp1_relative, inputs / "hp_1.json",
                               original_index[hp1_relative]))
    fixture = load_npz(inputs / "inputs.npz")
    freeze, old = read(inputs / "input_freeze.json"), read(inputs / "result.json")
    assert freeze["input_sha256"] == sha(inputs / "inputs.npz")
    assert freeze["physical_authority"] == "exact D(lift)+D(fluctuation)"
    for direction in (0, 1):
        checks = {row["name"]: row for row in old["directions"][direction]["checks"]}
        for name, limit in zip(COMPONENTS, LIMITS, strict=True):
            assert Decimal(checks["candidate_" + name]["limit"]) == limit
    model = make_model(fixture)
    summary = compare_actions(model, fixture["u_lift"], fixture["u_fluctuation"],
                              [fixture[f"direction_{i}"] for i in (0, 1)],
                              [read(inputs / f"hp_{i}.json") for i in (0, 1)], output)
    summary.update(case=case, inputs=bindings)
    write(output / "summary.json", summary)
    return summary


def c1_case(force_root, output):
    output.mkdir()
    inputs = output / "inputs"
    inputs.mkdir()
    source = force_root / "c1_state_014" / "inputs"
    prior = read(force_root / "c1_state_014" / "summary.json")
    bound = {row["name"]: row["sha256"] for row in prior["inputs"]}
    bindings = [copy_input(source / name, inputs / name, bound.get(name))
                for name in ("model.npz", "state.npz", "metadata.json", "reference.json")]
    fixture, state = load_npz(inputs / "model.npz"), load_npz(inputs / "state.npz")
    reference = read(inputs / "reference.json")
    assert reference["state_id"] == "uniform_tmc:14" and reference["parameter_s"] == .5
    assert reference["original_audit_sha256"] == prior["original_audit_sha256"]
    model = make_model(fixture, read(inputs / "metadata.json"))
    baseline = dict(zip(COMPONENTS, (state["production_tangent_action"],
                                   state["material_tangent_action"], state["regularization_tangent_action"])))
    summary = compare_actions(model, state["u_lift"], state["u_fluctuation"],
                              [state["tangent_direction"]], [reference["precision_evidence_decimal"]],
                              output, baseline_actions=baseline)
    summary.update(case="C1_TMC_h025_uniform_r2_state_014", inputs=bindings,
                   original_audit_sha256=reference["original_audit_sha256"])
    write(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-input", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True, help="Bound manufactured_001/results")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    begin = perf_counter()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = args.output / "sources"
    sources.mkdir()
    source_paths = [Path(__file__), Path(sys.modules[batch_tangent_components_split_numpy.__module__].__file__)]
    source_bindings = [copy_input(path, sources / path.name) for path in source_paths]
    original_index = read(args.original / "output_sha256.json")
    shutil.copyfile(args.original / "output_sha256.json", args.output / "original_output_sha256.json")
    records = []
    for case in (*CASES, "c1_state_014"):
        row = (c1_case(args.force_input, args.output / case) if case == "c1_state_014" else
               near_rotation_case(case, args.force_input, args.original, original_index, args.output / case))
        records.append(row)
        summary = dict(status="pass" if all(r["status"] == "pass" for r in records) else "fail",
                       completed_cases=len(records), planned_cases=4,
                       completed_directions=sum(r["directions"] for r in records), planned_directions=7,
                       total_seconds=perf_counter()-begin, python_version=sys.version,
                       numpy_version=np.__version__, reference_regenerated=False, compiled_force_executed=False,
                       equilibrium_solved=False, original_index_sha256=sha(args.original / "output_sha256.json"),
                       sources=source_bindings, cases=records)
        write(args.output / "summary.json", summary)
        print(json.dumps(dict(case=row["case"], status=row["status"], tangent_seconds=row["tangent_seconds"],
                              errors=[float(r["normalized_error"]) for r in row["comparisons"]])), flush=True)
        if row["status"] != "pass":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
