"""Independent saved JSON/NPZ review; no HF, solver, geometry or nodal imports."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import numpy as np

ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
OUT = Path("D:/hf-workpiece-enlarge-author-20261007/final_physical_data_review.json")
BASE = "lf_data_preparation/native_workpiece_001"
OLD = "enlarged_square_projection_001"
NEW = "gamma_half_cycle_001"
sha = lambda p: sha256(p.read_bytes()).hexdigest()
pins = {}

def bind(path, expected=None):
    value = sha(path)
    assert expected is None or value == expected, str(path)
    pins[path.relative_to(ROOT).as_posix()] = value
    return value

def read(path):
    bind(path)
    return json.loads(path.read_text(encoding="utf-8"))

def row_data(row):
    return {**{k: row[k] for k in ("d", "leg", "original_target_index", "state_sha256", "R_input", "q_in", "q_out",
        "relative_residual", "constraint_residual", "minimum_J", "max_abs_Hu_per_mm", "newton_checks",
        "assembler_force_call", "assembler_tangent_call")},
        "force_on_lower_body_N": row["workpiece"]["force_on_lower_body_N"],
        "holding_reaction_on_model_N": row["workpiece"]["holding_reaction_on_model_N"],
        "two_sided_normal_magnitude_sum_N": row["workpiece"]["two_sided_normal_magnitude_sum_N"],
        "full_workpiece_net_force_N": row["workpiece"]["full_workpiece_net_force_N"],
        "existing_node_window_clearance_mm": row["workpiece"]["node_window_clearance_mm"]}

def chronology(result, receipt):
    """Independently merge base/trial chronology of these two complete unbisected paths."""
    diag = result["path_diagnostics"]
    assert diag["failed_attempts"] == [] and diag["maximum_bisection_depth"] == 0
    bases, trials, states, linear = (diag["newton_history"],diag["trials"],result["states"],diag["linear_solve_diagnostics"])
    bi = ti = tangent = 0
    ledger, cached, groups = [], [], []
    for si, state in enumerate(states):
        assert state["bisection_depth"] == 0 and state["is_original_target"] is True
        for iteration in range(1,state["newton_checks"]+1):
            base = bases[bi];bi += 1;tangent += 1
            assert (base["d"],base["newton_check"]) == (state["d"],iteration)
            event = dict(force_ordinal=len(ledger)+1,kind="Newton_base",state_index=si,d=state["d"],
                newton_check=iteration,completed=True,tangent_ordinal=tangent)
            ledger.append(event)
            if iteration == state["newton_checks"]:
                assert event["force_ordinal"] == state["assembler_force_call"]
                assert tangent == state["assembler_tangent_call"] and base["state_sha256"] == state["state_sha256"]
                cached.append(event)
                continue
            group = []
            while True:
                trial = trials[ti]
                assert (trial["stage_parameter"],trial["target_displacement"],trial["newton_check"]) == (state["d"],state["d"],iteration)
                assert trial["factor"] == 2.**(-len(group)) and trial["fixed_residual_scale"] == base["residual_scale"]
                reason = trial.get("reason")
                if trial["accepted"] is True:
                    assert reason is None
                    category, completed = "accepted", True
                else:
                    assert reason in ("invalid_J","unsupported_arithmetic_range","armijo_insufficient_decrease")
                    category, completed = reason, reason == "armijo_insufficient_decrease"
                assert all(k in trial for k in ("phi","minimum_J","R_input")) if completed else not any(k in trial for k in ("phi","minimum_J","R_input"))
                if completed:
                    assert (trial["phi"] <= (1-2*result["settings"]["armijo_c"]*trial["factor"])*trial["base_phi"]) == trial["accepted"]
                event = dict(force_ordinal=len(ledger)+1,kind="line_search_trial",state_index=si,d=state["d"],
                    newton_check=iteration,trial_index=ti,factor=trial["factor"],category=category,completed=completed)
                ledger.append(event);group.append(event);ti += 1
                if trial["accepted"]:
                    break
            assert len(group) <= result["settings"]["max_backtracks"]+1
            groups.append(group)
    assert bi == len(bases) and ti == len(trials)
    counts = result["call_counts"]
    assert len(ledger) == counts["force_calls"] and sum(r["completed"] for r in ledger) == counts["force_calls_completed"]
    assert tangent == len(bases) == counts["tangent_calls"] == counts["tangent_calls_completed"]
    predictors = [r for r in linear if r["phase"] == "predictor"]
    correctors = [r for r in linear if r["phase"] == "corrector"]
    assert len(predictors) == len(states)-1 and len(correctors) == len(bases)-len(states)
    assert all(r["displacement_mode"] == "port_projection" and r["applied_dw"] is False and r["applied_dR"] is True for r in predictors)
    assert all(r["factorization"] == "general sparse LU" and r["symmetrized"] is False for r in linear)
    categories = Counter(r["category"] for r in ledger if r["kind"] == "line_search_trial")
    rejected = {reason:[r for r in ledger if r.get("category") == reason] for reason in
        ("invalid_J","unsupported_arithmetic_range","armijo_insufficient_decrease")}
    first_range = rejected["unsupported_arithmetic_range"]
    assert receipt["first_force_range_input"]["force_call_ordinal"] == first_range[0]["force_ordinal"] if first_range else receipt["first_force_range_input"] is None
    assert receipt["first_tangent_range_input"] is None
    return dict(counts=counts,base_completed=len(bases),trial_started=len(trials),trial_categories=dict(categories),
        predictor_LU=len(predictors),corrector_LU=len(correctors),total_LU=len(linear),
        failed_attempts=0,maximum_bisection_depth=0,maximum_trials_per_corrector=max(map(len,groups)),
        rejected_trial_records=rejected,first_force_range_ordinal=first_range[0]["force_ordinal"] if first_range else None,
        cached_state_ordinals=cached,complete_force_ordinal_ledger=ledger)

cases = {}
for label, name in (("gamma_baseline",OLD),("gamma_half",NEW)):
    control = ROOT/BASE/name;stage = control/"run_001"
    result = read(stage/"result/result.json");receipt = read(stage/"execution_receipt.json")
    inventory = read(stage/"input_inventory.json");freeze = read(stage/"source_freeze.json")
    launch = read(control/"production_launch.json");protocol = read(control/"production_protocol.json")
    task = read(stage/"task.json");metadata = read(stage/"result/model/model.json")
    assert result["status"] == "success" and receipt["status"] == launch["status"] == "pass"
    assert receipt["result_sha256"] == bind(stage/"result/result.json") and receipt["call_counts"] == result["call_counts"]
    assert launch["exit_code"] == 0 and launch["invocations"] == receipt["invocations"] == 1
    assert launch["all_bindings_unchanged"] is True and launch["stop_reason"] is None
    assert launch["protocol_sha256"] == bind(control/"production_protocol.json")
    assert receipt["sources"] == freeze["sources"] and receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
    assert receipt["force_hook_restored"] is receipt["tangent_hook_restored"] is True
    assert result["accepted_states"] == receipt["accepted_states"] == len(result["states"]) == 24
    assert [r["d"] for r in result["states"]] == result["targets_mm"] and result["states"][0]["d"] == result["states"][-1]["d"] == 0.
    assert all(result[k] is True for k in ("production_converged","path_completed","loading_peak_reached","unload_endpoint_reached","lift_origin_zero","lift_shape_zero"))
    assert all(result[k] is False for k in ("equilibrium_qualified","independent_HP_qualified","HF_qualified"))
    model_path = stage/"result"/result["model"]["arrays_path"]
    bind(model_path,result["model"]["arrays_sha256"])
    assert receipt["model_sha256"] == sha(model_path)
    core = {p:v for p,v in freeze["sources"].items() if p.startswith("hf_repo/src/hf_eval/")}
    assert len(core) == 24
    for p,v in core.items():bind(ROOT/p,v);bind(stage/"sources"/Path(p).name,v)
    original = [row_data(r) for r in result["states"]]
    peak = max(original,key=lambda r:r["d"])
    assert peak["original_target_index"] == 13 and peak["d"] == 1.2
    cases[label] = dict(stage=stage.relative_to(ROOT).as_posix(),result=result,receipt=receipt,inventory=inventory,
        task=task,metadata=metadata,core=core,model_path=model_path,
        summary=dict(production_terminal_status="pass",accepted_states=24,original_targets_retained=24,
            peak=row_data(result["states"][13]),origin=original[0],unload_endpoint=original[-1],
            all_original_rows=original,chronology=chronology(result,receipt),
            extrema_from_saved_state_JSON=dict(global_minimum_J=min(r["minimum_J"] for r in original),
                maximum_abs_Hu_per_mm=max(r["max_abs_Hu_per_mm"] for r in original),
                max_relative_residual=max(r["relative_residual"] for r in original),
                maximum_abs_constraint_residual=max(abs(r["constraint_residual"]) for r in original)),
            resources=dict(helper_elapsed_seconds=receipt["elapsed_seconds"],outer_elapsed_seconds=launch["elapsed_seconds"],
                helper_limit_seconds=receipt["seconds_limit"],outer_limit_seconds=launch["outer_seconds"],
                helper_sampled_peak_RSS_bytes=receipt["sampled_peak_RSS_bytes"],
                outer_sampled_peak_tree_RSS_bytes=launch["peak_sampled_tree_RSS_bytes"],
                sampled_RSS_limit_bytes=launch["sampled_RSS_limit_bytes"],
                binding_count=len(protocol["bindings"]),all_bindings_unchanged=True,
                path_timing_seconds=result["path_diagnostics"]["timing_seconds"])))

a,b = cases["gamma_baseline"],cases["gamma_half"]
assert a["core"] == b["core"]
assert a["result"]["targets_mm"] == b["result"]["targets_mm"] and a["result"]["tangent_execution"] == b["result"]["tangent_execution"]
assert b["result"]["settings"] == dict(a["result"]["settings"],time_limit_seconds=4500.)
assert a["inventory"]["gates"] == b["inventory"]["gates"]
descriptive = {"task_id","purpose","parameter_origin"}
assert {k:v for k,v in b["task"].items() if k not in descriptive} == {k:v for k,v in dict(a["task"],third_medium=dict(gamma=5e-7)).items() if k not in descriptive}

with np.load(a["model_path"],allow_pickle=False) as archive:
    model_a = {k:archive[k] for k in archive.files}
with np.load(b["model_path"],allow_pickle=False) as archive:
    model_b = {k:archive[k] for k in archive.files}
assert set(model_a) == set(model_b) and len(model_a) == 27
changed = {"gamma","lam","mu"};solid = model_a["solid"].astype(bool)
fields = {}
for name in sorted(model_a):
    x,y = model_a[name],model_b[name]
    assert x.dtype == y.dtype and x.shape == y.shape
    record = dict(dtype=str(x.dtype),shape=list(x.shape),baseline_array_sha256=sha256(x.tobytes()).hexdigest(),gamma_half_array_sha256=sha256(y.tobytes()).hexdigest())
    if name in changed:
        assert x[solid].tobytes() == y[solid].tobytes() and np.array_equal(y[~solid],x[~solid]*.5)
        record.update(solid_values_byte_exact=True,medium_values_exact_half=True)
    else:
        assert x.tobytes() == y.tobytes();record["byte_exact"]=True
    fields[name] = record

def delta(before,after):
    return dict(baseline=before,gamma_half=after,difference=after-before,
        relative_difference_percent=100*(after-before)/abs(before) if abs(before)>1e-20 else None)

matched = []
for before,after in zip(a["summary"]["all_original_rows"],b["summary"]["all_original_rows"]):
    assert (before["d"],before["leg"],before["original_target_index"]) == (after["d"],after["leg"],after["original_target_index"])
    matched.append(dict(original_target_index=before["original_target_index"],leg=before["leg"],d_mm=before["d"],
        R_input_N=delta(before["R_input"],after["R_input"]),q_out_mm=delta(before["q_out"],after["q_out"]),
        body_force_N={component:[delta(x,y) for x,y in zip(before["force_on_lower_body_N"][component],after["force_on_lower_body_N"][component])]
            for component in ("total","material","regularization")},minimum_J=delta(before["minimum_J"],after["minimum_J"]),
        max_abs_Hu_per_mm=delta(before["max_abs_Hu_per_mm"],after["max_abs_Hu_per_mm"])))

hysteresis = {}
for label,case in cases.items():
    rows = case["summary"]["all_original_rows"]
    pairs = []
    for load in rows:
        if load["leg"] not in ("origin","loading"):continue
        unload = [r for r in rows if r["leg"] == "unloading" and r["d"] == load["d"]]
        if unload:
            assert len(unload) == 1
            u = unload[0]
            pairs.append(dict(d_mm=load["d"],loading_original_target_index=load["original_target_index"],
                unloading_original_target_index=u["original_target_index"],
                delta_unload_minus_load_R_input_N=u["R_input"]-load["R_input"],
                delta_unload_minus_load_q_out_mm=u["q_out"]-load["q_out"],
                delta_unload_minus_load_body_Fy_N=u["force_on_lower_body_N"]["total"][1]-load["force_on_lower_body_N"]["total"][1]))
    hysteresis[label] = pairs

review = dict(schema_version="gamma-half-final-physical-saved-data-review-1.0",status="production_saved_data_review_pass",
    scope="Saved production data only. No new force, tangent, equilibrium, HP, geometry or nodal calculation; running independent reference is not claimed to pass.",
    independent_gamma_half_reference_status="running_per_root_message_not_read_or_qualified_by_this_review",
    reviewer_source=dict(file=Path(__file__).as_posix(),sha256=sha(Path(__file__))),
    input_bindings=pins,core_24_raw_sha_equal=True,core_24_sha256=a["core"],
    matching_conditions=dict(geometry="same native h1 side18 center(71,40) fixed square; body [62,80]x[31,40], zero right-medium margin",
        E_MPa=1.,nu=.3,thickness_mm=20.,alpha=1e-6,Lr_mm=80.,same_ports_supports_body_and_directions=True,
        target_sequence=a["result"]["targets_mm"],peak_input_mm=1.2,initial_guess="port_projection",same_math_gates=True,
        physical_change="gamma1e-6→5e-7 only; solid coefficients unchanged and medium gamma/lam/mu halved",
        resource_change="New independent production card4500/4560s versus closed baseline3000/3060s; not a physical input change"),
    model_comparison=dict(total_fields=27,changed_fields=sorted(changed),unchanged_fields=sorted(set(model_a)-changed),field_proof=fields),
    cases={label:case["summary"] for label,case in cases.items()},all_original_matched_comparisons=matched,load_unload_pairs=hysteresis,
    interpretation=dict(peak_body_Fy_difference_percent=matched[13]["body_force_N"]["total"][1]["relative_difference_percent"],
        peak_R_input_difference_percent=matched[13]["R_input_N"]["relative_difference_percent"],
        peak_q_out_difference_mm=matched[13]["q_out_mm"]["difference"],
        peak_minimum_J_ratio=b["summary"]["peak"]["minimum_J"]/a["summary"]["peak"]["minimum_J"],
        gamma_force_scaling="Body force after re-equilibration is not proportional to gamma; this pair is sensitivity evidence at this boundary only, not gamma convergence.",
        force_definition="Signed weak-form force on lower fixed body; holding reaction opposite. Two-sided magnitude sum2abs(Fy) is distinct from mirrored net(2Fx,0). No pressure/contact/clamp certification.",
        numerical_return="Origin and unloaded zero fields are retained raw, including tiny signed residuals; no force clipping.",
        cost_scope="Old354/330F176T and2839.98s describe its single closed baseline task, not gamma-half or an acceptance ceiling. New368/338F180T and1915.96s describe this card on this machine; wall time alone does not establish algorithmic speed improvement.",
        medium_safety="Saved global minimumJ falls to about half while Fy is close; same right-boundary task only. No new medium geometry or self-intersection observation is added.",
        geometry_and_strain="Only pre-existing node-window clearance and stateJSON J/Hu summaries are copied. Finite tip-surface gaps, Green strain and full saved deformation will be read from the planned qualified saved-only views, avoiding duplicate observations."),
    activity=dict(candidate_module_imports=0,FE_calls=0,force_calls=0,tangent_calls=0,solver_calls=0,HP_calls=0,
        geometry_calls=0,nodal_calls=0,constitutive_calls=0,cached_model_NPZ_reads=2,cached_state_NPZ_reads=0,formal_repository_writes=0))
assert all(sha(ROOT/path) == pin for path,pin in pins.items())
OUT.write_text(json.dumps(review,indent=2,allow_nan=False)+"\n",encoding="utf-8")
print(json.dumps(dict(status=review["status"],report_sha256=sha(OUT),model_fields=27,raw_unchanged_fields=24,
    cases={label:{"counts":case["summary"]["chronology"]["counts"],"trial_categories":case["summary"]["chronology"]["trial_categories"],
        "first_force_range_ordinal":case["summary"]["chronology"]["first_force_range_ordinal"],"peak":case["summary"]["peak"]["force_on_lower_body_N"]["total"]} for label,case in cases.items()},
    interpretation=review["interpretation"])))
