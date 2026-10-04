"""Full saved-state HP audit of the declared coarse fixed-square loading cycle.

The frozen CoreAudit.run_state supplies every original force, tangent, CSC,
KKT and equilibrium comparison. This wrapper binds the new task and fixed
overlay, then projects those same full references onto workpiece reactions.
No production mechanics or model constructor is imported or evaluated.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
import argparse
import ast
from decimal import Decimal, Inexact, localcontext
import gzip
import hashlib
import json
from pathlib import Path
import shutil

CORE_PINS = {
    "audit_native_mean.py": "331eb1d5406b6d6538d838da823e214201b5ec26c8fac9f7f0bc77f23b8a1678",
    "audit_native_force.py": "cd317914cba2e3ad2f5ec5bf5b857804c3406313ab6a433bd1d7b395872ee8bb",
    "hf4_split_precision_reference.py": "308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2",
    "hf2_precision_reference.py": "97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55",
}
for _name, _pin in CORE_PINS.items():
    if hashlib.sha256(Path(__file__).with_name(_name).read_bytes()).hexdigest() != _pin:
        raise ValueError("Frozen audit dependency differs: "+_name)

import numpy as np
from audit_native_mean import Audit as CoreAudit, COMPONENTS, FORCE_KEYS, GATES, RSS_LIMIT, compare
from audit_native_force import (canonical_hash, norm, npz, read, require, same_arrays,
    sha, verify_descriptor, verify_fields, write, write_gzip)

BASELINE = "a658945ba4cc629c311fd6f65a1bced6262e1412"
PINS = dict(geometry_file_sha256="8d831fd3f1a034a3cd1948415c3f9758a2c6b94507973b7dc8c409266fec78e6",
    geometry_npz_sha256="f7b23e8d16aedb0ebb5b7dc3954b7b59a80f99b6d3859046aa16904a610d6282",
    prior_model_sha256="887279fc3d11c39af305c8ba96c34d71bd10de56f3cf464c917f9672eab46a79",
    prior_task_sha256="67d21a63898b2f31962f3e930bc2cb17e36b2813671dfa413c85c7834e6c9b63")
GEOMETRY_ID = "d4e82cfd629e37f7d0c85aed672ab5df228314147cf5db59aeabb279cee5d91d"
GEOMETRY_DESCRIPTOR_SHA = "8c5c315e7328888a6ba16b28d5def1712e2ea5ddae21cfa97f99f06396e7977b"
TARGETS = [0., .1, 0.]
BODY = dict(kind="fixed_rigid", shape="square", center_mm=[70., 40.], side_mm=16., fixed_components=[0, 1])
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.1/16, time_limit_seconds=600.)
LIMITS = dict(production_seconds=600, reference_seconds=240, sampled_RSS_bytes=RSS_LIMIT,
    production_outer_seconds=660, reference_outer_seconds=300, view_outer_seconds=120)


def read_gzip(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def vector_sum(values, dofs):
    """Exact sum of the saved finite Decimal values over unique component DOFs."""
    with localcontext() as context:
        context.prec = 3000
        context.traps[Inexact] = True
        return [sum((Decimal(values[i]) for i in dofs if i % 2 == c), Decimal(0)) for c in (0, 1)]


class WorkpieceCycleAudit(CoreAudit):
    # The mathematical run_state method is inherited, without override or copy.
    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "Workpiece cycle reference time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Workpiece cycle sampled RSS exceeds 8 GiB")

    def lifecycle(self, status, error=None):
        write(self.output/"lifecycle.json", dict(status=status, error=error,
            elapsed_seconds=perf_counter()-STARTED, HP_calls_started=self.hp_started,
            HP_calls_completed=self.hp_completed, checks_completed=self.checks,
            accepted_states_completed=len(self.rows), sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            stop_policy="First failure stops; no retry, production evaluation or solve"))

    def load(self):
        inventory_file, receipt_file, freeze_file = (self.stage/name for name in
            ("input_inventory.json", "execution_receipt.json", "source_freeze.json"))
        self.bind(inventory_file)
        self.bind(receipt_file)
        inventory, receipt = read(inventory_file), read(receipt_file)
        row = inventory["case"]
        self.check(inventory["schema_version"] == "native-workpiece-cycle-input-inventory-1.0"
            and inventory["baseline_commit"] == BASELINE and self.stage.name == "coarse_square_cycle_001"
            and row["alias"] == "gripper_coarse_square" and row["source_alias"] == "gripper_canonical"
            and row["targets_mm"] == TARGETS and row["geometry_id"] == GEOMETRY_ID
            and (row["elements"], row["dofs"], row["fixed_DOFs"], row["free_DOFs"]) == (3200, 6642, 376, 6266)
            and all(row[key] == value for key, value in PINS.items())
            and inventory["settings"] == SETTINGS and inventory["execution_limits"] == LIMITS,
            "Wrong declared coarse fixed-square cycle identity/settings")
        self.bind(freeze_file, inventory["source_freeze_sha256"])
        freeze = read(freeze_file)
        self.check(freeze["schema_version"] == "native-workpiece-cycle-source-freeze-1.0"
            and receipt["sources"] == freeze["sources"]
            and len({Path(name).name for name in freeze["sources"]}) == len(freeze["sources"]),
            "Frozen source closure or unique capsule names differ")
        self.check(receipt["schema_version"] == "native-mean-execution-1.0" and receipt["status"] == "pass"
            and receipt["baseline_commit"] == BASELINE and receipt["invocations"] == 1
            and receipt["seconds_limit"] == 600 and receipt["sampled_RSS_limit_bytes"] == RSS_LIMIT
            and receipt["input_inventory_sha256"] == sha(inventory_file)
            and receipt["source_freeze_sha256"] == sha(freeze_file)
            and receipt["sources_unchanged"] is True and receipt["inputs_unchanged"] is True,
            "Production invocation/frozen bindings differ")
        for name, expected in receipt["sources"].items():
            self.bind(self.repo/name, expected)
            self.bind(self.stage/"sources"/Path(name).name, expected)
            shutil.copyfile(self.repo/name, self.output/"sources"/Path(name).name)
            self.bind(self.output/"sources"/Path(name).name, expected)
            self.sources[name] = expected
        for name, expected in receipt["inputs"].items():
            self.bind(self.repo/name, expected)
        for name, expected in CORE_PINS.items():
            path = Path(__file__).with_name(name)
            self.check(self.sources[path.relative_to(self.repo).as_posix()] == expected, "Inherited/reference source changed")
        self.check(Path(__file__).relative_to(self.repo).as_posix() in self.sources, "New checker is not source-bound")
        for path in (inventory_file, receipt_file, freeze_file):
            shutil.copyfile(path, self.output/path.name)
        original = Path(__file__).with_name("run_split_average_demo.py")
        self.bind(original, self.sources[original.relative_to(self.repo).as_posix()])
        assignments = [node.value for node in ast.parse(original.read_text(encoding="utf-8")).body
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "GATES" for t in node.targets)]
        self.check(len(assignments) == 1 and
            {item.arg: ast.literal_eval(item.value) for item in assignments[0].keywords} == GATES == inventory["gates"],
            "Original HF3 gates changed")
        for key, pin in (("geometry_file", "geometry_file_sha256"), ("geometry_npz_file", "geometry_npz_sha256"),
            ("prior_model_file", "prior_model_sha256"), ("prior_task_file", "prior_task_sha256"),
            ("task_file", "task_file_sha256"), ("direction_file", "direction_file_sha256")):
            self.bind(self.repo/row[key], row[pin])
        self.origin = self.stage/row["result_directory"]
        self.result_file = self.origin/"result.json"
        self.bind(self.result_file, receipt["result_sha256"])
        result = read(self.result_file)
        verify_descriptor(result)
        self.check(result["schema_version"] == "hf-native-mean-result-1.1" and result["status"] == "success"
            and all(result[key] is True for key in ("production_converged", "target_reached", "task_target_executed",
                "path_completed", "loading_peak_reached", "unload_endpoint_reached", "lift_origin_zero", "lift_shape_zero"))
            and result["path_kind"] == "ordered_cycle" and result["targets_mm"] == TARGETS
            and result["task_target_mm"] == .1 and result["reached_displacement"] == result["target_origin"] == 0.
            and result["settings"] == SETTINGS and result["backend"] == "numpy"
            and result["matrix_units"] == "N/mm" and result["k_out_N_per_mm"] == 0.
            and result["force_scale_per_length"] == 20. and result["failure"] is None
            and result["save_force_calls"] == result["save_tangent_calls"] == 0
            and all(result[key] is False for key in ("equilibrium_qualified", "independent_HP_qualified", "HF_qualified")),
            "Production cycle/settings/scope differ")
        counts = result["call_counts"]
        self.check(counts["force_calls"] == counts["force_calls_completed"]
            and counts["tangent_calls"] == counts["tangent_calls_completed"] and counts["solver_invocations"] == 1
            and counts["HP_calls"] == counts["JIT_calls"] == 0 and receipt["call_counts"] == counts
            and receipt["force_calls"] == counts["force_calls"] and receipt["tangent_calls"] == counts["tangent_calls"]
            and receipt["solver_calls"] == 1 and receipt["HP_calls"] == receipt["JIT_calls"] == receipt["LF_imports"] == 0
            and receipt["save_force_calls"] == receipt["save_tangent_calls"] == 0,
            "Production completed counters differ")
        self.check(all(self.sources[name] == pin for name, pin in result["mechanics_source_sha256"].items()),
            "Mechanics sources differ from frozen closure")
        model_file, metadata_file = (self.origin/result["model"][key] for key in ("arrays_path", "descriptor_path"))
        self.bind(model_file, result["model"]["arrays_sha256"])
        self.bind(model_file, receipt["model_sha256"])
        self.bind(metadata_file, result["model"]["descriptor_file_sha256"])
        model, metadata, prior = npz(model_file), read(metadata_file), npz(self.repo/row["prior_model_file"])
        prior_metadata_file = (self.repo/row["prior_model_file"]).with_suffix(".json")
        self.bind(prior_metadata_file)
        prior_metadata = read(prior_metadata_file)
        verify_descriptor(metadata)
        verify_descriptor(prior_metadata)
        self.check(prior_metadata["arrays"]["sha256"] == row["prior_model_sha256"], "Prior model descriptor differs")
        verify_fields(model, metadata["arrays"]["fields"])
        intrinsic = set(prior)-{"fixed_dofs", "free_dofs"}
        same_arrays({key: model[key] for key in intrinsic}, {key: prior[key] for key in intrinsic}, "All original 21 intrinsic arrays")
        task, prior_task = (read(self.repo/row[key]) for key in ("task_file", "prior_task_file"))
        changed = {"schema_version", "task_id", "purpose", "parameter_origin", "description", "input", "workpiece", "path"}
        self.check(set(task) == set(prior_task)|{"path"}
            and all(task[key] == prior_task[key] for key in set(prior_task)-changed)
            and task["schema_version"] == "hf-native-project-task-1.1" and task["case_family"] == "gripper"
            and task["input"] == dict(prior_task["input"], target_mm=.1) and task["workpiece"] == BODY
            and task["path"] == dict(kind="ordered_cycle", targets_mm=TARGETS)
            and metadata["schema_version"] == "hf-native-project-model-1.1" and metadata["task"] == task
            and metadata["task_sha256"] == result["task_sha256"] == receipt["task_sha256"] == canonical_hash(task)
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == sha(model_file), "Task/model overlay identity differs")
        self.check(all(metadata[key] == prior_metadata[key] for key in ("grid", "model_extent", "units", "material",
            "quadrature", "element_node_order", "dof_order", "analysis_grid_policy", "native_geometry_preserved",
            "qualification", "constraints_applied", "material_assigned", "task_created", "response_evaluated")),
            "Original grid/material/model semantics changed")
        source = metadata["source_geometry"]
        expected_source = dict(source, snapshot={key: "model/"+path for key, path in source["snapshot"].items()})
        self.check(source == prior_metadata["source_geometry"] and result["source_geometry"] == expected_source
            and source["geometry_id"] == GEOMETRY_ID and source["descriptor_sha256"] == GEOMETRY_DESCRIPTOR_SHA
            and source["descriptor_file_sha256"] == row["geometry_file_sha256"]
            and source["arrays_sha256"] == row["geometry_npz_sha256"], "Source geometry identity differs")
        for key, pin in (("descriptor", "geometry_file_sha256"), ("arrays", "geometry_npz_sha256")):
            self.bind(self.origin/expected_source["snapshot"][key], row[pin])
        coords, conn = model["coordinates"], model["connectivity"]
        centres = coords[conn].mean(axis=1)
        cells = np.flatnonzero((centres[:, 0] >= 62.) & (centres[:, 0] <= 78.) & (centres[:, 1] >= 32.) & (centres[:, 1] <= 40.))
        nodes = np.unique(conn[cells])
        dofs = (2*nodes[:, None]+np.arange(2)).ravel()
        groups = {name: prior_metadata["region_metadata"][name]["dofs"]
                  for name in ("support", "entity_symmetry", "background_symmetry")}
        overlap = np.intersect1d(dofs, groups["background_symmetry"])
        extras = dict(workpiece_cells=cells, workpiece_nodes=nodes, workpiece_dofs=dofs,
            workpiece_background_symmetry_overlap_dofs=overlap)
        self.check(len(prior) == 23 and set(model) == set(prior)|set(extras)
            and (len(cells), len(nodes), len(dofs), len(overlap)) == (128, 153, 306, 17)
            and all(model[key].dtype == np.dtype("int64") and np.array_equal(model[key], value) for key, value in extras.items())
            and np.all(npz(self.repo/row["geometry_npz_file"])["passive_void"].ravel()[cells])
            and not np.intersect1d(nodes, model["solid_nodes"]).size,
            "Independent fixed-square cells/nodes/DOFs differ")
        regions, body = metadata["region_metadata"], metadata["region_metadata"]["workpiece"]
        self.check(all(regions[name] == prior_metadata["region_metadata"][name] for name in groups)
            and regions["ports"] == prior_metadata["region_metadata"]["ports"]
            and regions["source_background"] == prior_metadata["region_metadata"]["source_background"]
            and body["definition"] == BODY and all(body[name] == value.tolist() for name, value in
                (("cells", cells), ("nodes", nodes), ("dofs", dofs), ("background_symmetry_overlap_dofs", overlap)))
            and body["initial_gaps_mm"] == dict(left=2., bottom=2.)
            and regions["effective_boundary"] == dict(task_sha256=canonical_hash(task),
                fixed_dofs_sha256=hashlib.sha256(model["fixed_dofs"].astype("<i8").tobytes()).hexdigest(),
                workpiece_constraint_overlay=True, source_geometry_masks_preserved=True,
                source_material_arrays_preserved=True,
                material_phase_classification="original mechanism solid and original medium; workpiece is a kinematic overlay"),
            "Workpiece or effective boundary metadata differs")
        fixed = np.union1d(prior["fixed_dofs"], dofs)
        edofs = (2*conn[:, :, None]+np.arange(2)).reshape(-1, 8)
        self.check(len(fixed) == 376 and np.array_equal(fixed, model["fixed_dofs"])
            and np.array_equal(np.setdiff1d(np.arange(6642), fixed), model["free_dofs"])
            and np.array_equal(edofs, model["edofs"]) and regions["fixed_dofs"] == fixed.tolist()
            and np.flatnonzero(model["b_in"]).tolist() == [6156, 6318, 6480]
            and np.flatnonzero(model["b_out"]).tolist() == [4697, 4859, 5021]
            and model["b_in"][[6156, 6318, 6480]].tolist() == model["b_out"][[4697, 4859, 5021]].tolist() == [.25, .5, .25],
            "Merged fixed/free indexing or actual signed ports differ")
        expected_counts = dict(prior_metadata["region_metadata"]["counts"], fixed_dofs=376, free_dofs=6266)
        self.check(regions["counts"] == result["counts"] == expected_counts
            and regions["solid_constraint_dofs"] == prior_metadata["region_metadata"]["solid_constraint_dofs"]
            and (body["selected_cells"], body["incident_nodes"], body["fixed_dofs"]) == (128, 153, 306),
            "Original material extent or declared overlay counts differ")
        direction_arrays = npz(self.repo/row["direction_file"])
        direction = direction_arrays["direction"]
        expected_direction = model["b_in"]/np.max(abs(model["b_in"]))
        expected_direction[fixed] = 0.
        self.check(direction_arrays.keys() == {"direction", "multiplier_direction"}
            and direction.dtype == np.dtype("float64") and direction.shape == (6642,)
            and direction.tobytes() == expected_direction.tobytes()
            and hashlib.sha256(direction.tobytes()).hexdigest() == row["direction_array_sha256"]
            and float(direction_arrays["multiplier_direction"]) == 0., "Declared reference direction differs")
        states = result["states"]
        originals = [item for item in states if item["is_original_target"]]
        self.check(len(states) >= 3 and len(states) == result["accepted_states"] == receipt["accepted_states"]
            and receipt["state_sha256"] == [item["state_sha256"] for item in states]
            and [item["d"] for item in originals] == TARGETS
            and [item["original_target_index"] for item in originals] == [0, 1, 2]
            and all(item["target_origin"] == 0. and item["physical_mean_target_mm"] == item["d"] for item in states)
            and states[0]["leg"] == "origin" and states[0]["d"] == states[-1]["d"] == 0.,
            "Actual accepted cycle does not retain all ordered original targets")
        for previous, current in zip(states, states[1:]):
            leg = current["original_target_index"]
            self.check(leg in (1, 2) and current["leg"] == ("loading" if leg == 1 else "unloading")
                and leg >= previous["original_target_index"]
                and current["original_target_displacement"] == TARGETS[leg]
                and (previous["d"] < current["d"] <= .1 if leg == 1 else 0. <= current["d"] < previous["d"])
                and 0 <= current["bisection_depth"] <= SETTINGS["max_bisections"], "Accepted loading/unloading leg differs")
        self.model, self.edofs, self.direction = model, edofs, direction
        self.inventory, self.receipt, self.result, self.metadata = inventory, receipt, result, metadata
        self.workpiece_dofs, self.groups = dofs, groups
        self.checkpoint()

    def workpiece_checks(self, index, row):
        record = self.rows[-1]
        directory = self.output/f"accepted_{index:03d}"
        for key in ("global_references", "equations"):
            self.bind(self.output/record[key]["path"], record[key]["sha256"])
        full = read_gzip(self.output/record["global_references"]["path"])
        equations = read_gzip(self.output/record["equations"]["path"])["independent_equations"]
        saved, scale = row["workpiece"], Decimal(record["metrics"]["force_scale_N"])
        checks, references = {}, {}
        with localcontext() as context:
            context.prec = 120
            for column, part in enumerate(COMPONENTS):
                values = {p: [-x for x in vector_sum(full[p][FORCE_KEYS[column]], self.workpiece_dofs)] for p in ("80", "120")}
                den = scale if part == "total" else max(norm(list(map(Decimal, full["80"][FORCE_KEYS[column]]))), Decimal("1e-12")*scale)
                measured, _ = compare(saved["force_on_lower_body_N"][part], values["80"], values["120"], den)
                checks[part+"_body_force"] = self.gate(measured, part+"_force", "workpiece "+part+" signed force")
                references[part] = values
            owned = set(map(int, self.workpiece_dofs))
            partition = {"workpiece": sorted(owned)}
            for name, group in self.groups.items():
                partition[name] = sorted(set(group)-owned)
                owned.update(group)
            self.check(owned == set(map(int, self.model["fixed_dofs"]))
                and sum(map(len, partition.values())) == len(owned), "Holding groups do not partition merged fixed DOFs once")
            holding = {p: {name: vector_sum(equations[p]["support"], dofs) for name, dofs in partition.items()} for p in ("80", "120")}
            for name in partition:
                measured, _ = compare(saved["fixed_holding_reaction_partition_N"][name], holding["80"][name], holding["120"][name], scale)
                checks["holding_partition_"+name] = self.gate(measured, "force_evaluation", "holding partition "+name)
            extra = {p: vector_sum(equations[p]["support"], self.model["workpiece_background_symmetry_overlap_dofs"]) for p in ("80", "120")}
            fx, fy = references["total"]["80"]
            other_fx, other_fy = references["total"]["120"]
            projections = {
                "holding_reaction_on_model_N": (holding["80"]["workpiece"], holding["120"]["workpiece"]),
                "normal_force_on_lower_body_N": ([fy], [other_fy]),
                "mirrored_upper_force_N": ([fx, -fy], [other_fx, -other_fy]),
                "full_workpiece_net_force_N": ([2*fx, Decimal(0)], [2*other_fx, Decimal(0)]),
                "two_sided_normal_magnitude_sum_N": ([2*abs(fy)], [2*abs(other_fy)]),
                "overlapping_background_holding_reaction_N": (extra["80"], extra["120"]),
            }
            for name, (a, b) in projections.items():
                actual = saved[name] if isinstance(saved[name], list) else [saved[name]]
                measured, _ = compare(actual, a, b, scale)
                checks[name] = self.gate(measured, "force_evaluation", "workpiece observation "+name)
        state, forces = (npz(self.origin/row[name]["path"]) for name in ("state", "forces"))
        cells = self.model["workpiece_cells"]
        self.check(np.count_nonzero(state["lift"][self.workpiece_dofs]) == np.count_nonzero(state["fluctuation"][self.workpiece_dofs]) == 0
            and np.array_equal(forces["F"][cells], np.broadcast_to(np.eye(2), forces["F"][cells].shape))
            and np.all(forces["J"][cells] == 1.) and np.count_nonzero(forces["Hu"][cells]) == 0
            and np.count_nonzero(forces["stress_first_piola"][cells]) == np.count_nonzero(forces["element_total_force"][cells]) == 0
            and all(value == 0. for value in saved["fixed_body_fields"].values()), "Fixed body interior is not the undeformed dummy field")
        path = directory/"workpiece_checks.json.gz"
        write_gzip(path, dict(checks=checks, signed_body_reference_N=references, holding_partition_dofs=partition,
            holding_partition_reference_N=holding, overlap_reference_N=extra,
            force_scale_N=scale, original_component_scale_rule=True,
            scope="Negative weak-form holding reaction, signed material/Hu contributions; mirror only about y=40. No pressure or contact qualification"))
        record["workpiece_checks"] = self.record(path)
        record["original_target_index"], record["leg"] = row["original_target_index"], row["leg"]
        write(directory/"summary.json", record)
        self.checkpoint()

    def run(self):
        self.checkpoint()
        self.load()
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        self.reference_class = DecimalSplitQ1Reference
        for index, row in enumerate(self.result["states"]):
            self.run_state(index, row)
            self.workpiece_checks(index, row)
        self.check(self.hp_started == self.hp_completed == 2*len(self.result["states"]), "Fresh full-state HP coverage/calls differ")
        for path, expected in self.bindings.items():
            self.check(sha(path) == expected, "Bound source/input changed: "+str(path))
        self.checkpoint()
        summary = dict(schema_version="native-workpiece-cycle-independent-audit-1.0", status="pass",
            alias="gripper_coarse_square", source_alias="gripper_canonical", case_family="gripper",
            baseline_commit=BASELINE, audited_targets_mm=TARGETS, path_kind="ordered_cycle", workpiece=BODY,
            accepted_states=len(self.rows), states=self.rows, result_sha256=sha(self.result_file),
            checks_completed=self.checks, HP_calls_started=self.hp_started, HP_calls_completed=self.hp_completed,
            HP_matrix_columns_exhaustively_checked=False, full_element_and_DOF_coverage=True,
            gates=GATES, global_scatter_precision=3000, global_scatter_inexact_trap=True,
            reference_scope="Every actual accepted state and element, exact real-DOF scatter; fixed-lift b_in/max(abs(b_in)), deltaR=0; same references project signed body and disjoint holding groups",
            qualification="Only this recorded coarse fixed-square small-cycle numerical TEST; no clamp, contact pressure, H2/H3, HF5, fine-grid, full-stroke or other-task qualification",
            contact_qualified=False, clamp_qualified=False, pressure_qualified=False,
            inherited_run_state_source_sha256=CORE_PINS["audit_native_mean.py"], candidate_force_calls=0, tangent_calls=0, solver_calls=0,
            source_bindings=self.sources, input_bindings={p.relative_to(self.repo).as_posix(): h for p, h in self.bindings.items()},
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT)
        write(self.output/"summary.json", summary)
        self.checkpoint()
        self.lifecycle("pass")
        self.checkpoint()
        print(dict(status="pass", accepted_states=len(self.rows), HP_calls=self.hp_completed, checks_completed=self.checks), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=240.)
    args = parser.parse_args()
    require(np.isfinite(args.time_limit) and 0 < args.time_limit <= 240., "Reference limit must be in (0,240]")
    audit = WorkpieceCycleAudit(args)
    try:
        audit.run()
    except Exception as error:
        audit.lifecycle("not_pass", repr(error))
        write(audit.output/"summary.json", dict(schema_version="native-workpiece-cycle-independent-audit-1.0",
            status="not_pass", alias="gripper_coarse_square", error=repr(error), states=audit.rows,
            accepted_states=len(audit.rows), checks_completed=audit.checks, HP_calls_started=audit.hp_started,
            HP_calls_completed=audit.hp_completed, elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__":
    main()
