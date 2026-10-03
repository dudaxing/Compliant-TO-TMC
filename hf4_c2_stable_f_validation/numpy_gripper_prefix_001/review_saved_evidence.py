"""Replay the saved canonical-prefix audit without new mechanics evaluation.

Independent equation arithmetic uses saved HP decimal strings and binary64
primitive arrays; no author audit-measurement or candidate helper is imported.
The only HF call is build_project, a geometry/task mapping with no assembly.
"""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PREFIX = [0., .001, .025]
NAMES = ("total_force", "material_force", "regularization_force", "total_tangent",
         "material_tangent", "regularization_tangent")
HP_KEYS = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal",
           "tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")
CANONICAL = {
    "geometry.json": "1aad84d50119d5d3c4d2b75c782d6b5d1466895e7df7b4496fde1e61adb7355f",
    "geometry.npz": "f7b23e8d16aedb0ebb5b7dc3954b7b59a80f99b6d3859046aa16904a610d6282",
    "task.json": "0a5d9d1ba3a64d1a715f1b05128da8f2047ad69b82ed9d527aae18f9a693c38b",
    "validation_spec.json": "44eb35fef2e6988bf66c3935b76559531e40f0f567bd5438fe7db2afb7bd583e",
}
GATES = dict(production_residual="1e-9", independent_residual="1e-8", force_evaluation="1e-9",
    average_constraint="1e-10", global_force_balance="1e-6", fixed_displacement_mm="8e-11",
    hp80_hp120="1e-40", total_force="1e-11", material_force="1e-9", regularization_force="1e-9",
    total_tangent="1e-10", material_tangent="1e-9", regularization_tangent="1e-9",
    augmented_force_tangent="1e-10", augmented_constraint_tangent="1e-10")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    with np.load(path, allow_pickle=False) as saved:
        return {key: saved[key].copy() for key in saved.files}


def D(value):
    return Decimal.from_float(float(value))


def decimals(value):
    return [decimals(x) for x in value] if isinstance(value, list) else Decimal(value)


def norm(vector):
    return sum((x*x for x in vector), Decimal(0)).sqrt()


def digest_state(state):
    digest = hashlib.sha256(b"split_displacement_v1")
    digest.update(np.asarray([len(state["u_lift"])], dtype="<i8").tobytes())
    for key in ("u_lift", "u_fluctuation"):
        digest.update(np.asarray(state[key], dtype="<f8").tobytes())
    return digest.hexdigest()


def bits_equal(left, right):
    left, right = np.asarray(left, dtype=np.float64), np.asarray(right, dtype=np.float64)
    return left.shape == right.shape and np.array_equal(left.view(np.uint64), right.view(np.uint64))


def exact_state(state, values, row):
    with localcontext() as context:
        context.prec = 3000
        u = [D(a)+D(b) for a, b in zip(state["u_lift"], state["u_fluctuation"])]
        bi, bo = [list(map(D, values[key])) for key in ("b_in", "b_out")]
        qi, qo = [sum((a*b for a, b in zip(port, u)), Decimal(0)) for port in (bi, bo)]
        target = D(row["target_origin"])+D(row["d"])
        return u, bi, bo, qi, qo, target, qi-target


def equation(hp, state, values, row):
    u, bi, bo, qi, qo, target, error = exact_state(state, values, row)
    with localcontext() as context:
        context.prec = 120
        fi = hp["internal_decimal"]
        actuator = [b*D(row["R_input"]) for b in bi]
        spring = [D(values["k_out"])*b*qo for b in bo]
        r = [a+b-c for a, b, c in zip(fi, spring, actuator)]
        fixed = set(map(int, values["fixed_dofs"]))
        free = [i for i in range(len(u)) if i not in fixed]
        ds = max(abs(target), Decimal("1e-6"))
        floor = Decimal("1e-8")*D(values["force_scale_per_length"])*ds
        sf = max(*[norm([x[i] for i in free]) for x in (fi, actuator, spring)], floor)
        support = [r[i] if i in fixed else Decimal(0) for i in range(len(u))]
        balance = [sum((support[i]+actuator[i]-spring[i] for i in range(j, len(u), 2)),
                       Decimal(0)) for j in (0, 1)]
        bs = max(norm(support)+norm(actuator)+norm(spring), sf)
        v = list(map(D, values["tangent_direction"]))
        dq = sum((b*x for b, x in zip(bo, v)), Decimal(0))
        dg = sum((b*x for b, x in zip(bi, v)), Decimal(0))
        action = [a+D(values["k_out"])*b*dq-c*D(values["tangent_multiplier_direction"])
                  for a, b, c in zip(hp["tangent_action_decimal"], bo, bi)]
        return dict(q_in=qi, q_out=qo, physical_mean_target_mm=target, constraint_residual=error,
                    force_scale=sf, force_scale_floor=floor, displacement_scale=ds,
                    relative_residual=norm([r[i] for i in free])/sf,
                    relative_constraint=abs(error)/ds, relative_force_balance=norm(balance)/bs,
                    fixed_error_mm=max(abs(u[i]) for i in fixed),
                    min_J=min(x for cell in hp["J_decimal"] for x in cell),
                    support=support, actuator=actuator, spring_force=[-x for x in spring],
                    force_residual=r, balance=balance, balance_scale=bs,
                    augmented_force=action, augmented_constraint=dg, free=free)


