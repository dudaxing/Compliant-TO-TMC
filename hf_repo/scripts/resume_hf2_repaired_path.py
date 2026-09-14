"""Resume the frozen 299-row HF-2 audit without changing its scientific gates.

This one-off, content-bound recovery inherits 290 complete array/row pairs,
re-evaluates MATLAB indices 90..99, and compares the nine overlapping rows
exactly except for timing. The three 50/80-digit checks are reconstructed from
their saved Decimal strings. No nonlinear solver or production kernel is used.
Run only under the separately authorized 120-second resource monitor.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from time import perf_counter

import numpy as np


VALIDATOR_SHA256 = "72392861066756ad875ef4b555fe5bba4f63098f6d85b9d8f0e791d13e5267ae"
HELPER_SHA256 = "97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55"
CACHE_DIRECTORY_SHA256 = "a9895e7984fe83781492549d9b9c1d69bc3b427a2ed8d42f9cdf3f03c680281b"
INPUT_SHA256 = {
    "fixture": "60832407c9b8c1c91e79e89d993e6f77c4e3c7a87f60c585c737217c49698f60",
    "spec": "ba4909b19d369890b79af8db8dfa58b01672e904fe68e8dc3175c408e23ad663",
    "new_model": "1b70862be3c2aa03ff77fa79bc0c442b0809112d622b9cec861c1d6cc89f627b",
    "new_path": "b06701814cd25effc04b50d630de9c572d8050abde46c72e8f3bcec9360e2cb3",
    "new_metadata": "d1c9b7d7b1f78d4bfdd4f8be1057502805c669b16dbf5fb922102dcae1f53fa1",
    "old_path": "28ed0812102a6561ab726417f63399881dae7dda644372f55ebc0cf4984940e9",
    "old_metadata": "0634a3af062e39632b3a23b5299defa2ed4d82ade0acfb76cb6103569550e1ab",
    "matlab_path": "95cd748aeff1edea712eec81274ce8658d3a5e54b8cc44c459c151a0924ccbc0",
    "matlab_metadata": "603b1aeead2f2c10c0130d03f7a5967c192ad9dbc2772764fb2856e9078ab994",
    "comparison": "eeb128edf55bcd92b0f43db2c515b95fc7373190f4d7e98204a4641c6a00dd60",
    "prior_receipt": "6741f2c52ed66c8649ea7ae192eacd78db0c9b2474bb5350d04e56ff00032b84",
    "resource_amendment": "69d269594961b43ef851c2db621aeb0fc02291ee5311fa2702497abdacd1c0df",
}
ARRAY_KEYS = ("source_index", "load_multiplier", "original_target", "original_target_index",
              "internal", "residual", "J", "material_energy", "reaction")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_validator():
    path = Path(__file__).with_name("validate_hf2_repaired_path.py")
    require(sha256(path) == VALIDATOR_SHA256, "original validator hash changed")
    helper = path.with_name("hf2_precision_reference.py")
    require(sha256(helper) == HELPER_SHA256, "original Decimal helper hash changed")
    spec = importlib.util.spec_from_file_location("hf2_original_path_validator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


class Recovery:
    def __init__(self, args, validator, validator_path):
        self.args, self.v, self.validator_path = args, validator, validator_path
        self.begin = perf_counter()
        self.overlap_checks = []
        self.seen = set()
        self.paths = dict(fixture=args.fixture, spec=args.spec, comparison=args.comparison,
            new_model=args.new_python/"model.npz", new_path=args.new_python/"cshape_path.npz",
            new_metadata=args.new_python/"result.json", old_path=args.old_python/"cshape_path.npz",
            old_metadata=args.old_python/"result.json", matlab_path=args.matlab/"cshape_path.npz",
            matlab_metadata=args.matlab/"cshape_path.json", prior_receipt=args.prior_receipt,
            resource_amendment=args.resource_amendment)
        for name, path in self.paths.items():
            require(sha256(path) == INPUT_SHA256[name], f"frozen input content differs: {name}")
        # Receipt absolute paths are retained as provenance only. Every actual
        # file read is located by the current CLI or this script's own directory.
        self.receipt = validator.read_json(args.prior_receipt)
        self.amendment = validator.read_json(args.resource_amendment)
        require(self.amendment["continuation_process_seconds"] == 120 and
                self.amendment["amended_postprocess_cumulative_seconds"] == 720,
                "the prospective continuation resource authorization differs")
        self.cache_files = sorted(p for p in args.previous.iterdir() if p.is_file())
        self.cache_hashes = {p.name: sha256(p) for p in self.cache_files}
        digest = hashlib.sha256(canonical(self.cache_hashes).encode()).hexdigest()
        require(digest == CACHE_DIRECTORY_SHA256, "initial audit cache content changed")
        require(sha256(args.previous/"precision_spec_used.json") == INPUT_SHA256["spec"],
                "cached spec differs from frozen precision spec")
        failure = validator.read_json(args.previous/"validation_failure.json")
        require(failure["exception_type"] == "TimeoutError" and failure["validation_status"] == "incomplete",
                "this recovery is only for the preserved deadline interruption")
        self.spec = validator.read_json(args.spec)
        self.fixture = validator.read_npz(args.fixture)
        self.side_data = {
            "new_python": validator.load_side(args.new_python)[0],
            "old_python": validator.load_side(args.old_python)[0],
            "matlab": validator.load_side(args.matlab, matlab=True)[0],
        }
        self.fixed = self.fixture["fixed_dofs"]
        self.free = np.setdiff1d(np.arange(len(self.fixture["F0"])), self.fixed)
        rows = [json.loads(line) for line in (args.previous/"state_progress.jsonl").read_text(encoding="utf-8").splitlines()]
        expected = [(side, i) for side, count in (("new_python", 100), ("old_python", 100), ("matlab", 99)) for i in range(count)]
        require([(r["side"], r["source_index"]) for r in rows] == expected,
                "initial audit must have exactly the ordered, unique 100+100+99 states")
        self.rows = {(r["side"], r["source_index"]): r for r in rows}
        self.cached_arrays = {}
        for side in ("new_python", "old_python"):
            self.add_arrays(side, validator.read_npz(args.previous/(side+"_high_precision.npz")), np.arange(100))
        for end in range(10, 91, 10):
            self.add_arrays("matlab", validator.read_npz(args.previous/f"matlab_checkpoint_{end:04d}.npz"), np.arange(end-10, end))
        require(len(self.cached_arrays) == 290, "must inherit exactly 290 complete array states")
        self.precision_rows = self.recover_precision()
        for key, row in self.rows.items():
            self.check_cached_gates(key, row)

    def add_arrays(self, side, arrays, expected_indices):
        require(set(arrays) == set(ARRAY_KEYS), f"unexpected cached array schema: {side}")
        require(np.array_equal(arrays["source_index"], expected_indices), "checkpoint index gap or overlap")
        count, ndof, ne = len(expected_indices), len(self.fixture["F0"]), len(self.fixture["connectivity"])
        shapes = dict(internal=(count, ndof), residual=(count, ndof), reaction=(count, ndof),
                      J=(count, ne, 9), material_energy=(count, ne))
        for field in ARRAY_KEYS:
            require(arrays[field].shape == shapes.get(field, (count,)), f"cached {field} shape invalid")
        for offset, index in enumerate(expected_indices):
            key = (side, int(index))
            require(key not in self.cached_arrays, "duplicate numerical cache state")
            row = self.rows[key]
            for field in ("source_index", "load_multiplier", "original_target", "original_target_index"):
                require(arrays[field][offset].item() == row[field], f"cached row/array disagreement: {key}/{field}")
            require(float(arrays["J"][offset].min()) == float(Decimal(row["high_precision_minimum_J"])),
                    f"cached minimum J differs from precise row: {key}")
            self.cached_arrays[key] = {field: arrays[field][offset] for field in ARRAY_KEYS}

    def recover_precision(self):
        rows = []
        for index in self.spec["path_validation"]["crosscheck_indices"]:
            path = self.args.previous/f"precision_crosscheck_target_{index+1:03d}.npz"
            with np.load(path, allow_pickle=False) as archive:
                data = {k: archive[k] for k in archive.files}
            require(set(data) == {"source_index", "load_multiplier", "internal_50_decimal", "internal_80_decimal", "external_80_decimal", "free_dofs"},
                    "precision archive schema differs")
            level = float(self.fixture["targets"][index])
            require(data["source_index"].shape == () and int(data["source_index"]) == index and
                    data["load_multiplier"].shape == () and float(data["load_multiplier"]) == level and
                    np.array_equal(data["free_dofs"], self.free), "precision archive identity differs")
            vectors = {}
            for name in ("internal_50_decimal", "internal_80_decimal", "external_80_decimal"):
                require(data[name].dtype.kind == "U" and data[name].shape == self.fixture["F0"].shape,
                        "precision evidence must be finite Decimal strings of the full vector")
                vectors[name] = [Decimal(x) for x in data[name]]
                require(all(x.is_finite() for x in vectors[name]), "nonfinite Decimal precision evidence")
            with localcontext() as context:
                context.prec = 80
                external = [self.v.promote(level)*self.v.promote(x) for x in self.fixture["F0"]]
                require(external == vectors["external_80_decimal"], "saved 80-digit external force differs from exact current input")
                scale = self.v.dnorm(external)
            error = self.v.precision_error(vectors["internal_50_decimal"], vectors["internal_80_decimal"], scale, self.free)
            tolerance = self.spec["path_validation"]["crosscheck_force_tolerance"]
            passed = max(Decimal(error["full_relative_error_decimal"]), Decimal(error["free_relative_error_decimal"])) <= Decimal(tolerance)
            require(self.rows[("new_python", index)]["reference_precision_pass"] is passed,
                    "reconstructed precision decision differs from cached state")
            rows.append(dict(side="new_python", source_index=index, original_target_index=index,
                load_multiplier=level, lower_digits=50, higher_digits=80,
                tolerance_decimal=str(tolerance), status="pass" if passed else "fail", **error))
        return rows

    def check_cached_gates(self, key, row):
        """Reapply frozen criteria to the saved exact metrics, not status labels."""
        side, index = key
        path = self.side_data[side]
        level = float(path["levels"][index])
        require(row["load_multiplier"] == level == float(self.fixture["targets"][index]) and
                row["original_target"] is True and row["original_target_index"] == index and
                row["precision_digits"] == 50 and "exception" not in row, f"cached state identity invalid: {key}")
        require(row["stored_relative_residual"] == float(path["stored_residual"][index]) and
                row["production_internal_available"] is (path["internal"] is not None), "cached production input differs")
        limits, tol = self.spec["path_validation"], self.spec["original_cshape_tolerances"]
        with localcontext() as context:
            context.prec = 50
            scale = self.v.dnorm([self.v.promote(level)*self.v.promote(x) for x in self.fixture["F0"]])
        require(str(scale) == row["force_scale_decimal"], "cached normalization differs from exact current external force")
        gates = {
            "equilibrium_pass": Decimal(row["high_precision_relative_residual"]) <= self.v.decimal(limits["external_residual_tolerance"]),
            "positive_J_pass": Decimal(row["high_precision_minimum_J"]) > 0,
            "fixed_displacement_pass": row["fixed_displacement_max"] <= 1e-12*tol["domain"][0],
            "balance_pass": max(Decimal(row["high_precision_balance_relative_decimal"]), Decimal(row["stored_reaction_balance_relative_decimal"])) <= self.v.decimal(tol["global_force_balance_tolerance"]),
            "J_pass": row["J_relative_error"] <= tol["J_field_relative_tolerance"],
            "reaction_pass": row["reaction_relative_error"] <= tol["reaction_relative_tolerance"],
            "solid_energy_pass": row["solid_energy_relative_error"] <= tol["region_material_energy_relative_tolerance"],
            "medium_energy_pass": row["medium_energy_relative_error"] <= tol["region_material_energy_relative_tolerance"],
            "minimum_J_pass": row["minimum_J_absolute_error"] <= tol["min_J_absolute_tolerance"],
            "free_support_reaction_zero_pass": bool(np.all(path["reaction"][index][self.free] == 0.)),
        }
        require(row["fixed_displacement_max"] == float(np.max(np.abs(path["U"][index][self.fixed]), initial=0.)), "cached fixed displacement differs")
        evaluation = None if path["internal"] is None else max(
            Decimal(row["evaluation_full_relative_error_decimal"]), Decimal(row["evaluation_free_relative_error_decimal"])) <= self.v.decimal(limits["evaluation_error_tolerance"])
        require(row["evaluation_budget_pass"] is evaluation, "cached evaluation budget decision differs")
        for field, passed in gates.items():
            require(row[field] is passed, f"cached gate differs under unchanged criterion: {key}/{field}")
        require(row["independent_state_status"] == ("pass" if all(gates.values()) else "fail"), "cached base status differs")
        if side == "new_python":
            archived = float(np.linalg.norm((path["internal"][index]-level*self.fixture["F0"])[self.free]))/float(scale)
            require(archived == row["archived_internal_relative_residual"], "cached production force residual differs")
            stopping = max(row["stored_relative_residual"], archived) <= self.spec["internal_newton_tolerance"]
            require(row["internal_stopping_pass"] is stopping, "cached internal stopping differs")
            new_pass = all(gates.values()) and evaluation is True and stopping and row.get("reference_precision_pass", True)
            require(row["new_version_state_status"] == ("pass" if new_pass else "fail"), "cached new-version decision differs")
        else:
            require(row["new_version_state_status"] == "historical_audit_only", "historical state was promoted to new-version acceptance")

    def accept_row(self, row):
        key = (row["side"], row["source_index"])
        require(key not in self.seen, "resumed state evaluated or inherited twice")
        self.seen.add(key)
        if key in self.rows:
            old = {k: v for k, v in self.rows[key].items() if k != "wall_seconds"}
            new = {k: v for k, v in self.v.plain(row).items() if k != "wall_seconds"}
            require(old == new, f"resumed scientific row differs from initial audit: {key}")
            if key not in self.cached_arrays:
                self.overlap_checks.append(dict(side=key[0], source_index=key[1],
                    status="pass", comparison="all fields exactly equal except wall_seconds",
                    original_scientific_row_sha256=hashlib.sha256(canonical(old).encode()).hexdigest(),
                    recomputed_scientific_row_sha256=hashlib.sha256(canonical(new).encode()).hexdigest()))

    def final_checks(self):
        require(self.seen == {(side, i) for side in self.side_data for i in range(100)}, "final 300-state coverage incomplete")
        require([row["source_index"] for row in self.overlap_checks] == list(range(90, 99)), "nine overlapping states were not checked")
        for name, path in self.paths.items():
            require(sha256(path) == INPUT_SHA256[name], f"input changed during recovery: {name}")
        for path in self.cache_files:
            require(sha256(path) == self.cache_hashes[path.name], f"initial cache changed during recovery: {path.name}")

    def provenance(self):
        return dict(status="pass", previous_directory=str(self.args.previous.resolve()),
            previous_validation_status="incomplete", previous_exception_type="TimeoutError",
            previous_completed_row_count=299, inherited_complete_state_count=290,
            recomputed_state_count=10, recomputed_side="matlab", recomputed_source_indices=list(range(90, 100)),
            newly_completed_source_indices=[99], overlapping_recomputed_state_count=9,
            overlap_comparison_status="pass", overlap_comparisons=self.overlap_checks,
            inherited_gate_revalidation="All saved exact Decimal equilibrium/evaluation metrics and all base/new-version gate criteria reapplied without tolerance changes",
            precision_reconstruction="Original precision_error applied to three saved internal_50_decimal/internal_80_decimal vectors, normalized by exact external_80_decimal norm at precision 80",
            precision_high_precision_re_evaluations=0, high_precision_evaluations_this_resume=10,
            original_validator_sha256=VALIDATOR_SHA256, decimal_helper_sha256=HELPER_SHA256,
            cache_directory_sha256=CACHE_DIRECTORY_SHA256, cached_source_hashes=self.cache_hashes,
            frozen_input_hashes=INPUT_SHA256, prior_receipt=self.receipt, resource_amendment=self.amendment,
            prior_receipt_absolute_paths="provenance only; current reads use supplied CLI paths",
            process_limit_seconds=120, internal_deadline_seconds=110,
            scientific_criteria_changed=False, historical_path_statuses_modified=False,
            scheduling_source_sha256=self.transformed_sha256)


def replace_once(source, old, new):
    require(source.count(old) == 1, "original validator scheduling anchor changed")
    return source.replace(old, new, 1)


def prepare_scheduling_source(recovery):
    """Only scheduling is wrapped; setup, real HP body and summary stay original."""
    source = recovery.validator_path.read_text(encoding="utf-8")
    source = replace_once(source, "all_rows, precision_rows, exceptions, audits = [], [], [], {}",
                          "all_rows, precision_rows, exceptions, audits = [], list(_recovery.precision_rows), [], {}")
    source = replace_once(source, "    input_paths.append(helper_path)",
        "    input_paths.append(helper_path)\n    input_paths += [Path(_recovery.args.prior_receipt), Path(_recovery.args.resource_amendment), Path(_resume_file), *_recovery.cache_files]")
    source = replace_once(source, "if perf_counter()-begin > 590:",
                          "if perf_counter()-_recovery.begin > 110:")
    source = replace_once(source, "offline validation nearing its frozen 600-second process limit",
                          "recovery nearing its separately authorized 120-second process limit")
    start = "                try:\n                    u = path[\"U\"][source_index]"
    end = "                except Exception as exc:\n"
    require(source.count(start) == 1 and source.count(end) == 1, "per-state body boundaries changed")
    left = source.index(start)
    right = source.index(end, left)
    original_body = source[left+len("                try:\n"):right]
    prefix = ("                cache_key = (side, source_index)\n"
              "                try:\n"
              "                    if cache_key in _recovery.cached_arrays:\n"
              "                        row = dict(_recovery.rows[cache_key])\n"
              "                        for key in arrays:\n"
              "                            arrays[key].append(_recovery.cached_arrays[cache_key][key])\n"
              "                    else:\n")
    source = source[:left]+prefix+"".join("    "+line if line.strip() else line for line in original_body.splitlines(keepends=True))+source[right:]
    source = replace_once(source, '                row["wall_seconds"] = perf_counter()-state_started',
        '                if cache_key not in _recovery.cached_arrays:\n                    row["wall_seconds"] = perf_counter()-state_started\n                _recovery.accept_row(row)')
    source = replace_once(source, '    new_rows = [row for row in all_rows if row["side"] == "new_python"]',
        '    _recovery.final_checks()\n    new_rows = [row for row in all_rows if row["side"] == "new_python"]')
    source = replace_once(source, '    write_json(output/"summary.json", summary)',
        '    summary["resume_provenance"] = _recovery.provenance()\n    write_json(output/"summary.json", summary)')
    recovery.transformed_sha256 = hashlib.sha256(source.encode()).hexdigest()
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("fixture", "spec", "new-python", "old-python", "matlab", "comparison", "previous", "prior-receipt", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--resource-amendment", type=Path)
    args = parser.parse_args()
    if args.resource_amendment is None:
        args.resource_amendment = args.previous.parent/"resource_amendment_001.json"
    if args.output.exists():
        parser.error("--output must name a new directory; previous evidence is never modified")
    begin = perf_counter()
    validator, validator_path = load_validator()
    try:
        recovery = Recovery(args, validator, validator_path)
        source = prepare_scheduling_source(recovery)
        namespace = dict(__name__="hf2_resumed_scheduling", __file__=str(validator_path),
                         _recovery=recovery, _resume_file=str(Path(__file__).resolve()))
        exec(compile(source, str(validator_path)+"[recovery scheduling]", "exec"), namespace)
        summary = namespace["validate"](args)
        for index in (0, 49, 99):
            name = f"precision_crosscheck_target_{index+1:03d}.npz"
            shutil.copy2(args.previous/name, args.output/name)
        validator.write_json(args.output/"setup_checks.json", summary["setup_checks"])
        validator.write_json(args.output/"resume_provenance.json", summary["resume_provenance"])
        validator.write_json(args.output/"overlap_comparisons.json", recovery.overlap_checks)
        summary["wall_seconds_including_recovery_setup"] = perf_counter()-begin
        validator.write_json(args.output/"summary.json", summary)
    except Exception as exc:
        args.output.mkdir(parents=True, exist_ok=True)
        failure = dict(repaired_python_numerical_closure_status="not_pass", validation_status="incomplete",
            exception_type=type(exc).__name__, message=str(exc), wall_seconds=perf_counter()-begin,
            note="Original audit, paths and frozen scientific criteria remain unchanged; recovery outputs are separate")
        validator.write_json(args.output/"validation_failure.json", failure)
        print(json.dumps(failure, indent=2), flush=True)
        return 1
    print(json.dumps({key: summary[key] for key in ("repaired_python_numerical_closure_status", "total_evaluated_states",
        "new_python_original_targets", "wall_seconds_including_recovery_setup")}, indent=2), flush=True)
    return 0 if summary["repaired_python_numerical_closure_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
