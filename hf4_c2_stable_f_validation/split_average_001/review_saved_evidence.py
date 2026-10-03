"""Replay saved arithmetic and sparse identities without importing HF mechanics.

Only JSON/NPZ/gzip saved outputs are read. No force kernel, solver, reference
helper or JAX module is imported. Decimal calculations reuse saved HP strings,
not a new HP constitutive evaluation. Missing candidate component actions are
reported explicitly rather than inferred from a recorded error scalar.
"""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
NAMES = ("total_force", "material_force", "regularization_force", "total_tangent",
         "material_tangent", "regularization_tangent")
HP_KEYS = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal",
           "tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arrays(path):
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


def task_measure(hp, values, row, stiffness):
    u = hp["physical_displacement_decimal"]
    bi, bo = [list(map(D, values[key])) for key in ("b_in", "b_out")]
    with localcontext() as exact:
        exact.prec = 3000
        qi, qo = [sum((a*b for a, b in zip(port, u)), Decimal(0)) for port in (bi, bo)]
        target = D(row["target_origin"]) + D(row["d"])
        error = qi-target
    with localcontext() as context:
        context.prec = 120
        fi = hp["internal_decimal"]
        actuator = [b*D(row["R_input"]) for b in bi]
        spring = [D(stiffness)*b*qo for b in bo]
        r = [a+b-c for a, b, c in zip(fi, spring, actuator)]
        fixed = set(map(int, values["fixed_dofs"]))
        free = [i for i in range(len(u)) if i not in fixed]
        ds = max(abs(target), Decimal("1e-6"))
        sf = max(*[norm([x[i] for i in free]) for x in (fi, actuator, spring)],
                 Decimal("1e-8")*Decimal(100)*ds)
        support = [r[i] if i in fixed else Decimal(0) for i in range(len(u))]
        balance = [sum((support[i]+actuator[i]-spring[i] for i in range(j, len(u), 2)),
                       Decimal(0)) for j in (0, 1)]
        bs = max(norm(support)+norm(actuator)+norm(spring), sf)
        direction = list(map(D, values["tangent_direction"]))
        dq = sum((b*v for b, v in zip(bo, direction)), Decimal(0))
        dg = sum((b*v for b, v in zip(bi, direction)), Decimal(0))
        action = [a+D(stiffness)*b*dq-c*D(values["tangent_multiplier_direction"])
                  for a, b, c in zip(hp["tangent_action_decimal"], bo, bi)]
        return dict(q_in=qi, q_out=qo, force_scale=sf, displacement_scale=ds,
                    relative_residual=norm([r[i] for i in free])/sf,
                    relative_constraint=abs(error)/ds, relative_force_balance=norm(balance)/bs,
                    fixed_error_mm=max(abs(u[i]) for i in fixed),
                    min_J=min(x for cell in hp["J_decimal"] for x in cell),
                    support=support, spring_force=[-x for x in spring], actuator=actuator,
                    augmented_force=action, augmented_constraint=dg, free=free)