def saved_equation(state, values, row):
    u, _, _, _, _, target, error = exact_state(state, values, row)
    with localcontext() as context:
        context.prec = 120
        fi, actuator, spring = [list(map(D, state[key])) for key in
                               ("internal_force", "input_force", "spring_force_on_structure")]
        support = list(map(D, state["support_reaction"]))
        r = [a-b-c for a, b, c in zip(fi, actuator, spring)]
        fixed = set(map(int, values["fixed_dofs"]))
        free = [i for i in range(len(u)) if i not in fixed]
        ds = max(abs(target), Decimal("1e-6"))
        sf = max(*[norm([x[i] for i in free]) for x in (fi, actuator, spring)],
                 Decimal("1e-8")*D(values["force_scale_per_length"])*ds)
        balance = [sum((support[i]+actuator[i]+spring[i] for i in range(j, len(u), 2)),
                       Decimal(0)) for j in (0, 1)]
        bs = max(norm(support)+norm(actuator)+norm(spring), sf)
        return dict(relative_residual=norm([r[i] for i in free])/sf, residual_scale=sf,
                    relative_constraint=abs(error)/ds, relative_force_balance=norm(balance)/bs,
                    force_residual=r, balance=balance, balance_scale=bs)


def verify_fields(calculated, saved, label):
    for key, value in calculated.items():
        assert (saved[key] == value if key == "free" else decimals(saved[key]) == value), (label, key)


def verify_model(solve, values, protocol):
    """Rebuild only original ordinary geometry/task mapping, never mechanics."""
    for name, expected in CANONICAL.items():
        assert sha(solve/"inputs"/name) == expected, name
    task = read(solve/"inputs/task.json")
    assert task["case_family"] == protocol["case_family"] == "gripper"
    assert task["input"]["target_mm"] == protocol["parent_task_target_mm"] == 1.
    assert task["material"]["E_MPa"] == 1. and task["workpiece"] is None
    assert task["output"]["spring_N_per_mm"] == float(values["k_out"]) == 0.
    assert float(values["force_scale_per_length"]) == float(values["thickness"]) == 20.
    specification = read(solve/"inputs/validation_spec.json")
    mapping = dict(tolerance="internal_relative_force_tolerance", constraint_tolerance="constraint_relative_tolerance",
        displacement_scale_floor="displacement_scale_floor_mm", force_scale_floor_factor="force_scale_floor_factor",
        max_checks="max_checks", max_backtracks="max_backtracks", max_bisections="max_bisections", armijo_c="armijo_c")
    for key, original in mapping.items():
        assert protocol["settings"][key] == specification[original]
    assert protocol["settings"]["minimum_increment"] == .001/16
    assert protocol["minimum_increment_rule"] == specification["minimum_increment_rule"] == "initial target increment / 16"
    sys.path.insert(0, str(REPO/"hf_repo/src"))
    from hf_eval.project import build_project
    project = build_project(solve/"inputs/geometry.json", task)
    assert (project.model.ne, project.model.ndof, len(project.model.fixed_dofs)) == (3200, 6642, 87)
    for name in ("coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy", "thickness", "solid", "fixed_dofs"):
        np.testing.assert_array_equal(values[name], getattr(project.model, name))
    for name in ("grad", "hessian", "weights"):
        np.testing.assert_array_equal(values[name], project.model.ops[name])
    np.testing.assert_array_equal(values["b_in"], project.bin)
    np.testing.assert_array_equal(values["b_out"], project.bout)
    assert project.geometry.geometry_id == protocol["geometry_id"]
    assert project.task_hash == protocol["task_sha256"]
    expected_shape = np.zeros(project.model.ndof)
    expected_shape[np.flatnonzero(project.bin)] = 1.
    assert bits_equal(values["lift_shape"], expected_shape)
    return project.model.free


