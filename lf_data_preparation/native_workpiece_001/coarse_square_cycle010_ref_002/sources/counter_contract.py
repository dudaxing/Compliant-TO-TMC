"""Pure saved chronology: one captured tangent-range base and ordinary trials.

This is a bounded trace contract for cycle010, not a mechanics evaluator.
"""
from math import isfinite


def reconstruct(result, receipt, settings, check=None):
    if check is None:
        def check(condition, label):
            if not condition:
                raise ValueError(label)

    counts = result['call_counts']; diagnostics = result['path_diagnostics']
    history, trials, states = diagnostics['newton_history'], diagnostics['trials'], result['states']
    keys = {'force_calls','force_calls_completed','tangent_calls','tangent_calls_completed','solver_invocations','HP_calls','JIT_calls'}
    check(set(counts) == keys and all(type(v) is int and v >= 0 for v in counts.values()),'Counter schema')
    check(counts['solver_invocations'] == 1 and counts['HP_calls'] == counts['JIT_calls'] == 0,'Production scope')
    check(receipt['call_counts'] == counts and receipt['force_calls'] == receipt['observed_force_calls'] == counts['force_calls']
          and receipt['tangent_calls'] == receipt['observed_tangent_calls'] == counts['tangent_calls']
          and receipt['observed_force_calls_completed'] == counts['force_calls_completed']
          and receipt['observed_tangent_calls_completed'] == counts['tangent_calls_completed']
          and receipt['solver_calls'] == 1
          and all(receipt[k] == 0 for k in ('HP_calls','JIT_calls','LF_imports','save_force_calls','save_tangent_calls')),'Observer counters')
    capture = receipt['first_tangent_range_input']; failures = diagnostics['failed_attempts']
    check(capture is not None and counts['tangent_calls']-counts['tangent_calls_completed'] == 1
          and counts['tangent_calls_completed'] == len(history),'Exactly one captured local tangent failure')
    missing = capture['tangent_call_ordinal']
    check(type(missing) is int and 1 < missing < counts['tangent_calls'] and len(failures) == 1,'Unique missing base')
    failed = failures[0]
    check(capture['schema_version'] == 'native-tangent-range-input-1.0'
          and capture['code'] == failed['code'] == 'unsupported_arithmetic_range'
          and capture['details'] == {'field':'total_tangent'} and capture['bound_force_fields_same_object'] is True
          and capture['message'] == failed['reason'] and failed['rollback_bitwise_equal'] is True
          and failed['depth'] == 0 and diagnostics['maximum_bisection_depth'] == 1
          and all(capture[k] == 0 for k in ('extra_force_calls','extra_tangent_calls','extra_solver_calls','HP_calls')),'Captured failure/rollback provenance')
    by_tangent = {s['assembler_tangent_call']:s for s in states}
    check(len(by_tangent) == len(states) and all(type(k) is int and 1 <= k <= counts['tangent_calls'] and k != missing for k in by_tangent),'Accepted completed-cache ordinals')
    events, caches, rejected = [], [], []
    cursor = completed = hcursor = 0
    previous = None
    for ordinal in range(1,counts['tangent_calls']+1):
        if ordinal == missing:
            check(previous is not None and previous['d'] == failed['attempted_displacement']
                  and previous['newton_check'] < settings['max_checks']
                  and cursor > 0 and trials[cursor-1]['accepted'] is True
                  and (trials[cursor-1]['stage_parameter'],trials[cursor-1]['newton_check']) == (previous['d'],previous['newton_check']), 'Missing base follows a completed accepted trial')
            force_call = len(events)+1
            check(force_call == capture['bound_force_call_ordinal'],'Captured failed tangent force ordinal')
            events.append(dict(force_call=force_call,kind='Newton_base_tangent_range',completed=True,
                d=previous['d'],newton_check=previous['newton_check']+1,tangent_call=ordinal,
                tangent_completed=False,state_sha256=capture['state_sha256']))
            completed += 1
            check(caches and states[len(caches)-1]['d'] == failed['from_displacement']
                  and states[len(caches)-1]['R_input'] == failed['from_R_input'],'Rollback to last accepted cache')
            midpoint = (failed['from_displacement']+failed['attempted_displacement'])/2
            check(history[hcursor]['newton_check'] == 1 and history[hcursor]['d'] == midpoint
                  and states[len(caches)]['d'] == midpoint and states[len(caches)]['bisection_depth'] == 1
                  and states[len(caches)+1]['d'] == failed['attempted_displacement']
                  and states[len(caches)+1]['bisection_depth'] == 1
                  and states[len(caches)]['original_target_index'] == states[len(caches)+1]['original_target_index'], 'Original rollback/midpoint/return chronology')
            previous = None
            continue
        base = history[hcursor]; hcursor += 1
        check(type(base['newton_check']) is int and 1 <= base['newton_check'] <= settings['max_checks'],'Newton check index')
        if base['newton_check'] > 1:
            check(previous is not None and previous['d'] == base['d'] and previous['newton_check']+1 == base['newton_check'],'Complete-base sequence')
        force_call = len(events)+1
        events.append(dict(force_call=force_call,kind='Newton_base',completed=True,d=base['d'],
            newton_check=base['newton_check'],tangent_call=ordinal,state_sha256=base['state_sha256']))
        completed += 1; previous = base
        cached = by_tangent.get(ordinal)
        if cached is not None:
            check(cached['assembler_force_call'] == force_call
                  and cached['assembler_state_sha256'] == cached['state_sha256'] == base['state_sha256']
                  and cached['d'] == base['d'] and cached['newton_checks'] == base['newton_check'],'Accepted state must have completed force/tangent base')
            caches.append(dict(force_call=force_call,tangent_call=ordinal,state_sha256=cached['state_sha256']))
            continue
        group = []
        while cursor < len(trials) and len(group) <= settings['max_backtracks']:
            trial = trials[cursor]
            if (trial['stage_parameter'],trial['newton_check']) != (base['d'],base['newton_check']):
                break
            factor = 2.**(-len(group))
            check(type(trial['accepted']) is bool and trial['factor'] == factor
                  and trial['target_displacement'] == trial['stage_parameter'] == base['d']
                  and trial['fixed_residual_scale'] == base['residual_scale'],'Trial chronology/scale')
            range_failure = trial['accepted'] is False and trial.get('reason') == 'unsupported_arithmetic_range'
            if range_failure:
                check(not any(k in trial for k in ('phi','minimum_J','R_input'))
                      and len(group) < settings['max_backtracks'] and cursor+1 < len(trials),'Incomplete trial provenance')
                following = trials[cursor+1]
                check((following['stage_parameter'],following['newton_check'],following['factor']) == (base['d'],base['newton_check'],factor/2),'Range trial must halve in same base')
                rejected.append(dict(trial_index=cursor,force_call=len(events)+1,**trial))
            else:
                check(all(k in trial and isfinite(trial[k]) for k in ('phi','minimum_J','R_input'))
                      and trial['minimum_J'] > 0 and ((trial['accepted'] is True and trial.get('reason') is None)
                      or (trial['accepted'] is False and trial.get('reason') == 'armijo_insufficient_decrease')),'Unknown completed trial')
            events.append(dict(force_call=len(events)+1,kind='line_search_trial',completed=not range_failure,
                d=trial['stage_parameter'],newton_check=trial['newton_check'],factor=factor,
                accepted=trial['accepted'],reason=trial.get('reason')))
            completed += int(not range_failure); group.append(trial); cursor += 1
            if trial['accepted']:
                break
        if group:
            check(group[-1]['accepted'] is True or len(group) == settings['max_backtracks']+1,'Backtracking sequence termination')
    check(hcursor == len(history) and cursor == len(trials) and len(events) == counts['force_calls']
          and completed == counts['force_calls_completed']
          and counts['force_calls']-counts['force_calls_completed'] == len(rejected)
          and len(caches) == len(states) and [x['state_sha256'] for x in caches] == receipt['state_sha256'],'Exact force/trial/cache accounting')
    return dict(counts=counts,Newton_base_calls=len(history)+1,completed_Newton_base_calls=len(history),
        trial_calls=len(trials),completed_trials=completed-len(history)-1,rejected_range_trials=rejected,
        reconstructed_force_events=events,accepted_completed_caches=caches,failed_tangent_base=events[capture['bound_force_call_ordinal']-1],
        all_Newton_base_and_tangent_calls_completed=False,all_accepted_caches_completed=True,
        policy='One captured local tangent-range base with complete force, rollback and midpoint; original trial rules; no missing/unknown events accepted',
        rejected_trials_independently_qualified=False,failed_tangent_input_independently_qualified=False,
        unsupported_arithmetic_issue_resolved=False,production_rerun=False,new_force_calls=0,new_tangent_calls=0,new_solver_calls=0)
