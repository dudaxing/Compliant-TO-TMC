"""Fresh accepted-state reference, with explicit accounting for three trial rejections.

Only the frozen loader's named instrumentation predicate is replaced. Its
identity checks and full saved-state mathematical audit remain inherited.
No rejected trial is qualified, resumed, repaired or evaluated again.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
import argparse
import hashlib
from pathlib import Path
import shutil
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())
SCRIPTS = ROOT/"hf_repo/scripts"
OLD_CHECKER_SHA = "aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938"
PINS = dict(production_result_sha256="184e47874ec8d257dd5c4b31432ef7a6320afb82b316b94cd0ab1a897964bbc0",
    production_receipt_sha256="9ac2629655c2f69d219a9e418ce38e2bb9eeb2e3f4c94a9dc3101766c42f9491",
    source_freeze_sha256="c671f8b49f0d69a285fd3a35bb41ea8d68e57e7fce094def0b40139d1e9f019a",
    original_checker_sha256=OLD_CHECKER_SHA,
    original_precondition_sha256="d9dd5f413c91038b6831e23ee9cf67d958883ffce198a95caa326971de3d226c")
if hashlib.sha256((SCRIPTS/"audit_native_workpiece_cycle.py").read_bytes()).hexdigest() != OLD_CHECKER_SHA:
    raise ValueError("Frozen original workpiece checker changed")
sys.path.insert(0, str(SCRIPTS))
from audit_native_workpiece_cycle import WorkpieceCycleAudit, RSS_LIMIT, read, require, sha, write

COUNTS = dict(force_calls=22, force_calls_completed=19, tangent_calls=11,
    tangent_calls_completed=11, solver_invocations=1, JIT_calls=0, HP_calls=0)
PREDICATE = "Production completed counters differ"


class AcceptedStateAudit(WorkpieceCycleAudit):
    def __init__(self, args):
        super().__init__(args)
        self.contract_path, self.contract_pin = args.contract.resolve(), args.contract_sha256
        self.replaced_predicate_calls, self.accounting = 0, None

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "Accepted-state reference time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Accepted-state reference sampled RSS exceeds 8 GiB")

    def lifecycle(self, status, error=None):
        write(self.output/"lifecycle.json", dict(status=status, error=error,
            elapsed_seconds=perf_counter()-STARTED, HP_calls_started=self.hp_started,
            HP_calls_completed=self.hp_completed, checks_completed=self.checks,
            accepted_states_completed=len(self.rows), sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            replaced_instrumentation_predicate_calls=self.replaced_predicate_calls,
            stop_policy="First error stops this fresh reference; no FE, retry or repair"))

    def check(self, condition, label):
        if label == PREDICATE:
            require(self.replaced_predicate_calls == 0 and condition is False,
                    "Only the known false instrumentation predicate may be replaced once")
            self.replaced_predicate_calls += 1
            self.accounting = self.reconstruct_counts()
            condition = True  # reconstruct_counts requires every declared accounting condition.
        return super().check(condition, label)

    def reconstruct_counts(self):
        result, receipt = self.accounting_result, self.accounting_receipt
        counts, diagnostics = result["call_counts"], result["path_diagnostics"]
        history, trials = diagnostics["newton_history"], diagnostics["trials"]
        require(counts == COUNTS and receipt["call_counts"] == counts
            and receipt["force_calls"] == 22 and receipt["tangent_calls"] == 11
            and receipt["solver_calls"] == 1
            and receipt["HP_calls"] == receipt["JIT_calls"] == receipt["LF_imports"] == 0
            and receipt["save_force_calls"] == receipt["save_tangent_calls"] == 0,
            "Original non-force-completion counters or receipts differ")
        require(not diagnostics["failed_attempts"] and diagnostics["maximum_bisection_depth"] == 0
            and len(history) == len(trials) == 11 and len(result["states"]) == 3
            and [(item["d"], item["newton_check"]) for item in history]
                == [(0., 1)]+[(.1, n) for n in range(1, 4)]+[(0., n) for n in range(1, 8)],
            "Newton base chronology or target-attempt coverage differs")
        rejected = [(i, item) for i, item in enumerate(trials) if item["accepted"] is not True]
        require(len(rejected) == 3 and [item["newton_check"] for _, item in rejected] == [3, 4, 5],
                "Unknown force-call deficit or rejected trial")
        for index, item in rejected:
            require(item["accepted"] is False and item["reason"] == "unsupported_arithmetic_range"
                and item["factor"] == 1. and item["stage_parameter"] == item["target_displacement"] == 0.
                and index+1 < len(trials), "Rejected trial differs from the explicit contract")
            following = trials[index+1]
            require(following["accepted"] is True and following["factor"] == .5
                and following["newton_check"] == item["newton_check"]
                and following["stage_parameter"] == following["target_displacement"] == 0.,
                "Rejected full trial is not immediately followed by its accepted half trial")
        events, cursor, completed, cache = [], 0, 0, []
        for tangent_call, base in enumerate(history, 1):
            force_call = len(events)+1
            events.append(dict(force_call=force_call, kind="Newton_base", completed=True,
                d=base["d"], newton_check=base["newton_check"], tangent_call=tangent_call))
            completed += 1
            matching = [row for row in result["states"] if row["state_sha256"] == base["state_sha256"]]
            for row in matching:
                require(row["assembler_force_call"] == force_call and row["assembler_tangent_call"] == tangent_call
                    and row["assembler_state_sha256"] == base["state_sha256"], "Accepted cache is not a completed Newton base")
                cache.append(dict(force_call=force_call, tangent_call=tangent_call, state_sha256=base["state_sha256"]))
            while cursor < len(trials) and (trials[cursor]["stage_parameter"], trials[cursor]["newton_check"]) == (base["d"], base["newton_check"]):
                trial = trials[cursor]
                done = trial["accepted"] is True
                events.append(dict(force_call=len(events)+1, kind="line_search_trial", completed=done,
                    d=trial["stage_parameter"], newton_check=trial["newton_check"], factor=trial["factor"],
                    reason=trial.get("reason")))
                completed += int(done)
                cursor += 1
        require(cursor == len(trials) and len(events) == 22 and completed == 19
            and [item["force_call"] for item in cache] == [1, 6, 22]
            and [item["tangent_call"] for item in cache] == [1, 4, 11]
            and [item["state_sha256"] for item in cache] == receipt["state_sha256"],
            "Exact base/trial/cached-state force chronology does not reconstruct the counters")
        return dict(original_instrumentation_condition="force_calls == force_calls_completed",
            original_condition_passed=False, replacement_scope="Only this named counter predicate; no mathematical gate replacement",
            counts=COUNTS, Newton_base_calls=11, trial_calls=11, completed_trials=8,
            rejected_trials=[item for _, item in rejected], reconstructed_force_events=events,
            accepted_completed_caches=cache, all_Newton_base_and_tangent_calls_completed=True,
            rejected_trials_independently_qualified=False, unsupported_arithmetic_issue_resolved=False,
            production_rerun=False, new_force_calls=0, new_tangent_calls=0, new_solver_calls=0)

    def load(self):
        self.bind(self.contract_path, self.contract_pin)
        contract = read(self.contract_path)
        require(contract["schema_version"] == "workpiece-accepted-state-reference-contract-1.0"
            and all(contract[key] == value for key, value in PINS.items())
            and contract["helper_sha256"] == sha(Path(__file__))
            and contract["reference_seconds"] == 240 and contract["reference_outer_seconds"] == 300
            and contract["sampled_RSS_bytes"] == RSS_LIMIT
            and contract["force_calls"] == contract["tangent_calls"] == contract["solver_calls"] == 0,
            "New explicit reference contract differs")
        paths = dict(production_result_sha256=self.stage/"result/result.json",
            production_receipt_sha256=self.stage/"execution_receipt.json",
            source_freeze_sha256=self.stage/"source_freeze.json",
            original_checker_sha256=SCRIPTS/"audit_native_workpiece_cycle.py",
            original_precondition_sha256=self.stage/"reference_precondition_001.json")
        for key, path in paths.items():
            self.bind(path, PINS[key])
        original = read(paths["original_precondition_sha256"])
        require(original["status"] == "not_started_precondition_not_met"
            and original["original_reference_phase_closed_without_launch"] is True
            and original["HP_calls"] == 0 and original["predicate_pass"] is False,
            "Original unlaunched reference disposition changed")
        self.accounting_result = read(paths["production_result_sha256"])
        self.accounting_receipt = read(paths["production_receipt_sha256"])
        helper = Path(__file__).resolve()
        self.bind(helper, contract["helper_sha256"])
        for path in (helper, self.contract_path):
            shutil.copyfile(path, self.output/"sources"/path.name)
            self.bind(self.output/"sources"/path.name, sha(path))
        self.sources[helper.relative_to(self.repo).as_posix()] = sha(helper)
        super().load()
        require(self.replaced_predicate_calls == 1 and self.accounting is not None,
                "Frozen loader did not use exactly the declared replacement predicate")
        self.reference_contract = dict(path=self.contract_path.relative_to(self.repo).as_posix(), sha256=self.contract_pin,
            copied_path=(self.output/"sources"/self.contract_path.name).relative_to(self.output).as_posix())
        self.checkpoint()

    def run(self):
        super().run()
        self.checkpoint()
        summary = read(self.output/"summary.json")
        summary.update(counter_accounting=self.accounting, reference_contract=self.reference_contract,
            superseded_unlaunched_criterion=dict(path=(self.stage/"reference_precondition_001.json").relative_to(self.repo).as_posix(),
                sha256=PINS["original_precondition_sha256"], status="closed_unlaunched", HP_calls=0),
            qualification="Only the three accepted coarse fixed-square cycle states under the unchanged mathematical gates; rejected trials remain unqualified; no clamp/contact pressure/H2/H3/HF5/all-column claim",
            accepted_state_reference_contract="Explicit new reference_002; no reuse or retry of a launched HP phase",
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=self.peak)
        write(self.output/"summary.json", summary)
        for path, expected in self.bindings.items():
            require(sha(path) == expected, "Bound file changed at final reference checkpoint: "+str(path))
        self.checkpoint()
        self.lifecycle("pass")
        self.checkpoint()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=Path(__file__).with_name("reference_contract.json"))
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--time-limit", type=float, default=240.)
    args = parser.parse_args()
    require(0 < args.time_limit <= 240., "New reference limit must be in (0,240]")
    audit = AcceptedStateAudit(args)
    try:
        audit.run()
    except Exception as error:
        audit.lifecycle("not_pass", repr(error))
        write(audit.output/"summary.json", dict(schema_version="native-workpiece-cycle-independent-audit-1.0",
            status="not_pass", alias="gripper_coarse_square", error=repr(error), states=audit.rows,
            counter_accounting=audit.accounting, replaced_instrumentation_predicate_calls=audit.replaced_predicate_calls,
            accepted_states=len(audit.rows), checks_completed=audit.checks, HP_calls_started=audit.hp_started,
            HP_calls_completed=audit.hp_completed, elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__":
    main()