def replay(receipt):
    solve, audit = ROOT/"solve", ROOT/"audit"
    protocol, summary, audited = [read(path) for path in
        (solve/"protocol.json", solve/"summary.json", audit/"summary.json")]
    assert protocol["schema_version"] == summary["schema_version"] == "split-project-prefix-1.0"
    assert protocol["case_family"] == summary["case_family"] == audited["case_family"] == "gripper"
    assert protocol["gates"] == audited["gates"] == GATES
    assert summary["status"] == "success" and summary["target_reached"]
    assert not summary["parent_task_complete"]
    assert audited["status"] == "pass" and audited["new_state_independent_HP_audited"]
    rows = summary["states"]
    assert [row["d"] for row in rows if row["is_original_target"]] == PREFIX
    assert len(rows) == len(audited["states"]) and audited["fresh_HP_evaluations"] == 2*len(rows)
    assert all(a["d"] < b["d"] for a, b in zip(rows, rows[1:]))
    assert sha(solve/"model.npz") == protocol["model_sha256"] == summary["model_sha256"]
    assert sha(solve/"protocol.json") == summary["protocol_sha256"]
    values = load(solve/"model.npz")
    free = verify_model(solve, values, protocol)
    for binding in audited["input_bindings"]:
        assert sha(solve/binding["path"]) == binding["sha256"], binding["path"]
    source_count = 0
    for directory, records in ((solve, protocol["sources"]), (audit, audited["sources"])):
        for binding in records:
            name = binding["name"]
            scripts = REPO/"hf_repo/scripts"/name
            current = scripts if scripts.exists() else REPO/"hf_repo/src/hf_eval"/name
            assert sha(directory/"sources"/name) == sha(current) == binding["sha256"], name
            source_count += 1
    receipts, count = [], 0
    for index, (row, record) in enumerate(zip(rows, audited["states"])):
        assert record["index"] == index and record["d_mm"] == row["d"] and record["status"] == "pass"
        assert row["target_origin"] == 0. and row["physical_mean_target_mm"] == row["d"]
        assert sha(solve/row["path"]) == row["file_sha256"]
        state = load(solve/row["path"])
        assert digest_state(state) == row["state_sha256"] == record["state_sha256"]
        expected_lift = np.zeros(len(values["b_in"])) if row["d"] == 0. else row["d"]*values["lift_shape"]
        assert bits_equal(state["u_lift"], expected_lift)
        assert np.all(state["u_fluctuation"][values["fixed_dofs"]] == 0.)
        assert all(np.isfinite(x).all() for x in state.values()) and np.all(state["J"] > 0.)
        u, _, _, qi, qo, _, constraint = exact_state(state, values, row)
        assert float(qi) == row["q_in"] and float(qo) == row["q_out"]
        assert float(constraint) == row["constraint_residual"]
        hp, measured = {}, {}
        for precision, binding in zip((80, 120), record["references"]):
            assert sha(audit/binding["path"]) == binding["sha256"]
            with gzip.open(audit/binding["path"], "rt", encoding="utf-8") as stream:
                saved = json.load(stream)
            hp[precision] = {key: decimals(saved["mechanics"][key]) for key in
                             (*HP_KEYS, "J_decimal", "physical_displacement_decimal")}
            assert hp[precision]["physical_displacement_decimal"] == u
            measured[precision] = equation(hp[precision], state, values, row)
            verify_fields(measured[precision], saved["task"], (index, precision, "task"))
        verify_fields(measured[80], record["metrics"], (index, "metrics"))
        exact_saved = saved_equation(state, values, row)
        verify_fields(exact_saved, record["saved_equation_metrics"], (index, "saved_equation"))
        vector_binding = record["candidate_vectors"]
        assert sha(audit/vector_binding["path"]) == vector_binding["sha256"]
        candidate = load(audit/vector_binding["path"])
        for name, key in zip(NAMES[:3], ("internal_force", "material_internal_force", "regularization_internal_force")):
            assert bits_equal(candidate[name], state[key])
        assert bits_equal(candidate["tangent_direction"], values["tangent_direction"])
        assert bits_equal(candidate["tangent_multiplier_direction"], values["tangent_multiplier_direction"])
        for binding in record["matrices"]:
            assert sha(audit/binding["path"]) == binding["sha256"]
        total, augmented = [sparse.load_npz(audit/binding["path"]) for binding in record["matrices"]]
        bi, bo, v = [values[key] for key in ("b_in", "b_out", "tangent_direction")]
        assert bits_equal(total@v, candidate["total_tangent"])
        output_column = sparse.csc_matrix(bo[:, None])
        expected_free = (total+float(values["k_out"])*(output_column@output_column.T))[free][:, free]
        column = sparse.csc_matrix(bi[free, None])
        expected_augmented = sparse.bmat([[expected_free, -column], [column.T, None]], format="csc")
        difference = augmented-expected_augmented
        assert difference.nnz == 0 or np.all(difference.data == 0.)
        action = augmented@np.r_[v[free], float(values["tangent_multiplier_direction"])]
        assert bits_equal(action[:-1], candidate["augmented_force_action"])
        assert bits_equal(np.array(action[-1]), candidate["augmented_constraint_action"])
        checks, gate_map = {}, {}
        with localcontext() as context:
            context.prec = 120
            sf = measured[80]["force_scale"]
            for name, key in zip(NAMES, HP_KEYS):
                reference = hp[80][key]
                denominator = sf if name == "total_force" else max(norm(reference),
                    Decimal("1e-12")*sf if "force" in name else Decimal("1e-10"))
                checks[name] = norm([D(a)-b for a, b in zip(candidate[name], reference)])/denominator
                gate_map[name] = name
                checks[name+"__hp80_hp120"] = norm([a-b for a, b in zip(hp[80][key], hp[120][key])])/denominator
                gate_map[name+"__hp80_hp120"] = "hp80_hp120"
            checks["force_evaluation"] = norm([D(a)-b for a, b in zip(state["internal_force"], hp[80]["internal_decimal"])])/sf
            gate_map["force_evaluation"] = "force_evaluation"
            for key, target in (("input_force", "actuator"), ("spring_force_on_structure", "spring_force"), ("support_reaction", "support")):
                checks["saved_"+key] = norm([D(a)-b for a, b in zip(state[key], measured[80][target])])/sf
                gate_map["saved_"+key] = "force_evaluation"
            for key in ("q_in", "q_out"):
                checks["reported_"+key] = abs(D(row[key])-measured[80][key])/measured[80]["displacement_scale"]
                gate_map["reported_"+key] = "average_constraint"
            for precision in (80, 120):
                for key, gate in (("relative_residual", "independent_residual"), ("relative_constraint", "average_constraint"),
                                  ("relative_force_balance", "global_force_balance"), ("fixed_error_mm", "fixed_displacement_mm")):
                    name = f"hp{precision}__{key}"
                    checks[name], gate_map[name] = measured[precision][key], gate
                checks[f"hp{precision}__positive_J"] = measured[precision]["min_J"]
            for key, gate in (("relative_residual", "production_residual"), ("relative_constraint", "average_constraint"),
                              ("relative_force_balance", "global_force_balance")):
                checks["saved_equation__"+key], gate_map["saved_equation__"+key] = exact_saved[key], gate
            checks["reported_production_residual"] = Decimal(str(row["relative_residual"]))
            gate_map["reported_production_residual"] = "production_residual"
            checks["reported_residual_difference"] = abs(D(row["relative_residual"])-exact_saved["relative_residual"])
            gate_map["reported_residual_difference"] = "force_evaluation"
            checks["support_zero_on_free_dofs"] = bool(np.all(state["support_reaction"][free] == 0.))
            reference_action = [measured[80]["augmented_force"][i] for i in free]
            denominator = max(norm(reference_action), Decimal("1e-10"))
            checks["augmented_force_tangent"] = norm([D(a)-b for a, b in zip(action[:-1], reference_action)])/denominator
            gate_map["augmented_force_tangent"] = "augmented_force_tangent"
            checks["augmented_constraint_tangent"] = abs(D(action[-1])-measured[80]["augmented_constraint"])/max(abs(measured[80]["augmented_constraint"]), Decimal("1e-6"))
            gate_map["augmented_constraint_tangent"] = "augmented_constraint_tangent"
            checks["augmented_force_tangent__hp80_hp120"] = norm([measured[80]["augmented_force"][i]-measured[120]["augmented_force"][i] for i in free])/denominator
            gate_map["augmented_force_tangent__hp80_hp120"] = "hp80_hp120"
        assert set(checks) == {item["name"] for item in record["checks"]}
        for check in record["checks"]:
            name, value = check["name"], checks[check["name"]]
            assert check["pass_gate"]
            if isinstance(value, bool):
                assert value == check["pass_gate"]
            else:
                assert value == Decimal(check["value"]), (index, name, "Decimal value")
                if "positive_J" in name:
                    assert value.is_finite() and value > 0.
                else:
                    assert Decimal(check["limit"]) == Decimal(GATES[gate_map[name]])
                    assert value.is_finite() and value <= Decimal(check["limit"])
            count += 1
        residual = state["internal_force"]-state["spring_force_on_structure"]-state["input_force"]
        floor = 1e-8*20.*max(abs(row["d"]), 1e-6)
        sf_float = max(*[float(np.linalg.norm(state[key][free])) for key in
                         ("internal_force", "input_force", "spring_force_on_structure")], floor)
        assert sf_float == row["residual_scale"]
        assert float(np.linalg.norm(residual[free]))/sf_float == row["relative_residual"]
        receipts.append(dict(index=index, d_mm=row["d"], state_sha256=row["state_sha256"], checks_recomputed=len(checks),
            exact_split_physical_sum=True, lift_bitwise_equal=True, exact_mean_and_constraint_equal=True,
            total_CSC_direction_bitwise_equal=True, augmented_CSC_direction_bitwise_equal=True,
            augmented_KKT_equation_identity=True, production_float_residual_equal=True,
            force_scale_decimal=str(sf), all_reported_Decimal_values_equal=True))
    assert count == audited["checks_completed"]
    receipt.update(status="pass", all_saved_checks_recomputed=True, checks_completed=count, state_count=len(rows), states=receipts,
        original_targets_verified=PREFIX, parent_task_target_mm=1., parent_task_complete=False,
        canonical_model_rebuilt_without_assembly=True, input_bindings_verified=len(audited["input_bindings"]),
        source_bindings_verified=source_count, reference_hashes_verified=2*len(rows), sparse_matrix_hashes_verified=2*len(rows),
        candidate_vector_file_hashes_verified=len(rows), omitted_checks=0,
        force_kernel_calls=0, solver_calls=0, fresh_HP_calls=0,
        audit_summary_sha256=sha(audit/"summary.json"), solve_summary_sha256=sha(solve/"summary.json"))


