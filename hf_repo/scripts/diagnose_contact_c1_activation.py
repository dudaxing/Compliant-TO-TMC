"""Read-only HP experiment on the failed C1 constraint activation handoff."""
from pathlib import Path
from decimal import Decimal, localcontext
import argparse
import numpy as np
from hf4_common import read_json, read_npz, sha, write_json
from hf4_split_precision_reference import evaluate_split_prescribed_state


def diagnose(run, output):
    run, output = Path(run).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError("never overwrite a diagnostic")
    stage = run / "stages/uniform_precontact"
    entry = read_json(stage / "steps/index.json")["steps"][-1]
    path = stage / "steps" / entry["file"]
    if entry["d"] != .25 or sha(path) != entry["sha256"]:
        raise ValueError("requires the stored closure endpoint")
    model, state = read_npz(stage / "model.npz"), read_npz(path)
    top_dofs = 2 * model["top_nodes"] + 1
    new_fixed = np.setdiff1d(top_dofs, model["fixed_dofs"])
    projected = state["u_fluctuation"].copy()
    projected[new_fixed] = 0.
    groups = {k[6:]: v for k, v in model.items() if k.startswith("group_") and np.any(v)}
    closed = dict(model)
    closed["fixed_dofs"] = np.union1d(model["fixed_dofs"], top_dofs)
    base, direction = np.zeros_like(model["base"]), np.zeros_like(model["direction"])
    base[closed["fixed_dofs"]] = state["u_lift"][closed["fixed_dofs"]]
    direction[2 * model["bottom_nodes"] + 1] = 1.
    top_group = np.zeros_like(base)
    top_group[top_dofs] = 1.
    closed_groups = {**groups, "top": top_group}
    cases = []
    for name, fixture, w, parameter, b, dr, gs in (
        ("source_free_top", model, state["u_fluctuation"], .25, model["base"], model["direction"], groups),
        ("new_constraints_unprojected", closed, state["u_fluctuation"], 0., base, direction, closed_groups),
        ("new_constraints_explicit_projection", closed, projected, 0., base, direction, closed_groups),
    ):
        checks = {}
        for precision in (50, 80):
            hp = evaluate_split_prescribed_state(fixture, state["u_lift"], w, parameter, b, dr, gs,
                                                   force_scale_per_length=100., precision=precision)
            checks[str(precision)] = {k: hp[k] for k in (
                "relative_residual_decimal", "relative_constraint_decimal", "minimum_J_decimal",
                "force_scale_decimal", "free_residual_norm_decimal", "internal_decimal")}
        cases.append(dict(case=name, precision_checks=checks))
    with localcontext() as ctx:
        ctx.prec = 100
        force_a = cases[1]["precision_checks"]["80"]["internal_decimal"]
        force_b = cases[2]["precision_checks"]["80"]["internal_decimal"]
        force_change = sum(((x-y)**2 for x, y in zip(force_a, force_b)), Decimal(0)).sqrt()
    unchanged = np.setdiff1d(np.arange(len(projected)), new_fixed)
    receipt = dict(schema="contact_c1_activation_diagnostic_v1", source_run=run.name,
        source_state_sha256=sha(path), source_model_sha256=sha(stage / "model.npz"),
        diagnostic_source_sha256=sha(__file__), new_fixed_dofs=new_fixed,
        source_new_fixed_fluctuation=state["u_fluctuation"][new_fixed],
        maximum_projection_mm=float(np.max(np.abs(projected-state["u_fluctuation"]))),
        unaffected_fluctuation_bitwise_equal=bool(np.array_equal(projected[unchanged].view(np.uint64),
                                                  state["u_fluctuation"][unchanged].view(np.uint64))),
        lift_unchanged=True, force_change_norm_N=force_change, cases=cases,
        scope="fixed-state HP diagnosis only; does not accept a path or modify the source state")
    write_json(output, receipt)
    print({"maximum_projection_mm": receipt["maximum_projection_mm"],
           "force_change_N": str(force_change),
           "projected_hp80_residual": str(cases[-1]["precision_checks"]["80"]["relative_residual_decimal"])})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    diagnose(args.run, args.output)
