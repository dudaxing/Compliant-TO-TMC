"""Fresh exhaustive mechanical-mode reference for the coarse square 1.8 mm cycle.

The private CoreAudit retains the original compensated saved-tensor actions,
reference equations and mathematical gates. Only the declared sixteen-field
mechanical response contract replaces the full auxiliary-energy availability.
HP analytic energy is archived without candidate comparison or qualification.
The original signed workpiece projections remain unchanged. Rejected trials
are unqualified; no production response, solve or construction is evaluated.
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
PARSER.add_argument("--time-limit", type=float, default=600.)
ARGS = PARSER.parse_args()
ROOT = ARGS.repo.resolve() if ARGS.repo else next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())
SCRIPTS = ROOT/"hf_repo/scripts"
OLD_CHECKER_SHA = "aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938"
LEGACY_FREEZE_SHA = "eb926541f25fdd1783bda17368ca112558fdab03b1ad70366e7b12c655076791"
KERNEL_PIN = "d5f7d20a6ec0c92847d67f8782f4dcc89772fc4ea62797626b0beae7effabd9a"
NATIVE_MEAN_PIN = "186a6662c14310b4dc577591764eef849988448de132474fd6953579449cb22b"
CLI_PIN = "d457783d3818f3f4c5fe2ce558df9cd9a14245880198aaa6907e7b3541d54888"
TANGENT_PIN = "fe36581e8b49f1a547973e135f3c8ca0f2bbc7d954502405418bd794d731955a"
TANGENT_EXECUTION = dict(mode="chunk256", element_block_size=256, global_selector_scope="full_batch")
CONSUMER_PIN = "b52f8b5ab279321f6e716885dd00dae946929c4b7c23d97d98d9bcd7f5b593fe"
PRIVATE_CORE_PIN = 'b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5'
PREVIOUS_TASK_PIN = 'aa6801849144f85fe6db1ab68db0869d6895b531a556481234f1e0fc9339c54c'
BODY_MODEL_PIN = "a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049"
PRIVATE_CORE = Path(__file__).with_name("core_audit_mechanical.py")
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
expected_core = expected_core.replace(
    "The production tensor consumer is imported only to apply saved Jacobians.",
    "The production tensor consumer is imported only to apply saved Jacobians.\n"
    "This private loader requires explicit mechanical availability and sixteen saved\n"
    "force fields; HP analytic energy is archived without candidate comparison or\n"
    "energy qualification. Every mathematical equation and gate is retained.")
expected_core = expected_core.replace(
    'COMPONENTS = ("total", "material", "regularization")\n',
    'COMPONENTS = ("total", "material", "regularization")\n'
    'MECHANICAL_AVAILABILITY = dict(response_mode="mechanical", response_contract="split-numpy-mechanical-1.0",\n'
    '    force_kernel_version="p26_q1_split_mechanical_numpy_aux_omitted_candidate1",\n'
    '    auxiliary_material_energy=dict(status="not_evaluated", qualified=False, field_present=False))\n')
expected_core = expected_core.replace(
    '        self.check(descriptor == {key: value for key, value in row.items()\n'
    '            if key not in ("descriptor_path", "descriptor_file_sha256")}, "Accepted descriptor differs from result")\n',
    '        self.check(descriptor == {key: value for key, value in row.items()\n'
    '            if key not in ("descriptor_path", "descriptor_file_sha256")}, "Accepted descriptor differs from result")\n'
    '        self.check(all(row.get(key) == value for key, value in MECHANICAL_AVAILABILITY.items()),\n'
    '            "Accepted mechanical response/auxiliary availability differs")\n')
expected_core = expected_core.replace(
    'stress_second_piola=(ne, 9, 2, 2), material_energy=(ne,), input_force=(ndof,), support_reaction=(ndof,),',
    'stress_second_piola=(ne, 9, 2, 2), input_force=(ndof,), support_reaction=(ndof,),').replace(
    '"Accepted full force fields/J differ"', '"Accepted mechanical force fields/J differ"')
require(sha(SCRIPTS/"audit_native_mean.py") == CORE_PINS["audit_native_mean.py"]
    and sha(PRIVATE_CORE) == PRIVATE_CORE_PIN
    and PRIVATE_CORE.read_text(encoding="utf-8") == expected_core,
    "Private CoreAudit differs beyond consumer/explicit mechanical availability/16-field shape/scope")
require(sha(ROOT/"hf_repo/src/hf_eval/tangent_action.py") == CONSUMER_PIN
    and sha(ROOT/"hf_repo/src/hf_eval/split_kernel_invariants_hu.py") == KERNEL_PIN,
    "Declared new kernel or saved-tensor consumer differs")
from core_audit_mechanical import Audit as ActionCoreAudit, MECHANICAL_AVAILABILITY
from counter_contract import reconstruct

BASELINE = "07134ea6cd9aa0ab2de4bf97f80a8e8ca44c241e"
TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.1/16, time_limit_seconds=900.)
LIMITS = dict(production_seconds=900, reference_seconds=600, sampled_RSS_bytes=RSS_LIMIT,
    production_outer_seconds=960, reference_outer_seconds=660, view_outer_seconds=120)


class CycleAudit(ActionCoreAudit, WorkpieceCycleAudit):
    # The private core supplies run_state; the original wrapper supplies workpiece_checks.
    # check, gate, scalar_gate and all reference equations are unchanged.
    def __init__(self, args):
        super().__init__(args)
        self.repo = ROOT  # The unchanged private CoreAudit initializer was relocated.
        require(self.repo == ROOT and self.limit == LIMITS["reference_seconds"], "Explicit repository/reference budget differs")
        self.accounting = None
        self.first_range_observation = None
        self.tangent_range_observation = None

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "Eleven-target cycle reference time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Eleven-target cycle reference sampled RSS exceeds 8 GiB")

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
            and inventory["baseline_commit"] == BASELINE and self.stage.name == "coarse_square_cycle_010"
            and row["alias"] == "gripper_coarse_square" and row["source_alias"] == "gripper_canonical"
            and row["targets_mm"] == TARGETS and row["geometry_id"] == GEOMETRY_ID
            and (row["elements"], row["dofs"], row["fixed_DOFs"], row["free_DOFs"]) == (3200, 6642, 376, 6266)
            and all(row[key] == value for key, value in PINS.items())
            and inventory["settings"] == SETTINGS and inventory["execution_limits"] == LIMITS,
            "Wrong declared coarse fixed-square cycle identity/settings")
        self.check(all(inventory.get(key) == MECHANICAL_AVAILABILITY[key] for key in
            ("response_mode", "response_contract", "auxiliary_material_energy")),
            "Inventory must explicitly omit unqualified auxiliary material energy")
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
        reference_protocol = Path(__file__).with_name("protocol.json")
        self.bind(reference_protocol)
        self.reference_protocol_sha256 = sha(reference_protocol)
        self.reference_bindings = read(reference_protocol)["bindings"]
        for name, expected in self.reference_bindings.items():
            self.bind(self.repo/name, expected)
        self.check(self.reference_bindings.get(Path(__file__).relative_to(self.repo).as_posix()) == sha(Path(__file__))
            and self.reference_bindings.get(Path(__file__).with_name("counter_contract.py").relative_to(self.repo).as_posix())
                == sha(Path(__file__).with_name("counter_contract.py")), "Independent reference/counter source binding differs")
        self.check(self.sources["hf_repo/scripts/audit_native_workpiece_cycle.py"] == OLD_CHECKER_SHA
            and receipt["inputs"] == inventory["input_bindings"], "Inherited checker or new input closure differs")
        legacy_stage = self.repo/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_003"
        self.bind(legacy_stage/"source_freeze.json", LEGACY_FREEZE_SHA)
        legacy_sources = read(legacy_stage/"source_freeze.json")["sources"]
        changes = {"hf_repo/src/hf_eval/split_kernel_invariants_hu.py": KERNEL_PIN,
                   "hf_repo/src/hf_eval/native_mean.py": NATIVE_MEAN_PIN,
                   "hf_repo/scripts/solve_native_mean.py": CLI_PIN,
                   "hf_repo/src/hf_eval/split_numpy_tangent.py": TANGENT_PIN}
        expected_sources = dict(legacy_sources, **changes)
        extra_paths = [self.stage/"core_audit_mechanical.py", self.stage/"audit_cycle010.py", *(self.stage/name for name in
            ("prepare_cycle010.py", "execute_cycle010.py", "launch_cycle010.py"))]
        extras = {path.relative_to(self.repo).as_posix() for path in extra_paths}
        transition = {name: dict(previous_sha256=legacy_sources[name], current_sha256=pin)
                      for name, pin in changes.items()}
        self.check(len(legacy_sources) == 63 and len(self.sources) == 68
            and set(self.sources) == set(legacy_sources)|extras
            and all(self.sources.get(name) == pin for name, pin in expected_sources.items())
            and inventory["source_transition"] == freeze["source_transition"] == transition
            and self.sources["hf_repo/src/hf_eval/tangent_action.py"] == CONSUMER_PIN
            and self.sources[(self.stage/"core_audit_mechanical.py").relative_to(self.repo).as_posix()] == sha(PRIVATE_CORE),
            "Previous 63 sources or the four declared mechanical/tangent-interface changes differ")
        for name, pin in legacy_sources.items():
            self.bind(legacy_stage/"sources"/Path(name).name, pin)
        legacy_inventory_file = legacy_stage/"input_inventory.json"
        self.bind(legacy_inventory_file, inventory["input_bindings"][legacy_inventory_file.relative_to(self.repo).as_posix()])
        legacy_inventory = read(legacy_inventory_file)
        self.check(all(inventory["input_bindings"].get(name) == pin
            for name, pin in legacy_inventory["input_bindings"].items()), "Original physical input closure differs")
        unit_file = legacy_stage.parent/"native_mean_mechanical_integration_001/unit_tests_result.json"
        self.bind(unit_file, inventory["input_bindings"][unit_file.relative_to(self.repo).as_posix()])
        unit = read(unit_file)
        self.check(unit["status"] == "pass" and unit["failed_tests"] == unit["skipped_tests"] == 0,
            "Mechanical mean integration tests must have passed before this production")
        self.verify_chunk_prerequisites(inventory)
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
        self.check(result["schema_version"] == "hf-native-mean-result-1.2" and result["status"] == "success"
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
        self.check(all(result.get(key) == receipt.get(key) == value for key, value in MECHANICAL_AVAILABILITY.items()),
            "Saved result/receipt must declare the explicit mechanical response and absent auxiliary energy")
        self.check(result.get("tangent_execution") == TANGENT_EXECUTION
            and all(item.get("tangent_execution") == TANGENT_EXECUTION for item in result["states"]),
            "Result and every accepted cache must explicitly declare chunk256/full-batch selection")
        self.accounting = self.reconstruct_counts(result, receipt)
        counts = result["call_counts"]
        self.check(receipt["observed_force_calls_completed"] == counts["force_calls_completed"]
            and receipt["observed_tangent_calls"] == counts["tangent_calls"]
            and receipt["observed_tangent_calls_completed"] == counts["tangent_calls_completed"]
            and receipt["first_tangent_range_input"] is not None
            and (self.stage/"first_tangent_range_input").is_dir()
            and receipt["force_hook_restored"] is receipt["tangent_hook_restored"] is True,
            "Completed force/tangent observer chronology or same-instance restoration differs")
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
        previous_task_file = self.repo/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_009/task.json"
        self.bind(previous_task_file, PREVIOUS_TASK_PIN)
        self.check(inventory["input_bindings"].get(previous_task_file.relative_to(self.repo).as_posix()) == PREVIOUS_TASK_PIN,
            "Previous mechanical task is not bound by the new input closure")
        previous_task = read(previous_task_file)
        descriptive = {"task_id", "purpose", "parameter_origin", "description"}
        expected_task = dict(previous_task, input=dict(previous_task["input"], target_mm=max(TARGETS)),
            path=dict(kind="ordered_cycle", targets_mm=TARGETS))
        self.check({key: value for key, value in task.items() if key not in descriptive}
            == {key: value for key, value in expected_task.items() if key not in descriptive},
            "Task changed beyond the declared 1.8 mm peak/ordered path and four descriptive keys")
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
        self.tangent_range_observation = self.verify_tangent_range_observation(receipt, model)
        self.checkpoint()

    def verify_chunk_prerequisites(self, inventory):
        """Bind closed chunk equivalence and fresh integration before any HP."""
        chunk = self.repo/"lf_data_preparation/native_workpiece_001/numpy_tangent_chunk_001"
        integration = self.repo/"lf_data_preparation/native_workpiece_001/native_mean_chunk_integration_001"
        self.check(len(inventory["input_bindings"]) == 73, "Expected 73 declared inputs for the new eleven-target card")
        for stage, phases in ((chunk, ("tests", "comparison")), (integration, ("tests",))):
            protocol_file = stage/"protocol.json"
            self.bind(protocol_file, inventory["input_bindings"][protocol_file.relative_to(self.repo).as_posix()])
            protocol = read(protocol_file)
            for name, pin in protocol["bindings"].items():
                if stage == chunk and name == "hf_repo/src/hf_eval/native_mean.py":
                    self.check(pin == "205572334129ec4d7aaf9fdd5838935b450fce929e6b2ea18844308f85ae8fd3"
                        and self.sources[name] == NATIVE_MEAN_PIN,
                        "Closed chunk producer source must have the explicit new native-mean transition")
                    continue  # The unchanged historical capsule is bound by the same protocol.
                self.bind(self.repo/name, pin)
            for phase in phases:
                paths = (stage/(phase+"_launch.json"), stage/(phase+"_receipt.json"))
                for path in paths:
                    self.bind(path, inventory["input_bindings"][path.relative_to(self.repo).as_posix()])
                launch, receipt = map(read, paths)
                limits = protocol["phases"][phase]
                peak_key = "peak_sampled_RSS_bytes" if stage == chunk else "sampled_peak_RSS_bytes"
                self.check(launch["status"] == receipt["status"] == "pass"
                    and launch["exit_code"] == 0 and launch["invocations"] == receipt["invocations"] == 1
                    and launch["protocol_sha256"] == sha(protocol_file) and launch["bindings"] == protocol["bindings"]
                    and launch["stop_reason"] is None and launch["all_bindings_unchanged"] is True
                    and receipt["all_bindings_unchanged"] is True
                    and 0 <= receipt["elapsed_seconds"] <= limits["helper_seconds"]
                    and 0 <= launch["elapsed_seconds"] <= limits["outer_seconds"]
                    and 0 <= receipt[peak_key] <= RSS_LIMIT
                    and 0 <= launch["peak_sampled_tree_RSS_bytes"] <= RSS_LIMIT,
                    "A chunk/integration prerequisite did not close once within its original resource window")
        comparison = read(chunk/"comparison_receipt.json")
        rows = comparison["rows"]
        self.check([row["name"] for row in rows] == ["origin007", "peak008", "return007"]
            and all(row["status"] == "pass" and row["single_pass_speed_ratio"] >= 1.25
                    and row["all_three_tensors_byte_equal"] is row["tensor_strides_preserved"]
                        is row["all_full_CSC_bytes_equal"] is row["rich_cache_unchanged"] is True for row in rows)
            and comparison["candidate_cost_gate_passed"] is comparison["compiled_hooks_restored"] is True
            and comparison["force_calls"] == comparison["force_calls_completed"] == 3
            and comparison["tangent_calls"] == comparison["tangent_calls_completed"] == 9
            and comparison["sparse_assembly_calls"] == 9
            and comparison["solver_calls"] == comparison["HP_calls"] == comparison["JIT_calls"] == 0
            and comparison["independent_HP_qualified"] is comparison["old_closed_008_card_reopened"] is False,
            "The closed three-state chunk equivalence/cost card is incomplete or has expanded qualification")
        unit = read(integration/"tests_receipt.json")
        self.check(unit["passed_tests"] == 10 and unit["failed_tests"] == unit["skipped_tests"] == unit["error_tests"] == 0
            and unit["pytest_exit_code"] == 0 and unit["formal_workpiece_solver_calls"] == 0
            and unit["HP_calls"] == unit["JIT_calls"] == 0,
            "Fresh full/chunk mean integration tests must close once before nine-target production")
        self.chunk_prerequisites = dict(three_state_saved_input_equivalence_and_cost=True,
            fresh_mean_integration_tests=10, inherited_chunk_HP_calls=0,
            scope="Closed supplied-state cost/equivalence plus new tiny integration only; no inherited cycle008 HP")

    def reconstruct_counts(self, result, receipt):
        """Strict captured-failure trace; all accepted caches must be complete."""
        return reconstruct(result, receipt, SETTINGS, self.check)

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

    def verify_tangent_range_observation(self, receipt, model):
        """Read/copy failed input and its same-object force fields; no reevaluation."""
        directory = self.stage/"first_tangent_range_input"
        descriptor = directory/"observation.json"
        self.bind(descriptor)
        observation = read(descriptor)
        self.check(observation == receipt["first_tangent_range_input"]
            and observation["tangent_call_ordinal"] == self.accounting["failed_tangent_base"]["tangent_call"]
            and observation["bound_force_call_ordinal"] == self.accounting["failed_tangent_base"]["force_call"]
            and observation["state_sha256"] == self.accounting["failed_tangent_base"]["state_sha256"]
            and observation["source_freeze_sha256"] == receipt["source_freeze_sha256"]
            and observation["input_inventory_sha256"] == receipt["input_inventory_sha256"]
            and observation["exception_type"] == "KernelError"
            and np.isfinite(observation["elapsed_seconds"])
            and 0 <= observation["elapsed_seconds"] <= receipt["elapsed_seconds"],
            "Failed tangent observation/provenance differs")
        archive, force_archive = directory/"input.npz", directory/"force_fields.npz"
        self.bind(archive, observation["input_npz_sha256"])
        self.bind(force_archive, observation["force_fields_npz_sha256"])
        arrays, fields = npz(archive), npz(force_archive)
        verify_fields(arrays, observation["fields"])
        verify_fields(fields, observation["force_fields"])
        intrinsic = ("edofs", "coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy",
                     "thickness", "solid", "fixed_dofs", "grad", "hessian", "weights", "points")
        self.check(set(arrays) == set(intrinsic)|{"lift", "fluctuation"}, "Failed tangent input field contract")
        same_arrays({k:arrays[k] for k in intrinsic},{k:model[k] for k in intrinsic}, "Failed tangent model/operator fields")
        self.check(all(arrays[k].dtype == np.dtype("float64") and arrays[k].shape == (6642,)
                and np.isfinite(arrays[k]).all() for k in ("lift","fluctuation"))
            and np.count_nonzero(arrays["lift"]) == 0
            and np.count_nonzero(arrays["fluctuation"][model["fixed_dofs"]]) == 0
            and state_hash(arrays) == observation["state_sha256"]
            and all(np.isfinite(v).all() for v in fields.values())
            and fields["J"].shape == (3200,9) and np.all(fields["J"] > 0)
            and not any(row["state_sha256"] == observation["state_sha256"] for row in self.result["states"]),
            "Failed tangent raw fields/state/caches differ")
        copied = self.output/"first_tangent_range_input"; copied.mkdir()
        for path in (descriptor,archive,force_archive):
            shutil.copyfile(path,copied/path.name); self.bind(copied/path.name,sha(path))
        return dict(observation=self.record(copied/descriptor.name),input=self.record(copied/archive.name),
            force_fields=self.record(copied/force_archive.name),tangent_call_ordinal=observation["tangent_call_ordinal"],
            bound_force_call_ordinal=observation["bound_force_call_ordinal"],state_sha256=observation["state_sha256"],
            independently_qualified=False,reevaluated=False,arithmetic_issue_resolved=False,
            scope="Only bound failed local tangent input and returned force fields; no force/tangent/HP evaluation")

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
            qualification="Only accepted mechanical states of this declared coarse square [0,.5,1,1.5,1.75,1.8,1.75,1.5,1,.5,0] cycle under original force/Jv/equilibrium/workpiece gates; no auxiliary-energy, stress-HP, rejected-trial, pressure, clamp, H2/H3, HF5 or all-column qualification",
            response_mode="mechanical", response_contract=MECHANICAL_AVAILABILITY["response_contract"],
            force_kernel_version=MECHANICAL_AVAILABILITY["force_kernel_version"],
            auxiliary_material_energy=MECHANICAL_AVAILABILITY["auxiliary_material_energy"],
            analytic_HP_energy_scope="Archived reference evaluator output only; no candidate energy or energy qualification",
            contact_qualified=False, clamp_qualified=False, pressure_qualified=False,
            original_run_state_source_sha256=CORE_PINS["audit_native_mean.py"],
            private_run_state_source_sha256=sha(PRIVATE_CORE),
            private_core_changes="Original compensated consumer and all equations/gates retained; explicit mechanical availability check and 16-field shape contract; scope docstring",
            tangent_action_consumer_sha256=CONSUMER_PIN, promoted_kernel_sha256=KERNEL_PIN,
            tangent_execution=TANGENT_EXECUTION, tangent_source_sha256=TANGENT_PIN,
            chunk_prerequisites=self.chunk_prerequisites,
            inherited_workpiece_checker_sha256=OLD_CHECKER_SHA,
            candidate_force_calls=0, tangent_calls=0, solver_calls=0, counter_accounting=self.accounting,
            first_force_range_input=self.first_range_observation,
            tangent_observation=dict(observed_tangent_calls=self.receipt["observed_tangent_calls"],
                observed_tangent_calls_completed=self.receipt["observed_tangent_calls_completed"],
                all_tangent_calls_completed=False,all_accepted_caches_completed=True,
                first_tangent_range_input=self.tangent_range_observation),
            independent_reference_card_protocol_sha256=self.reference_protocol_sha256,
            independent_reference_source_bindings=self.reference_bindings,
            source_bindings=self.sources, input_bindings={p.relative_to(self.repo).as_posix(): h for p,h in self.bindings.items()},
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT)
        write(self.output/"summary.json", summary)
        self.checkpoint()
        self.lifecycle("pass")
        self.checkpoint()
        print(dict(status="pass", accepted_states=len(self.rows), HP_calls=self.hp_completed, checks_completed=self.checks), flush=True)


def main():
    require(np.isfinite(ARGS.time_limit) and ARGS.time_limit == LIMITS["reference_seconds"], "Reference limit must be exactly the declared 600 seconds")
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