def main():
    output = ROOT/"independent_review.json"
    history = []
    if output.exists():
        previous = read(output)
        if previous.get("status") == "pass":
            raise FileExistsError("Successful review is immutable")
        index = 1
        while (ROOT/f"independent_review_failed_{index:03d}.json").exists():
            index += 1
        archive = ROOT/f"independent_review_failed_{index:03d}.json"
        output.rename(archive)
        history.append(dict(path=archive.name, sha256=sha(archive)))
    receipt = dict(kind="independent_saved_arithmetic_replay", datetime_utc=datetime.now(timezone.utc).isoformat(),
        review_source_sha256=sha(Path(__file__)), prior_failed_reviews=history,
        scope="Saved canonical gripper prefix only; no new constitutive evaluation, Newton path or HP reference",
        arithmetic=dict(exact_split_and_port_products_decimal_digits=3000, declared_equation_decimal_digits=120,
                        saved_HP_authorities=[80, 120], force_scale_per_length_N_per_mm=20.))
    try:
        replay(receipt)
    except Exception as error:
        receipt.update(status="failed_review", failure_type=type(error).__name__, failure=str(error),
                       failed_review_source=Path(__file__).read_text(encoding="utf-8"))
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        raise
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "state_count", "checks_completed", "omitted_checks")}))


if __name__ == "__main__":
    main()
