"""Complete NumPy force assembly at one saved C1 compression state.

Copies the small model/state and extracts the existing Decimal reference from
the original audit. It does not regenerate a reference or solve equilibrium.
"""
import argparse
from decimal import Decimal, localcontext
from pathlib import Path
import shutil
from time import perf_counter

import numpy as np

from run_numpy_force_comparison import (
    COMPONENTS, FIELDS, HP_FIELDS, LIMITS, compare, kernel, load_npz, norm,
    read, sha, write, TMCModel, SplitDisplacement,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="TMC_h025_uniform_r2 source directory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    inputs = args.output / "inputs"
    inputs.mkdir()
    stage = args.input / "stages/uniform_tmc"
    bindings = []
    for source, name in ((stage / "model.npz", "model.npz"),
                         (stage / "steps/state_014.npz", "state.npz"),
                         (stage / "metadata.json", "metadata.json")):
        shutil.copyfile(source, inputs / name)
        bindings.append(dict(name=name, source=source.as_posix(), sha256=sha(source), bytes=source.stat().st_size))
    audit_path = args.input / "audit.json"
    audit = read(audit_path)
    last = audit["states"][-1]
    assert last["state_id"] == "uniform_tmc:14" and last["parameter_s"] == .5
    write(inputs / "reference.json", dict(state_id=last["state_id"], parameter_s=last["parameter_s"],
          precision_evidence_decimal=last["precision_evidence_decimal"],
          original_force_scale=last["measurements"]["force_scale"],
          normal_force_N_decimal=last["measurements"]["normal_force"],
          original_audit_sha256=sha(audit_path)))
    fixture, saved = load_npz(inputs / "model.npz"), load_npz(inputs / "state.npz")
    reference = read(inputs / "reference.json")
    metadata = read(inputs / "metadata.json")
    h = metadata["h"]
    model = TMCModel(fixture["coordinates"], fixture["connectivity"], fixture["lam"],
                     fixture["mu"], float(fixture["kr"]), h, h, 1., fixture["solid"], fixture["fixed_dofs"])
    for key in ("grad", "hessian", "weights"):
        assert np.array_equal(model.ops[key], fixture[key])
    state = SplitDisplacement(saved["u_lift"], saved["u_fluctuation"])
    begin = perf_counter()
    matrix, internal, fields = kernel.assemble_split_numpy(model, state)
    seconds = perf_counter()-begin
    assert matrix is None
    forces = {name: np.bincount(model.edofs.ravel(), weights=fields[key].ravel(), minlength=model.ndof)
              for name, key in zip(COMPONENTS, FIELDS)}
    np.testing.assert_array_equal(internal, forces["total_force"])
    arrays = dict(coordinates=model.coordinates, connectivity=model.connectivity,
                  u_lift=state.lift, u_fluctuation=state.fluctuation, **forces,
                  **{k: v for k, v in fields.items() if k != "timing_seconds"})
    comparisons = []
    with localcontext() as context:
        context.prec = 120
        sf = Decimal(reference["original_force_scale"])
        hp = reference["precision_evidence_decimal"]
        for name, key, limit, old_key in zip(COMPONENTS, HP_FIELDS, LIMITS,
                                            ("internal_force", "material_internal_force", "regularization_internal_force")):
            ref = [Decimal(x) for x in hp["80"][key]]
            assert len(ref) == model.ndof
            scale = sf if name == "total_force" else max(norm(ref), Decimal("1e-12")*sf)
            agreement = norm([a-Decimal(b) for a, b in zip(ref, hp["120"][key])])/scale
            assert agreement <= Decimal("1e-40")
            error, difference = compare(forces[name], ref, scale)
            old_error, _ = compare(saved[old_key], ref, scale)
            comparisons.append(dict(component=name, scale_N=scale, threshold=limit, normalized_error=error,
                                    old_stable_F_normalized_error=old_error, hp80_hp120_agreement=agreement,
                                    pass_gate=error <= limit))
            arrays["reference_"+name] = np.array([float(x) for x in ref])
            arrays["difference_"+name] = np.array([float(x) for x in difference])
    magnitudes = sum(np.abs(fields[key]) for key in FIELDS)
    absolute_sum = np.bincount(model.edofs.ravel(), weights=magnitudes.ravel(), minlength=model.ndof)
    count = np.bincount(model.edofs.ravel(), minlength=model.ndof)
    rho = (count+4)*np.finfo(float).eps
    decomposition = internal-forces["material_force"]-forces["regularization_force"]
    assert np.all(np.abs(decomposition) <= rho/(1-rho)*absolute_sum)
    arrays["normalized_error"] = np.array([float(r["normalized_error"]) for r in comparisons])
    arrays["thresholds"] = np.array([float(x) for x in LIMITS])
    np.savez_compressed(args.output / "arrays.npz", **arrays)
    normal = -float(fixture["group_top"] @ internal)
    summary = dict(status="pass" if all(r["pass_gate"] for r in comparisons) else "fail",
                   case="C1_TMC_h025_uniform_r2_state_014", entry="assemble_split_numpy",
                   elements=model.ne, dofs=model.ndof, comparisons=comparisons,
                   force_and_assembly_seconds=seconds, min_J=float(fields["J"].min()),
                   normal_force_N=normal, HP80_normal_force_N_decimal=reference["normal_force_N_decimal"],
                   normal_force_semantics="minus full top constraint reaction, includes background medium",
                   decomposition_rounding_bound_pass=True, inputs=bindings,
                   original_audit_sha256=reference["original_audit_sha256"],
                   equilibrium_solved=False, tangent_executed=False, reference_regenerated=False)
    sources = [Path(kernel.__file__), Path(kernel.ci.__file__), Path(__file__),
               Path(__file__).with_name("run_numpy_force_comparison.py"),
               Path(kernel.__file__).with_name("compensated_kinematics.py")]
    (args.output / "sources").mkdir()
    for source in sources:
        shutil.copyfile(source, args.output / "sources" / source.name)
    summary["sources"] = [dict(name=p.name, sha256=sha(p)) for p in sources]
    write(args.output / "summary.json", summary)
    print("C1", summary["status"], "errors", arrays["normalized_error"], "normal force [N]", normal, "seconds", seconds)
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