def run(receipt):
    solve, audit = ROOT/"solve", ROOT/"audit"
    protocol, solved, audited = [read(path) for path in
        (solve/"protocol.json", solve/"summary.json", audit/"summary.json")]
    assert solved["status"] == audited["status"] == "pass"
    assert solved["all_cases_completed"] and len(solved["cases"]) == 2
    assert audited["fresh_HP_evaluations"] == 16 and len(audited["states"]) == 8
    assert audited["gates"] == protocol["gates"]
    assert sha(solve/"model.npz") == protocol["model_sha256"]
    values = arrays(solve/"model.npz")
    for binding in audited["input_bindings"]:
        assert sha(solve/binding["path"]) == binding["sha256"]
    source_count = 0
    for directory, records in ((solve, protocol["sources"]), (audit, audited["sources"])):
        for binding in records:
            source = directory/"sources"/binding["name"]
            current = REPO/"hf_repo"/("scripts" if binding["name"] in
                ("run_split_average_demo.py", "audit_numpy_c1_path.py",
                 "hf4_split_precision_reference.py", "hf2_precision_reference.py") else "src/hf_eval")/binding["name"]
            assert sha(source) == sha(current) == binding["sha256"]
            source_count += 1
    fixed = values["fixed_dofs"]
    free = np.setdiff1d(np.arange(len(values["b_in"])), fixed)
    state_count, check_count, references_count, matrices_count = 0, 0, 0, 0
    limitations, state_results = [], []
    for case in solved["cases"]:
        summary = read(solve/case["path"]/"summary.json")
        assert summary == {key: case[key] for key in summary}
        assert [r["d"] for r in summary["states"]] == protocol["targets_mm"]
        stiffness = summary["k_out_N_per_mm"]
        for index, row in enumerate(summary["states"]):
            recorded = next(r for r in audited["states"] if r["case"] == case["path"] and r["index"] == index)
            state_path = solve/case["path"]/row["path"]
            assert sha(state_path) == row["file_sha256"]
            state = arrays(state_path)
            assert digest_state(state) == row["state_sha256"] == recorded["state_sha256"]
            np.testing.assert_array_equal(state["u_lift"], row["d"]*values["lift_shape"])
            assert np.all(state["u_fluctuation"][fixed] == 0.)
            assert all(np.isfinite(x).all() for x in state.values())
            hp, task = {}, {}
            for precision, reference in zip((80, 120), recorded["references"]):
                assert sha(audit/reference["path"]) == reference["sha256"]
                with gzip.open(audit/reference["path"], "rt", encoding="utf-8") as stream:
                    saved = json.load(stream)
                hp[precision] = {key: decimals(value) for key, value in saved["mechanics"].items()
                                 if key.endswith("_decimal") and isinstance(value, list)}
                with localcontext() as exact:
                    exact.prec = 3000
                    expected_u = [D(a)+D(b) for a, b in zip(state["u_lift"], state["u_fluctuation"])]
                assert hp[precision]["physical_displacement_decimal"] == expected_u
                task[precision] = task_measure(hp[precision], values, row, stiffness)
                for key, value in task[precision].items():
                    if key != "free":
                        assert decimals(saved["task"][key]) == value, (case["path"], index, precision, key)
                    else:
                        assert saved["task"][key] == value
                references_count += 1
            total_record, augmented_record = recorded["matrices"]
            for record in recorded["matrices"]:
                assert sha(audit/record["path"]) == record["sha256"]
                matrices_count += 1
            total = sparse.load_npz(audit/total_record["path"])
            augmented = sparse.load_npz(audit/augmented_record["path"])
            bo, bi, v = [values[key] for key in ("b_out", "b_in", "tangent_direction")]
            expected_free = (total+sparse.csc_matrix(stiffness*np.outer(bo, bo)))[free][:, free]
            col = sparse.csc_matrix(bi[free, None])
            expected_augmented = sparse.bmat([[expected_free, -col], [col.T, None]], format="csc")
            np.testing.assert_array_equal(augmented.toarray(), expected_augmented.toarray())
            action = augmented @ np.r_[v[free], float(values["tangent_multiplier_direction"])]
            actual = dict(zip(NAMES[:3], [state[key] for key in
                ("internal_force", "material_internal_force", "regularization_internal_force")]))
            actual["total_tangent"] = total@v
            checks = {}
            with localcontext() as context:
                context.prec = 120
                sf = task[80]["force_scale"]
                for name, key in zip(NAMES, HP_KEYS):
                    target = hp[80][key]
                    denominator = sf if name == "total_force" else max(norm(target),
                        Decimal("1e-12")*sf if "force" in name else Decimal("1e-10"))
                    if name in actual:
                        checks[name] = norm([D(a)-b for a, b in zip(actual[name], target)])/denominator
                    else:
                        limitations.append(dict(case=case["path"], index=index, check=name,
                            reason="Candidate component action/matrix not saved; kernel execution prohibited"))
                    checks[name+"__hp80_hp120"] = norm([a-b for a, b in zip(hp[80][key], hp[120][key])])/denominator
                checks["force_evaluation"] = norm([D(a)-b for a, b in zip(state["internal_force"], hp[80]["internal_decimal"])])/sf
                for key, target in (("input_force", "actuator"), ("spring_force_on_structure", "spring_force"), ("support_reaction", "support")):
                    checks["saved_"+key] = norm([D(a)-b for a, b in zip(state[key], task[80][target])])/sf
                for key in ("q_in", "q_out"):
                    checks["reported_"+key] = abs(D(row[key])-task[80][key])/task[80]["displacement_scale"]
                for precision in (80, 120):
                    for key in ("relative_residual", "relative_constraint", "relative_force_balance", "fixed_error_mm"):
                        checks[f"hp{precision}__{key}"] = task[precision][key]
                    checks[f"hp{precision}__positive_J"] = task[precision]["min_J"]
                checks["production_residual"] = Decimal(str(row["relative_residual"]))
                checks["support_zero_on_free_dofs"] = bool(np.all(state["support_reaction"][free] == 0.))
                balance = [sum((D(state["support_reaction"][i])+task[80]["actuator"][i]+task[80]["spring_force"][i]
                    for i in range(j, len(bi), 2)), Decimal(0)) for j in (0, 1)]
                bs = max(norm(list(map(D, state["support_reaction"])))+norm(task[80]["actuator"])+norm(task[80]["spring_force"]), sf)
                checks["stored_support_balance"] = norm(balance)/bs
                target = task[80]["augmented_force"]
                checks["augmented_force_tangent"] = norm([D(a)-target[i] for a, i in zip(action[:-1], free)])/max(norm([target[i] for i in free]), Decimal("1e-10"))
                checks["augmented_constraint_tangent"] = abs(D(action[-1])-task[80]["augmented_constraint"])/max(abs(task[80]["augmented_constraint"]), Decimal("1e-6"))
                checks["augmented_force_tangent__hp80_hp120"] = norm([a-b for a, b in zip(task[80]["augmented_force"], task[120]["augmented_force"])])/max(norm(target), Decimal("1e-10"))
            for check in recorded["checks"]:
                name = check["name"]
                assert check["pass_gate"]
                if name not in checks:
                    assert name in ("material_tangent", "regularization_tangent")
                    continue
                value = checks[name]
                if isinstance(value, bool):
                    assert value == check["pass_gate"]
                else:
                    assert value == Decimal(check["value"]), (case["path"], index, name)
                    assert (value > 0 if "positive_J" in name else value.is_finite() and value <= Decimal(check["limit"]))
                check_count += 1
            residual = state["internal_force"]-state["spring_force_on_structure"]-state["input_force"]
            scale = max(*[float(np.linalg.norm(state[key][free])) for key in
                ("internal_force", "spring_force_on_structure", "input_force")], row["force_scale_floor"])
            assert float(np.linalg.norm(residual[free]))/scale == row["relative_residual"]
            assert scale == row["residual_scale"]
            state_results.append(dict(case=case["path"], index=index, original_checks=len(recorded["checks"]),
                independently_recomputed_checks=len(checks), exact_physical_array_match=True,
                force_scale_decimal=str(sf), augmented_CSC_equation_identity=True,
                total_CSC_action_recomputed=True))
            state_count += 1
    receipt.update(status="pass_with_explicit_replay_limitations", original_audit_status=audited["status"],
        original_checks=audited["checks_completed"], independently_recomputed_checks=check_count,
        omitted_candidate_component_checks=len(limitations), limitations=limitations,
        state_count=state_count, fresh_HP_calls_in_review=0, force_kernel_calls_in_review=0,
        solver_calls_in_review=0, input_file_bindings_verified=len(audited["input_bindings"]),
        source_file_bindings_verified=source_count, reference_file_hashes_verified=references_count,
        sparse_matrix_file_hashes_verified=matrices_count, states=state_results,
        solve_summary_sha256=sha(solve/"summary.json"), audit_summary_sha256=sha(audit/"summary.json"))


