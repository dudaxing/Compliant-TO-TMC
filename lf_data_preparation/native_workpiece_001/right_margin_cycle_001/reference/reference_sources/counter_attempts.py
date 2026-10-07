"""Pure saved chronology accounting for a complete shifted-square cycle.

No model, force, tangent, consumer or HP evaluation. Unknown trace structures
fail closed. Predictor invalid-J bases and recovered invalid-J trials are distinct.
"""
from math import isfinite


def reconstruct(result, receipt, settings, check):
    counts, diagnostics = result["call_counts"], result["path_diagnostics"]
    history, trials, states = diagnostics["newton_history"], diagnostics["trials"], result["states"]
    failures, linear = diagnostics["failed_attempts"], diagnostics["linear_solve_diagnostics"]
    keys = {"force_calls", "force_calls_completed", "tangent_calls", "tangent_calls_completed",
            "solver_invocations", "HP_calls", "JIT_calls"}
    check(result["status"] == "success" and result["failure"] is None and result["path_completed"] is True,
          "Counter accounting requires a complete successful path, never a partial timeout")
    check(set(counts) == keys and all(type(v) is int and v >= 0 for v in counts.values())
        and counts["solver_invocations"] == 1 and counts["HP_calls"] == counts["JIT_calls"] == 0
        and receipt["call_counts"] == counts and receipt["force_calls"] == receipt["observed_force_calls"] == counts["force_calls"]
        and receipt["tangent_calls"] == receipt["observed_tangent_calls"] == counts["tangent_calls"]
        and receipt["observed_force_calls_completed"] == counts["force_calls_completed"]
        and receipt["observed_tangent_calls_completed"] == counts["tangent_calls_completed"]
        and receipt["solver_calls"] == 1 and receipt["HP_calls"] == receipt["JIT_calls"] == receipt["LF_imports"] == 0
        and receipt["save_force_calls"] == receipt["save_tangent_calls"] == 0,
        "Actual production/observer/non-mechanical counters differ")
    segments = [dict(predictor=None, correctors=[])]
    for index, row in enumerate(linear):
        check(row["factorization"] == "general sparse LU" and row["symmetrized"] is False
            and row["target_displacement"] == row["stage_parameter"]
            and all(isfinite(row[k]) for k in ("force_block_residual_norm", "relative_force_block_residual",
                "constraint_block_residual", "normwise_backward_error")), "Unaccounted LU record")
        if row["phase"] == "predictor":
            check(row["newton_check"] is None and all(isfinite(row[k]) for k in
                ("mean_error_before_projection", "mean_error_after_projection")), "Predictor LU record differs")
            segments.append(dict(predictor=dict(index=index, **row), correctors=[]))
        else:
            check(row["phase"] == "corrector" and type(row["newton_check"]) is int,
                  "Unknown linear-solve phase")
            segments[-1]["correctors"].append(dict(index=index, **row))
    hi = ti = si = fi = ai = tangent = completed = completed_tangents = 0
    current_d, current_R = 0., 0.
    events, caches, attempts, invalid_bases, range_trials, invalid_trials, failed_tangents = [], [], [], [], [], [], []
    observed_depth = 0

    def event(kind, d, iteration, force_complete, tangent_started=False, tangent_complete=False, **extra):
        nonlocal tangent, completed, completed_tangents
        tangent += int(tangent_started); completed += int(force_complete); completed_tangents += int(tangent_complete)
        item = dict(force_call=len(events)+1, kind=kind, d=d, newton_check=iteration,
                    completed=force_complete, tangent_call=tangent if tangent_started else None,
                    tangent_completed=tangent_complete, **extra)
        events.append(item)
        return item

    def trial_group(base, corrector, exhaustion=False):
        nonlocal ti
        check(corrector["newton_check"] == base["newton_check"] and corrector["stage_parameter"] == base["d"],
              "Corrector is not attached to its complete Newton base")
        group = []
        while ti < len(trials) and len(group) <= settings["max_backtracks"]:
            row = trials[ti]
            check((row["stage_parameter"], row["newton_check"]) == (base["d"], base["newton_check"])
                and row["target_displacement"] == base["d"] and type(row["accepted"]) is bool
                and row["factor"] == 2.**(-len(group)) and row["fixed_residual_scale"] == base["residual_scale"]
                and isfinite(row["base_phi"]) and row["base_phi"] >= 0., "Trial chronology/factor/base scale differs")
            reason = row.get("reason")
            incomplete = row["accepted"] is False and reason in ("unsupported_arithmetic_range", "invalid_J")
            if incomplete:
                check(not any(k in row for k in ("phi", "minimum_J", "R_input"))
                    and len(group) < settings["max_backtracks"] and ti+1 < len(trials),
                    "Rejected incomplete force has contradictory fields or no supported half-factor continuation")
                following = trials[ti+1]
                check((following["stage_parameter"],following["newton_check"],following["factor"])
                    == (base["d"],base["newton_check"],row["factor"]/2), "Incomplete trial lacks the same-base half factor")
            else:
                check(all(k in row and isfinite(row[k]) for k in ("phi", "minimum_J", "R_input"))
                    and row["minimum_J"] > 0. and ((row["accepted"] is True and reason is None)
                        or (row["accepted"] is False and reason == "armijo_insufficient_decrease")),
                    "Unknown trial reason/completion cannot be attributed")
                passed = row["phi"] <= (1-2*settings["armijo_c"]*row["factor"])*row["base_phi"]
                check(passed == row["accepted"], "Saved trial acceptance differs from original Armijo rule")
            e = event("line_search_trial", base["d"], base["newton_check"], not incomplete,
                      trial_index=ti, factor=row["factor"], accepted=row["accepted"], reason=reason)
            if incomplete:
                (invalid_trials if reason == "invalid_J" else range_trials).append(dict(row, trial_index=ti, force_call=e["force_call"]))
            group.append(row); ti += 1
            if row["accepted"]:
                break
        check(group and (all(r["accepted"] is False for r in group) and len(group) == settings["max_backtracks"]+1
            if exhaustion else group[-1]["accepted"] is True), "Trial group did not terminate at its declared acceptance/exhaustion")

    def advance(d, depth, original_index):
        nonlocal ai, fi, hi, si, current_d, current_R, observed_depth
        check(ai < len(segments), "Missing attempt/predictor segment")
        segment = segments[ai]; ai += 1; observed_depth = max(observed_depth, depth)
        before_d, before_R = current_d, current_R
        predictor = segment["predictor"]
        check((predictor is None and original_index == 0 and d == before_d == 0. and depth == 0)
            or (predictor is not None and d != before_d and predictor["stage_parameter"] == d),
            "Attempt does not match its initial/predictor boundary")
        failure = failures[fi] if fi < len(failures) and (failures[fi]["from_displacement"],
            failures[fi]["attempted_displacement"], failures[fi]["depth"]) == (before_d, d, depth) else None
        correctors = segment["correctors"]
        if failure is not None:
            fi += 1
            check(failure["rollback_bitwise_equal"] is True and failure["from_R_input"] == before_R
                and depth < settings["max_bisections"] and abs(d-before_d)/2 >= settings["minimum_increment"]*(1-1e-12),
                "Failed attempt has no valid bitwise rollback/bounded midpoint recovery")
            code = failure["code"]
            check(code in ("invalid_J", "unsupported_arithmetic_range", "newton_limit", "backtracking_failed"),
                  "Unknown failed-attempt branch is outside this counter contract")
            if code == "invalid_J":
                check(predictor is not None and not correctors and failure["reason"] == "NumPy total J must be positive",
                      "Only a first predictor-base native J-guard rejection is supported")
                base_count = 0
            elif code == "unsupported_arithmetic_range":
                observation = receipt["first_tangent_range_input"]
                check(observation is not None and not failed_tangents and observation["code"] == code
                    and observation["bound_force_fields_same_object"] is True and observation["details"]["field"] == "total_tangent",
                    "Unobserved/multiple/non-tangent base range failure")
                base_count = len(correctors)
            elif code == "newton_limit":
                check(len(correctors) == settings["max_checks"]-1, "Newton limit does not contain all original base checks")
                base_count = settings["max_checks"]
            else:
                check(bool(correctors), "Backtracking failure has no completed corrector")
                base_count = len(correctors)
        else:
            check(si < len(states), "Attempt has neither a recorded failure nor an accepted cache")
            state = states[si]; si += 1
            check((state["d"], state["bisection_depth"], state["original_target_index"]) == (d,depth,original_index)
                and state["original_target_displacement"] == result["targets_mm"][original_index]
                and type(state["newton_checks"]) is int and 1 <= state["newton_checks"] <= settings["max_checks"]
                and len(correctors) == state["newton_checks"]-1, "Accepted attempt/cache/linear chronology differs")
            base_count = state["newton_checks"]
        for iteration in range(1, base_count+1):
            check(hi < len(history), "Missing completed Newton history")
            base = history[hi]; hi += 1
            check((base["d"],base["newton_check"]) == (d,iteration)
                and isfinite(base["relative_residual"]) and base["relative_residual"] >= 0.
                and isfinite(base["constraint_residual"]) and abs(base["constraint_residual"]) <= base["constraint_bound"]
                and isfinite(base["minimum_J"]) and base["minimum_J"] > 0., "Newton history/constraint/J chronology differs")
            e = event("Newton_base", d, iteration, True, True, True, state_sha256=base["state_sha256"])
            cached = failure is None and iteration == base_count
            if cached:
                check(base["relative_residual"] <= settings["tolerance"]
                    and state["assembler_force_call"] == e["force_call"] and state["assembler_tangent_call"] == e["tangent_call"]
                    and state["assembler_state_sha256"] == state["state_sha256"] == base["state_sha256"],
                    "Accepted state is not the completed converged base/cache ordinal")
                caches.append(dict(force_call=e["force_call"],tangent_call=e["tangent_call"],state_sha256=state["state_sha256"]))
            else:
                check(base["relative_residual"] > settings["tolerance"], "Converged base inexplicably continued/rejected")
                if failure is not None and failure["code"] == "newton_limit" and iteration == base_count:
                    continue
                trial_group(base,correctors[iteration-1], failure is not None
                    and failure["code"] == "backtracking_failed" and iteration == base_count)
        if failure is None:
            current_d, current_R = d, state["R_input"]
            attempts.append(dict(target=d,depth=depth,original_index=original_index,accepted_index=si-1))
            return
        code = failure["code"]
        if code == "invalid_J":
            e = event("predictor_base_invalid_J",d,1,False, reason=code,failed_attempt_index=fi-1)
            invalid_bases.append(dict(e,predictor_linear_index=predictor["index"],from_displacement=before_d))
        elif code == "unsupported_arithmetic_range":
            observation = receipt["first_tangent_range_input"]
            e = event("failed_tangent_base",d,base_count+1,True,True,False,state_sha256=observation["state_sha256"])
            check(observation["tangent_call_ordinal"] == e["tangent_call"] and observation["bound_force_call_ordinal"] == e["force_call"]
                and all(s["state_sha256"] != observation["state_sha256"] for s in states), "Captured tangent input/derived ordinal/cache differs")
            failed_tangents.append(e)
        attempts.append(dict(target=d,depth=depth,original_index=original_index,failed_attempt_index=fi-1,code=code))
        advance(before_d+(d-before_d)/2,depth+1,original_index)
        advance(d,depth+1,original_index)

    for original_index,d in enumerate(result["targets_mm"]):
        advance(d,0,original_index)
    timing = diagnostics["timing_seconds"]
    check((ai,fi,hi,ti,si) == (len(segments),len(failures),len(history),len(trials),len(states)),
          "Unconsumed or ambiguous attempt/history/trial/cache event")
    check(len(events) == counts["force_calls"] and completed == counts["force_calls_completed"]
        and tangent == counts["tangent_calls"] and completed_tangents == counts["tangent_calls_completed"]
        and completed_tangents == len(history) and timing["kernel_calls"] == len(events)
        and timing["successful_kernel_calls"] == completed-len(failed_tangents)
        and observed_depth == diagnostics["maximum_bisection_depth"]
        and [s["state_sha256"] for s in states] == receipt["state_sha256"], "Exact reconstructed counters/assembly/cache totals differ")
    check((receipt["first_tangent_range_input"] is None) == (not failed_tangents), "Tangent capture has no exact supported event")
    return dict(counts=counts,Newton_base_calls=len(history),trial_calls=len(trials),
        completed_trials=sum(e["completed"] for e in events if e["kind"] == "line_search_trial"),
        rejected_range_trials=range_trials,
        rejected_invalid_J_trials=invalid_trials,
        predictor_invalid_J_bases=invalid_bases,reconstructed_attempts=attempts,reconstructed_force_events=events,
        accepted_completed_caches=caches,all_Newton_base_and_tangent_calls_completed=not failed_tangents,
        failed_tangent_base=failed_tangents[0] if failed_tangents else None,
        policy="Exact recursive attempt/LU/base/trial/cache chronology; native predictor J rejections and captured tangent range failures remain unqualified",
        rejected_trials_independently_qualified=False,unsupported_arithmetic_issue_resolved=False,
        production_rerun=False,new_force_calls=0,new_tangent_calls=0,new_solver_calls=0)
