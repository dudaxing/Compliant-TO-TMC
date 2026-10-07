"""Fresh exhaustive reference for the new-core coarse square three-point cycle.

The private CoreAudit differs from the original only by its compensated saved
tensor action consumer. All equations, reference evaluations and mathematical
gates remain unchanged; the pinned workpiece projections are inherited.
Rejected trial states remain unqualified. This script performs no production
force, tangent, solver or geometry construction.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
import argparse
import ast
import hashlib
from pathlib import Path
import shutil
import sys

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--input", type=Path, required=True)
PARSER.add_argument("--output", type=Path, required=True)
PARSER.add_argument("--repo", type=Path, help="Repository root; otherwise inferred after installation")
PARSER.add_argument("--time-limit", type=float, default=240.)
ARGS = PARSER.parse_args()
ROOT = ARGS.repo.resolve() if ARGS.repo else next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())
SCRIPTS = ROOT/"hf_repo/scripts"
OLD_CHECKER_SHA = "aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938"
LEGACY_FREEZE_SHA = "b11b7d5002b46aec3ebdcf38fcf1a01ed4c8ec9737b89b6c7785657ad16cfdc0"
KERNEL_PIN = "7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce"
CONSUMER_PIN = "b52f8b5ab279321f6e716885dd00dae946929c4b7c23d97d98d9bcd7f5b593fe"
BODY_MODEL_PIN = "a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049"
PRIVATE_CORE = Path(__file__).with_name("core_audit.py")
if hashlib.sha256((SCRIPTS/"audit_native_workpiece_cycle.py").read_bytes()).hexdigest() != OLD_CHECKER_SHA:
    raise ValueError("Frozen workpiece reference wrapper changed")
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT/"hf_repo/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_native_workpiece_cycle import (WorkpieceCycleAudit, CORE_PINS, PINS, BODY,
    GEOMETRY_ID, GEOMETRY_DESCRIPTOR_SHA, RSS_LIMIT, GATES, canonical_hash,
    npz, read, require, same_arrays, sha, verify_descriptor, verify_fields, write)
from audit_native_force import state_hash
import numpy as np

original_core = (SCRIPTS/"audit_native_mean.py").read_text(encoding="utf-8")
expected_core = original_core.replace(
    '\nCOMPONENTS = ("total", "material", "regularization")',
    '\nfrom hf_eval.tangent_action import apply_element_tangent_numpy\n'
    '\nCOMPONENTS = ("total", "material", "regularization")').replace(
    'local_actions = {part: np.einsum("eij,ej->ei", tensors[part+"_tangent"], v[edofs]) for part in COMPONENTS}',
    'local_actions = {part: apply_element_tangent_numpy(tensors[part+"_tangent"], v[edofs]) for part in COMPONENTS}')
expected_core = expected_core.replace(
    "direction is independently checked, not all tangent columns. No production\n"
    "mechanics, model constructor, controller or shared assembler is imported.",
    "direction is independently checked, not all tangent columns. No constitutive\n"
    "response, model constructor, controller or shared assembler is evaluated.\n"
    "The production tensor consumer is imported only to apply saved Jacobians.")
require(sha(SCRIPTS/"audit_native_mean.py") == CORE_PINS["audit_native_mean.py"]
    and PRIVATE_CORE.read_text(encoding="utf-8") == expected_core,
    "Private CoreAudit differs beyond consumer import/local action/scope docstring")
require(sha(ROOT/"hf_repo/src/hf_eval/tangent_action.py") == CONSUMER_PIN
    and sha(ROOT/"hf_repo/src/hf_eval/split_kernel_invariants_hu.py") == KERNEL_PIN,
    "Declared new kernel or saved-tensor consumer differs")
from core_audit import Audit as ActionCoreAudit

BASELINE = "33ac937620da1e2c87686dd028a0792f258220d8"
TARGETS = [0., .5, 0.]
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.1/16, time_limit_seconds=600.)
LIMITS = dict(production_seconds=600, reference_seconds=240, sampled_RSS_bytes=RSS_LIMIT,
    production_outer_seconds=660, reference_outer_seconds=300, view_outer_seconds=120)


class CycleAudit(ActionCoreAudit, WorkpieceCycleAudit):
    # The private core supplies run_state; the original wrapper supplies workpiece_checks.
    # check, gate, scalar_gate and all reference equations are unchanged.
    def __init__(self, args):
        super().__init__(args)
        self.repo = ROOT  # The unchanged private CoreAudit initializer was relocated.
        require(self.repo == ROOT and self.limit == LIMITS["reference_seconds"], "Explicit repository/reference budget differs")
        self.accounting = None
        self.first_range_observation = None

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "Three-point cycle reference time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Three-point cycle reference sampled RSS exceeds 8 GiB")

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
            and inventory["baseline_commit"] == BASELINE and self.stage.name == "coarse_square_cycle_003"
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
            and receipt["seconds_limit"] == LIMITS["production_seconds"] and receipt["sampled_RSS_limit_bytes"] == RSS_LIMIT
            and np.isfinite(receipt["elapsed_seconds"]) and 0 <= receipt["elapsed_seconds"] <= LIMITS["production_seconds"]
            and 0 <= receipt["sampled_peak_RSS_bytes"] <= RSS_LIMIT
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
            path = SCRIPTS/name
            self.check(self.sources[path.relative_to(self.repo).as_posix()] == expected, "Inherited/reference source changed")
        self.check(Path(__file__).relative_to(self.repo).as_posix() in self.sources, "New checker is not source-bound")
        self.check(self.sources["hf_repo/scripts/audit_native_workpiece_cycle.py"] == OLD_CHECKER_SHA
            and receipt["inputs"] == inventory["input_bindings"], "Inherited checker or new input closure differs")
        legacy_stage = self.repo/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_002"
        self.bind(legacy_stage/"source_freeze.json", LEGACY_FREEZE_SHA)
        legacy_sources = read(legacy_stage/"source_freeze.json")["sources"]
        expected_sources = dict(legacy_sources)
        kernel_key = "hf_repo/src/hf_eval/split_kernel_invariants_hu.py"
        expected_sources[kernel_key] = KERNEL_PIN
        extra_paths = [self.repo/"hf_repo/src/hf_eval/tangent_action.py", PRIVATE_CORE,
            Path(__file__), *(self.stage/name for name in
                ("prepare_cycle003.py", "execute_cycle003.py", "launch_cycle003.py"))]
        extras = {path.relative_to(self.repo).as_posix() for path in extra_paths}
        transition = {kernel_key: dict(previous_sha256=legacy_sources[kernel_key], current_sha256=KERNEL_PIN)}
        self.check(len(legacy_sources) == 57 and len(self.sources) == 63
            and set(self.sources) == set(legacy_sources)|extras
            and all(self.sources.get(name) == pin for name, pin in expected_sources.items())
            and inventory["source_transition"] == freeze["source_transition"] == transition
            and self.sources["hf_repo/src/hf_eval/tangent_action.py"] == CONSUMER_PIN
            and self.sources[PRIVATE_CORE.relative_to(self.repo).as_posix()] == sha(PRIVATE_CORE),
            "Previous 57 sources or declared kernel/consumer/private-core changes differ")
        for name, pin in legacy_sources.items():
            self.bind(legacy_stage/"sources"/Path(name).name, pin)
        for path in (inventory_file, receipt_file, freeze_file):
            shutil.copyfile(path, self.output/path.name)
        original = SCRIPTS/"run_split_average_demo.py"
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
            and result["task_target_mm"] == max(TARGETS) and result["reached_displacement"] == result["target_origin"] == 0.
            and result["settings"] == SETTINGS and result["backend"] == "numpy"
            and result["matrix_units"] == "N/mm" and result["k_out_N_per_mm"] == 0.
            and result["force_scale_per_length"] == 20. and result["failure"] is None
            and result["save_force_calls"] == result["save_tangent_calls"] == 0
            and all(result[key] is False for key in ("equilibrium_qualified", "independent_HP_qualified", "HF_qualified")),
            "Production cycle/settings/scope differ")
        self.accounting = self.reconstruct_counts(result, receipt)
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
        self.check(row["workpiece_model_sha256"] == BODY_MODEL_PIN, "Original 27-array square model pin differs")
        self.bind(self.repo/row["workpiece_model_file"], BODY_MODEL_PIN)
        same_arrays(model, npz(self.repo/row["workpiece_model_file"]), "All original 27 fixed-square arrays")
        task, prior_task = (read(self.repo/row[key]) for key in ("task_file", "prior_task_file"))
        changed = {"schema_version", "task_id", "purpose", "parameter_origin", "description", "input", "workpiece", "path"}
        self.check(set(task) == set(prior_task)|{"path"}
            and all(task[key] == prior_task[key] for key in set(prior_task)-changed)
            and task["schema_version"] == "hf-native-project-task-1.1" and task["case_family"] == "gripper"
            and task["input"] == dict(prior_task["input"], target_mm=max(TARGETS)) and task["workpiece"] == BODY
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
        self.check(len(states) >= len(TARGETS) and len(states) == result["accepted_states"] == receipt["accepted_states"]
            and receipt["state_sha256"] == [item["state_sha256"] for item in states]
            and [item["d"] for item in originals] == TARGETS
            and [item["original_target_index"] for item in originals] == list(range(len(TARGETS)))
            and all(item["original_target_displacement"] == TARGETS[index]
                    for index, item in enumerate(originals))
            and all(item["target_origin"] == 0. and item["physical_mean_target_mm"] == item["d"] for item in states)
            and states[0]["leg"] == "origin" and states[0]["original_target_index"] == 0
            and states[0]["bisection_depth"] == 0 and states[0]["is_original_target"] is True
            and states[0]["d"] == states[-1]["d"] == 0.,
            "Actual accepted cycle does not retain all ordered original targets")
        for previous, current in zip(states, states[1:]):
            leg = current["original_target_index"]
            previous_leg = previous["original_target_index"]
            self.check(type(leg) is int and 1 <= leg < len(TARGETS)
                and leg in (previous_leg, previous_leg+1)
                and (leg == previous_leg or previous["is_original_target"] is True)
                and current["leg"] == ("loading" if TARGETS[leg] > TARGETS[leg-1] else "unloading")
                and current["original_target_displacement"] == TARGETS[leg]
                and (previous["d"] < current["d"] <= TARGETS[leg] if TARGETS[leg] > TARGETS[leg-1]
                     else TARGETS[leg] <= current["d"] < previous["d"])
                and 0 <= current["bisection_depth"] <= SETTINGS["max_bisections"],
                "Accepted ordered loading/unloading leg differs")
        self.model, self.edofs, self.direction = model, edofs, direction
        self.inventory, self.receipt, self.result, self.metadata = inventory, receipt, result, metadata
        self.workpiece_dofs, self.groups = dofs, groups
        self.first_range_observation = self.verify_first_range_observation(result, receipt, model)
        self.checkpoint()

    def reconstruct_counts(self, result, receipt):
        """Attribute every force start to a complete base or a recorded trial.

        A rejected Armijo trial has a complete force. Only a recorded range
        rejection without returned merit fields may account for an incomplete
        force, and its next factor must halve in that same Newton base.
        """
        counts, diagnostics = result["call_counts"], result["path_diagnostics"]
        history, trials, states = diagnostics["newton_history"], diagnostics["trials"], result["states"]
        expected_keys = {"force_calls", "force_calls_completed", "tangent_calls", "tangent_calls_completed",
                         "solver_invocations", "HP_calls", "JIT_calls"}
        self.check(set(counts) == expected_keys and all(type(v) is int and v >= 0 for v in counts.values())
            and counts["tangent_calls"] == counts["tangent_calls_completed"] == len(history)
            and counts["solver_invocations"] == 1 and counts["HP_calls"] == counts["JIT_calls"] == 0
            and receipt["call_counts"] == counts and receipt["force_calls"] == counts["force_calls"]
            and receipt["observed_force_calls"] == counts["force_calls"]
            and receipt["tangent_calls"] == counts["tangent_calls"] and receipt["solver_calls"] == 1
            and receipt["HP_calls"] == receipt["JIT_calls"] == receipt["LF_imports"] == 0
            and receipt["save_force_calls"] == receipt["save_tangent_calls"] == 0,
            "Completed Newton-base/tangent/receipt counters differ")
        by_tangent = {row["assembler_tangent_call"]: row for row in states}
        self.check(len(by_tangent) == len(states) and all(type(k) is int and 1 <= k <= len(history) for k in by_tangent),
                   "Accepted tangent-cache ordinals are not unique complete bases")
        events, caches, rejected, cursor, completed = [], [], [], 0, 0
        for tangent_call, base in enumerate(history, 1):
            self.check(type(base["newton_check"]) is int and 1 <= base["newton_check"] <= SETTINGS["max_checks"],
                       "Recorded Newton-base index differs")
            if base["newton_check"] > 1:
                previous = history[tangent_call-2] if tangent_call > 1 else None
                self.check(previous is not None and previous["d"] == base["d"]
                    and previous["newton_check"]+1 == base["newton_check"],
                    "Newton-base sequence skips an iteration or changes its attempt parameter")
            force_call = len(events)+1
            events.append(dict(force_call=force_call, kind="Newton_base", completed=True,
                d=base["d"], newton_check=base["newton_check"], tangent_call=tangent_call,
                state_sha256=base["state_sha256"]))
            completed += 1
            cached = by_tangent.get(tangent_call)
            if cached is not None:
                self.check(cached["assembler_force_call"] == force_call
                    and cached["assembler_state_sha256"] == cached["state_sha256"] == base["state_sha256"]
                    and cached["d"] == base["d"] and cached["newton_checks"] == base["newton_check"],
                    "Accepted state cache is not the recorded completed Newton base")
                caches.append(dict(force_call=force_call, tangent_call=tangent_call,
                                   state_sha256=cached["state_sha256"]))
                continue  # A converged base makes no line-search force call.
            group = []
            while cursor < len(trials) and len(group) <= SETTINGS["max_backtracks"]:
                trial = trials[cursor]
                if (trial["stage_parameter"], trial["newton_check"]) != (base["d"], base["newton_check"]):
                    break
                factor = 2.**(-len(group))
                self.check(type(trial["accepted"]) is bool and trial["factor"] == factor
                    and trial["target_displacement"] == trial["stage_parameter"] == base["d"]
                    and trial["fixed_residual_scale"] == base["residual_scale"],
                    "Trial chronology/factor/unchanged base scale differs")
                range_failure = trial["accepted"] is False and trial.get("reason") == "unsupported_arithmetic_range"
                if range_failure:
                    self.check(not any(k in trial for k in ("phi", "minimum_J", "R_input"))
                        and len(group) < SETTINGS["max_backtracks"] and cursor+1 < len(trials),
                        "Unaccounted incomplete force or terminal range rejection")
                    following = trials[cursor+1]
                    self.check((following["stage_parameter"], following["newton_check"], following["factor"])
                        == (base["d"], base["newton_check"], factor/2),
                        "Range-rejected trial is not followed by the controller half factor")
                    rejected.append(dict(trial_index=cursor, force_call=len(events)+1, **trial))
                else:
                    self.check(all(k in trial and np.isfinite(trial[k]) for k in ("phi", "minimum_J", "R_input"))
                        and trial["minimum_J"] > 0. and ((trial["accepted"] is True and trial.get("reason") is None)
                            or (trial["accepted"] is False and trial.get("reason") == "armijo_insufficient_decrease")),
                        "Unknown trial result cannot account for a completed force")
                events.append(dict(force_call=len(events)+1, kind="line_search_trial", completed=not range_failure,
                    d=trial["stage_parameter"], newton_check=trial["newton_check"], factor=factor,
                    accepted=trial["accepted"], reason=trial.get("reason")))
                completed += int(not range_failure)
                group.append(trial)
                cursor += 1
                if trial["accepted"]:
                    break
            if group:
                self.check(group[-1]["accepted"] is True or len(group) == SETTINGS["max_backtracks"]+1,
                           "Recorded bounded backtracking sequence terminates without acceptance or exhaustion")
        self.check(cursor == len(trials) and len(events) == counts["force_calls"]
            and completed == counts["force_calls_completed"]
            and counts["force_calls"]-counts["force_calls_completed"] == len(rejected)
            and [item["state_sha256"] for item in caches] == receipt["state_sha256"]
            and len(caches) == len(states), "Exact base/trial/accepted-cache chronology does not reconstruct counters")
        failures = diagnostics["failed_attempts"]
        self.check(all(item["rollback_bitwise_equal"] is True
            and item["code"] in ("newton_limit", "backtracking_failed", "singular_tangent", "nonfinite")
            and 0 <= item["depth"] < SETTINGS["max_bisections"] for item in failures)
            and 0 <= diagnostics["maximum_bisection_depth"] <= SETTINGS["max_bisections"],
            "Unrecorded rollback, unknown failed-attempt kind or excessive bisection")
        return dict(counts=counts, Newton_base_calls=len(history), trial_calls=len(trials),
            completed_trials=completed-len(history), rejected_range_trials=rejected,
            reconstructed_force_events=events, accepted_completed_caches=caches,
            all_Newton_base_and_tangent_calls_completed=True,
            policy="Only recorded unsupported_arithmetic_range trials followed by the same-base half factor account for incomplete forces; Armijo rejected forces remain complete",
            rejected_trials_independently_qualified=False, unsupported_arithmetic_issue_resolved=False,
            production_rerun=False, new_force_calls=0, new_tangent_calls=0, new_solver_calls=0)

    def verify_first_range_observation(self, result, receipt, model):
        """Bind the once-only observer's raw state/model without evaluating it."""
        directory = self.stage/"first_force_range_input"
        rejected = self.accounting["rejected_range_trials"]
        if not rejected:
            self.check(receipt["first_force_range_input"] is None and not directory.exists(),
                       "An unexplained force-range observation was saved")
            return None
        descriptor, archive = directory/"observation.json", directory/"input.npz"
        self.bind(descriptor)
        observation = read(descriptor)
        self.bind(archive, observation["input_npz_sha256"])
        arrays = npz(archive)
        verify_fields(arrays, observation["fields"])
        intrinsic = ("edofs", "coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy",
                     "thickness", "solid", "fixed_dofs", "grad", "hessian", "weights")
        self.check(set(arrays) == set(intrinsic)|{"lift", "fluctuation"}
            and observation == receipt["first_force_range_input"]
            and observation["schema_version"] == "native-force-range-input-1.0"
            and observation["code"] == "unsupported_arithmetic_range"
            and observation["exception_type"] in ("KernelError", "TMCError")
            and observation["force_call_ordinal"] == rejected[0]["force_call"]
            and observation["source_freeze_sha256"] == receipt["source_freeze_sha256"]
            and observation["input_inventory_sha256"] == receipt["input_inventory_sha256"]
            and np.isfinite(observation["elapsed_seconds"])
            and 0 <= observation["elapsed_seconds"] <= receipt["elapsed_seconds"]
            and all(observation[key] == 0 for key in ("extra_force_calls", "extra_tangent_calls", "extra_solver_calls", "HP_calls")),
            "First saved force-range observation differs from exact trial/counter provenance")
        same_arrays({key: arrays[key] for key in intrinsic}, {key: model[key] for key in intrinsic},
                    "First force-range input model/operator raw fields")
        self.check(all(arrays[key].dtype == np.dtype("float64") and arrays[key].shape == (6642,)
                       and np.isfinite(arrays[key]).all() for key in ("lift", "fluctuation"))
            and np.count_nonzero(arrays["lift"]) == 0
            and np.count_nonzero(arrays["fluctuation"][model["fixed_dofs"]]) == 0
            and state_hash(arrays) == observation["state_sha256"],
            "First range-rejected split input is not the bound finite zero-lift state")
        copied = self.output/"first_force_range_input"
        copied.mkdir()
        for path in (descriptor, archive):
            shutil.copyfile(path, copied/path.name)
            self.bind(copied/path.name, sha(path))
        return dict(observation=self.record(copied/descriptor.name), input=self.record(copied/archive.name),
            force_call_ordinal=observation["force_call_ordinal"], state_sha256=observation["state_sha256"],
            model_and_operator_fields_match_saved_model=True, independently_qualified=False,
            scope="First recorded rejected trial input only; no reevaluation or reference qualification")

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
            reference_scope="Every actual accepted state and element, exact real-DOF scatter; fixed-lift b_in/max(abs(b_in)), deltaR=0; inherited signed-body/holding projections",
            qualification="Only accepted states of the declared new-core coarse square [0,.5,0] cycle under unchanged gates and the compensated saved-tensor action method; no rejected-trial, pressure, clamp, H2/H3, HF5 or all-column qualification",
            contact_qualified=False, clamp_qualified=False, pressure_qualified=False,
            original_run_state_source_sha256=CORE_PINS["audit_native_mean.py"],
            private_run_state_source_sha256=sha(PRIVATE_CORE),
            private_core_changes="Consumer import/local_actions contraction and precise scope docstring; all other AST identical",
            tangent_action_consumer_sha256=CONSUMER_PIN, promoted_kernel_sha256=KERNEL_PIN,
            inherited_workpiece_checker_sha256=OLD_CHECKER_SHA,
            candidate_force_calls=0, tangent_calls=0, solver_calls=0, counter_accounting=self.accounting,
            first_force_range_input=self.first_range_observation,
            source_bindings=self.sources, input_bindings={p.relative_to(self.repo).as_posix(): h for p,h in self.bindings.items()},
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT)
        write(self.output/"summary.json", summary)
        self.checkpoint()
        self.lifecycle("pass")
        self.checkpoint()
        print(dict(status="pass", accepted_states=len(self.rows), HP_calls=self.hp_completed, checks_completed=self.checks), flush=True)


def main():
    require(np.isfinite(ARGS.time_limit) and ARGS.time_limit == LIMITS["reference_seconds"], "Reference limit must be exactly the declared 240 seconds")
    audit = CycleAudit(ARGS)
    try:
        audit.run()
    except Exception as error:
        audit.lifecycle("not_pass", repr(error))
        write(audit.output/"summary.json", dict(schema_version="native-workpiece-cycle-independent-audit-1.0",
            status="not_pass", alias="gripper_coarse_square", error=repr(error), states=audit.rows,
            accepted_states=len(audit.rows), checks_completed=audit.checks, HP_calls_started=audit.hp_started,
            HP_calls_completed=audit.hp_completed, counter_accounting=audit.accounting,
            first_force_range_input=audit.first_range_observation,
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__":
    main()
