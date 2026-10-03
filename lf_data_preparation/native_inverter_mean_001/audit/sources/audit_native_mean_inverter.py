"""New inverter identity/clock wrapper around the frozen mean audit mathematics.

The inherited run_state is unchanged: every accepted state receives fresh
HP80/120, exhaustive local/global force and direction checks, exact scatter,
full saved CSC assembly and the original mean/KKT/physical gates. No gripper
identity is simulated, and no frozen source or earlier evidence is rewritten.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
import argparse
import ast
from decimal import Decimal
import hashlib
from pathlib import Path
import shutil

CORE_PINS = {
    "audit_native_mean.py": "331eb1d5406b6d6538d838da823e214201b5ec26c8fac9f7f0bc77f23b8a1678",
    "audit_native_force.py": "cd317914cba2e3ad2f5ec5bf5b857804c3406313ab6a433bd1d7b395872ee8bb",
    "hf4_split_precision_reference.py": "308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2",
    "hf2_precision_reference.py": "97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55",
}
# Verify the inherited code and its pure/reference dependencies before imports.
for _name, _pin in CORE_PINS.items():
    if hashlib.sha256(Path(__file__).with_name(_name).read_bytes()).hexdigest() != _pin:
        raise ValueError("Frozen inherited audit dependency differs: "+_name)

import numpy as np
from audit_native_mean import Audit as CoreAudit, GATES, RSS_LIMIT
from audit_native_force import (canonical_hash, npz, read, require, same_arrays, sha,
    verify_descriptor, verify_fields, write)

BASELINE = "3f0c45d0554a340217bdbfe504b68c445008a06b"
ORIGINAL_INPUT_PINS = {
    "geometry_file_sha256": "23adf44ea8164fb103998ab97363747540a11ef7bb589ae81aa2fde23ff57eee",
    "geometry_npz_sha256": "1911362efaa5b6c5104af0cecf95310f262b129f3e0cd2a1c648cf550b756132",
    "prior_model_sha256": "321a10e0d46149cee9d17caf40dd1819c810ec9498d74c8882da1e3146aab9c6",
    "prior_task_sha256": "5d488f275515b77e37c07ef57c3ebda71f706ba498cec20f72261400408bfe65",
}
GEOMETRY_ID = "2e2bb3466ade06f920dfbb92577ccbe46106acec430837bac8e1a30b8083527a"
GEOMETRY_DESCRIPTOR_SHA = "31c2e8c9f8691f9f69aebeafec6b88fa3458556165bca35765402eaab1764397"
OLD_RECEIPT_SHA = "b488b170abd89ebda737a15c5211da9d8c77f706936aaccbea429ae737f9559c"
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.001/16, time_limit_seconds=180.)


class InverterAudit(CoreAudit):
    # run_state, check, gates, equation helpers and all mathematical comparisons
    # are inherited directly, including full local reference serialization.
    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "Independent inverter mean audit time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Independent inverter mean audit sampled RSS exceeds 8 GiB")

    def lifecycle(self, status, error=None):
        write(self.output/"lifecycle.json", dict(status=status, error=error,
            elapsed_seconds=perf_counter()-STARTED, HP_calls_started=self.hp_started,
            HP_calls_completed=self.hp_completed, checks_completed=self.checks,
            accepted_states_completed=len(self.rows), sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            stop_policy="First failure stops; no retry, repair, production evaluation or solve"))

    def load(self):
        inventory_file, receipt_file = (self.stage/name for name in ("input_inventory.json", "execution_receipt.json"))
        self.bind(inventory_file)
        self.bind(receipt_file)
        inventory, receipt = read(inventory_file), read(receipt_file)
        row = inventory["case"]
        self.check(inventory["schema_version"] == "native-mean-input-inventory-1.0"
            and inventory["baseline_commit"] == BASELINE and row["alias"] == "inverter_canonical"
            and row["targets_mm"] == [0., .001] and row["geometry_id"] == GEOMETRY_ID
            and (row["elements"], row["dofs"], row["fixed_DOFs"], row["free_DOFs"]) == (3200, 6642, 89, 6553)
            and inventory["settings"] == SETTINGS
            and all(row[key] == pin for key, pin in ORIGINAL_INPUT_PINS.items()), "Wrong real coarse inverter identity")
        self.check(receipt["schema_version"] == "native-mean-execution-1.0" and receipt["baseline_commit"] == BASELINE
            and receipt["status"] == "pass" and receipt["invocations"] == 1
            and receipt["input_inventory_sha256"] == sha(inventory_file), "Production invocation/inventory differs")
        self.check(len(receipt["sources"]) == 37
            and len({Path(name).name for name in receipt["sources"]}) == 37, "Expected 37 unique source capsule filenames")
        old_receipt_file = self.repo/"lf_data_preparation/native_mean_001/execution_receipt.json"
        self.bind(old_receipt_file, OLD_RECEIPT_SHA)
        old_receipt = read(old_receipt_file)
        self.check(old_receipt["status"] == "pass" and len(old_receipt["sources"]) == 33
            and all(receipt["sources"][name] == pin for name, pin in old_receipt["sources"].items()),
            "The original 33 frozen gripper sources changed")
        for name, expected in receipt["sources"].items():
            capsule = Path(name).name
            self.bind(self.repo/name, expected)
            self.bind(self.stage/"sources"/capsule, expected)
            shutil.copyfile(self.repo/name, self.output/"sources"/capsule)
            self.bind(self.output/"sources"/capsule, expected)
            self.sources[name] = expected
        for name, expected in receipt["inputs"].items():
            self.bind(self.repo/name, expected)
        for name, expected in CORE_PINS.items():
            path = Path(__file__).with_name(name)
            relative = path.relative_to(self.repo).as_posix()
            self.check(receipt["sources"][relative] == expected, "Inherited/reference source binding differs")
            self.bind(path, expected)
        self.check(Path(__file__).relative_to(self.repo).as_posix() in self.sources, "New identity wrapper is not source-bound")
        for path in (inventory_file, receipt_file):
            shutil.copyfile(path, self.output/path.name)
        original = Path(__file__).with_name("run_split_average_demo.py")
        self.bind(original, receipt["sources"][original.relative_to(self.repo).as_posix()])
        syntax = ast.parse(original.read_text(encoding="utf-8"))
        assignments = [node.value for node in syntax.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "GATES" for target in node.targets)]
        original_gates = {item.arg: ast.literal_eval(item.value) for item in assignments[0].keywords}
        self.check(len(assignments) == 1 and original_gates == GATES == inventory["gates"], "Original HF3 gates changed")
        self.origin = self.stage/row["result_directory"]
        self.result_file = self.origin/"result.json"
        self.bind(self.result_file, receipt["result_sha256"])
        result = read(self.result_file)
        verify_descriptor(result)
        self.check(result["schema_version"] == "hf-native-mean-result-1.0" and result["status"] == "success"
            and result["production_converged"] is True and result["target_reached"] is True
            and result["task_target_executed"] is True and result["targets_mm"] == row["targets_mm"]
            and result["task_target_mm"] == .001 and result["target_origin"] == 0.
            and result["lift_origin_zero"] is True and result["lift_shape_zero"] is True
            and result["settings"] == inventory["settings"] and result["backend"] == "numpy"
            and result["matrix_units"] == "N/mm" and result["k_out_N_per_mm"] == 0.
            and result["force_scale_per_length"] == 20. and result["save_force_calls"] == result["save_tangent_calls"] == 0
            and result["equilibrium_qualified"] is False and result["independent_HP_qualified"] is False
            and result["HF_qualified"] is False and result["failure"] is None,
            "Production path/settings/qualification changed")
        counts = result["call_counts"]
        self.check(counts["force_calls"] == counts["force_calls_completed"]
            and counts["tangent_calls"] == counts["tangent_calls_completed"]
            and counts["solver_invocations"] == 1 and counts["HP_calls"] == counts["JIT_calls"] == 0,
            "Production mechanics invocation counts differ")
        self.check(receipt["call_counts"] == counts and receipt["force_calls"] == counts["force_calls"]
            and receipt["tangent_calls"] == counts["tangent_calls"] and receipt["solver_calls"] == 1
            and receipt["HP_calls"] == receipt["JIT_calls"] == 0
            and receipt["save_force_calls"] == receipt["save_tangent_calls"] == 0,
            "Production receipt counters differ from returned API counters")
        for name, expected in result["mechanics_source_sha256"].items():
            self.check(receipt["sources"][name] == expected, "Mechanics source binding differs")
        for key, pin in (("geometry_file", "geometry_file_sha256"), ("geometry_npz_file", "geometry_npz_sha256"),
            ("prior_model_file", "prior_model_sha256"), ("task_file", "task_file_sha256"),
            ("prior_task_file", "prior_task_sha256"), ("direction_file", "direction_file_sha256"),
            ("lifting_file", "lifting_file_sha256")):
            self.bind(self.repo/row[key], row[pin])
        model_file, model_json_file = (self.origin/result["model"][key] for key in ("arrays_path", "descriptor_path"))
        self.bind(model_file, result["model"]["arrays_sha256"])
        self.bind(model_file, receipt["model_sha256"])
        self.bind(model_json_file, result["model"]["descriptor_file_sha256"])
        model, metadata = npz(model_file), read(model_json_file)
        verify_descriptor(metadata)
        verify_fields(model, metadata["arrays"]["fields"])
        same_arrays(model, npz(self.repo/row["prior_model_file"]), "Previously reviewed intrinsic inverter model")
        task, prior_task = (read(self.repo/row[key]) for key in ("task_file", "prior_task_file"))
        physical_keys = set(prior_task)-{"task_id", "purpose", "parameter_origin", "description", "input"}
        self.check(all(task[key] == prior_task[key] for key in physical_keys)
            and task["input"] == dict(prior_task["input"], target_mm=.001)
            and task["case_family"] == "inverter" and task["workpiece"] is None,
            "New explicit inverter TEST changed previously reviewed physics")
        self.check(len(model) == 23 and metadata["schema_version"] == "hf-native-project-model-1.0"
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == sha(model_file) and metadata["task"] == task
            and metadata["task_sha256"] == canonical_hash(task) == result["task_sha256"], "Ordinary task/model declaration differs")
        source = metadata["source_geometry"]
        expected_source = dict(source, snapshot={key: "model/"+path for key, path in source["snapshot"].items()})
        self.check(result["source_geometry"] == expected_source and source["geometry_id"] == GEOMETRY_ID
            and source["descriptor_file_sha256"] == row["geometry_file_sha256"]
            and source["arrays_sha256"] == row["geometry_npz_sha256"]
            and source["descriptor_sha256"] == GEOMETRY_DESCRIPTOR_SHA
            == read(self.repo/row["geometry_file"])["descriptor_sha256"], "Source inverter geometry/path context differs")
        for key, pin in (("descriptor", "geometry_file_sha256"), ("arrays", "geometry_npz_sha256")):
            self.bind(self.origin/expected_source["snapshot"][key], row[pin])
        edofs = (2*model["connectivity"][:, :, None]+np.arange(2)).reshape(-1, 8)
        self.check(np.array_equal(edofs, model["edofs"]) and len(edofs) == 3200
            and np.array_equal(np.setdiff1d(np.arange(6642), model["fixed_dofs"]), model["free_dofs"])
            and len(model["fixed_dofs"]) == 89, "Independent inverter element/fixed/free indexing differs")
        self.check(np.flatnonzero(model["b_in"]).tolist() == [6156, 6318, 6480]
            and model["b_in"][[6156, 6318, 6480]].tolist() == [.25, .5, .25]
            and np.flatnonzero(model["b_out"]).tolist() == [6316, 6478, 6640]
            and model["b_out"][[6316, 6478, 6640]].tolist() == [-.25, -.5, -.25], "Actual +x input/-x output ports differ")
        direction_arrays, lifting = (npz(self.repo/row[key]) for key in ("direction_file", "lifting_file"))
        direction = direction_arrays["direction"]
        expected_direction = model["b_in"]/np.max(abs(model["b_in"]))
        expected_direction[model["fixed_dofs"]] = 0.
        self.check(direction_arrays.keys() == {"direction", "multiplier_direction"}
            and direction.dtype == np.dtype("float64") and direction.shape == (6642,)
            and direction.tobytes() == expected_direction.tobytes()
            and hashlib.sha256(direction.tobytes()).hexdigest() == row["direction_array_sha256"]
            and float(direction_arrays["multiplier_direction"]) == 0.
            and lifting.keys() == {"lift_origin", "lift_shape"}
            and all(value.dtype == np.dtype("float64") and value.shape == (6642,) and np.count_nonzero(value) == 0
                    for value in lifting.values()), "Direction or zero-lift declaration differs")
        states = result["states"]
        self.check(len(states) == result["accepted_states"] and states and receipt["accepted_states"] == len(states)
            and receipt["state_sha256"] == [item["state_sha256"] for item in states]
            and [item["d"] for item in states if item["is_original_target"]] == row["targets_mm"]
            and states[0]["d"] == 0. and states[-1]["d"] == .001
            and all(a["d"] < b["d"] for a, b in zip(states, states[1:]))
            and all(item["target_origin"] == 0. and item["physical_mean_target_mm"] == item["d"] for item in states),
            "Accepted inverter path does not cover every declared target in order")
        self.model, self.edofs, self.direction = model, edofs, direction
        self.inventory, self.receipt, self.result = inventory, receipt, result
        self.checkpoint()

    def run(self):
        self.checkpoint()
        self.load()
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        self.reference_class = DecimalSplitQ1Reference
        self.checkpoint()
        for index, row in enumerate(self.result["states"]):
            self.run_state(index, row)
        self.check(self.hp_started == self.hp_completed == 2*len(self.result["states"]), "Fresh reference coverage/calls differ")
        for path, expected in self.bindings.items():
            self.check(sha(path) == expected, "Bound source/input changed: "+str(path))
        self.checkpoint()
        summary = dict(schema_version="native-mean-independent-audit-1.0", status="pass", alias="inverter_canonical",
            case_family="inverter", input_reference_direction=[1., 0.], output_reference_direction=[-1., 0.],
            input_port_dofs=[6156, 6318, 6480], output_port_dofs=[6316, 6478, 6640],
            input_port_weights=[.25, .5, .25], output_port_weights=[-.25, -.5, -.25],
            accepted_states=len(self.rows), states=self.rows, result_sha256=sha(self.result_file),
            checks_completed=self.checks, HP_calls_started=self.hp_started, HP_calls_completed=self.hp_completed,
            HP_matrix_columns_exhaustively_checked=False, full_element_and_DOF_coverage=True,
            gates=GATES, global_scatter_precision=3000, global_scatter_inexact_trap=True,
            reference_scope="All accepted inverter states, elements and real DOFs; fixed-lift v=b_in/max(abs(b_in)), deltaR=0",
            qualification="Independent small coarse no-workpiece inverter TEST only; no H2/H3, fine-grid or full-task qualification",
            inherited_run_state_source_sha256=CORE_PINS["audit_native_mean.py"],
            candidate_force_calls=0, tangent_calls=0, solver_calls=0,
            source_bindings=self.sources, input_bindings={path.relative_to(self.repo).as_posix(): value for path, value in self.bindings.items()},
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT)
        write(self.output/"summary.json", summary)
        self.checkpoint()
        self.lifecycle("pass")
        self.checkpoint()
        print(dict(status="pass", accepted_states=len(self.rows), HP_calls=self.hp_completed,
            checks_completed=self.checks, elapsed_seconds=perf_counter()-STARTED), flush=True)
        self.checkpoint()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=180.)
    args = parser.parse_args()
    require(np.isfinite(args.time_limit) and 0 < args.time_limit <= 180., "Time limit must be in (0,180]")
    audit = InverterAudit(args)
    try:
        audit.run()
    except Exception as error:
        audit.lifecycle("not_pass", repr(error))
        write(audit.output/"summary.json", dict(schema_version="native-mean-independent-audit-1.0", status="not_pass",
            alias="inverter_canonical", error=repr(error), states=audit.rows, accepted_states=len(audit.rows), checks_completed=audit.checks,
            HP_calls_started=audit.hp_started, HP_calls_completed=audit.hp_completed,
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__":
    main()