def main():
    output = ROOT/"independent_review.json"
    if output.exists():
        raise FileExistsError("Independent review is immutable; preserve failed history before a new revision")
    receipt = dict(kind="saved_arithmetic_and_identity_review", datetime_utc=datetime.now(timezone.utc).isoformat(),
        reviewer_source_sha256=sha(Path(__file__)), scope="Saved primitive arrays, Decimal strings and CSC matrices; no fresh mechanics evaluation",
        test_history=[
            dict(kind="test_run", command="python -B -m pytest -q tests/test_split_displacement.py",
                 interpreter="D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe",
                 passed=8, failed=0, elapsed_pytest_seconds=2.27, exit_code=0,
                 note="Initial 8-case source before later test strengthening; no archived source hash for this invocation"),
            dict(kind="test_run", command="python -B -m pytest -q tests/test_split_displacement.py tests/test_displacement.py",
                 interpreter="D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe",
                 passed=44, failed=1, elapsed_pytest_seconds=2.72, exit_code=1,
                 split_cases_passed=9, common_synthetic_cases_passed=35,
                 failure="Original real_tmc_small_path_tangent_limit_and_A_B_A: runtime_configuration, JAX x64 disabled at early import",
                 current_test_source_sha256=sha(REPO/"hf_repo/tests/test_split_displacement.py"),
                 note="Recorded actual import-order failure; no hidden environment change or agent retry"),
            dict(kind="static_review", checks="Independent source reading, test AST parse and git diff --check; no solver or HP execution")])
    try:
        run(receipt)
    except Exception as error:
        receipt.update(status="failed_review", failure_type=type(error).__name__, failure=str(error))
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        raise
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "state_count", "original_checks", "independently_recomputed_checks", "omitted_candidate_component_checks")}))


if __name__ == "__main__":
    main()
