"""Fresh accepted-state reference for the explicit complete x71 pose002 cycle.

B850 run_state and aa86 workpiece_checks are unchanged. No construction,
constitutive force, production tangent, controller or solver is evaluated.
The B52 consumer applies saved tensors; analytic HP energy is archived only.
A separate actual-production reference contract is required before execution.
"""
from __future__ import annotations
from time import perf_counter
STARTED = perf_counter()
import argparse
import ast
import hashlib
import importlib.util
from pathlib import Path
import shutil
import sys

parser = argparse.ArgumentParser(description=__doc__)
for name in ("repo", "input", "output", "contract"):
    parser.add_argument("--"+name, type=Path, required=True)
parser.add_argument("--time-limit", type=float, required=True)
ARGS = parser.parse_args()
ROOT = ARGS.repo.resolve()
SCRIPTS = ROOT/"hf_repo/scripts"
PRIVATE_CORE = Path(__file__).with_name("core_audit_mechanical.py")
CORE_PIN = "b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5"
WP_PIN = "aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938"
CONSUMER_PIN = "b52f8b5ab279321f6e716885dd00dae946929c4b7c23d97d98d9bcd7f5b593fe"
COUNTER_PIN = "b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3"
COUNTER_FILE = Path(__file__).with_name("counter_attempts.py")
sha_raw = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if sha_raw(PRIVATE_CORE) != CORE_PIN or sha_raw(SCRIPTS/"audit_native_workpiece_cycle.py") != WP_PIN:
    raise ValueError("Frozen reference mathematics changed")
sys.path[:0] = [str(Path(__file__).parent), str(SCRIPTS), str(ROOT/"hf_repo/src")]
from core_audit_mechanical import Audit as CoreAudit, MECHANICAL_AVAILABILITY
from audit_native_workpiece_cycle import (WorkpieceCycleAudit, CORE_PINS, PINS,
    GEOMETRY_ID, GEOMETRY_DESCRIPTOR_SHA, RSS_LIMIT, GATES, canonical_hash,
    npz, read, require, same_arrays, sha, verify_descriptor, verify_fields, write)
from audit_native_force import state_hash
import numpy as np

PREVIOUS = ROOT/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010"
PREVIOUS_FREEZE_PIN = "a4eb119f87899c1a2b12db9ef7209f0a73cf4d0d0ea72186bbef57a7e51cd03b"
COMPARISON_MODEL_PIN = "a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049"
TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]
BODY = dict(kind="fixed_rigid", shape="square", center_mm=[71.,40.], side_mm=16., fixed_components=[0,1])
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.1/16, time_limit_seconds=1500.)
OVERLAY = {"fixed_dofs", "free_dofs", "workpiece_cells", "workpiece_nodes", "workpiece_dofs",
           "workpiece_background_symmetry_overlap_dofs"}


class ShiftPoseAudit(CoreAudit, WorkpieceCycleAudit):
    # run_state and signed workpiece_checks resolve to the unchanged frozen methods.
    def __init__(self, args):
        super().__init__(args)
        self.repo = ROOT
        require(np.isfinite(self.limit) and self.limit > 0., "An explicit pre-frozen positive reference window is required")
        self.accounting = self.first_range_observation = self.tangent_range_observation = None

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "Shifted-square reference time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Shifted-square reference sampled RSS exceeds 8 GiB")
        require(not (self.output.parent/"stop_requested.txt").exists(), "Reference stop requested")

    def lifecycle(self, status, error=None):
        write(self.output/"lifecycle.json", dict(status=status,error=error,
            elapsed_seconds=perf_counter()-STARTED,HP_calls_started=self.hp_started,
            HP_calls_completed=self.hp_completed,checks_completed=self.checks,
            accepted_states_completed=len(self.rows),sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit,sampled_RSS_limit_bytes=RSS_LIMIT,
            stop_policy="First failure stops; no production evaluation or retry"))

    def load(self):
        contract_file = ARGS.contract.resolve()
        self.bind(contract_file)
        contract = read(contract_file)
        self.check(contract["schema_version"] == "shift-square-reference-contract-1.1"
            and contract["production_stage"] == self.stage.relative_to(self.repo).as_posix()
            and contract["limits"] == dict(helper_seconds=self.limit,outer_seconds=self.limit+60,sampled_RSS_bytes=RSS_LIMIT)
            and contract["workpiece"] == BODY and contract["targets_mm"] == TARGETS
            and self.stage.name == "run_001" and self.stage.parent.name == "shift_square_pose_002"
            and contract["counter_schema"] == "shift-complete-attempt-counter-1.0"
            and contract["counter_helper_sha256"] == COUNTER_PIN,
            "Wrong explicit shifted-square reference card")
        self.reference_contract = contract
        self.reference_contract_sha256 = sha(contract_file)
        self.check(contract["preceding_failure_scope"] == "Cost/closed-failure context only; no prefix reuse or failed-state qualification",
            "Prior failed pose card may only supply cost/failure context")
        for name,pin in contract["preceding_failed_pose001"].items(): self.bind(self.repo/name,pin)
        old_failure_file = self.repo/"lf_data_preparation/native_workpiece_001/shift_square_pose_001/run_001/result/result.json"
        self.check(contract["preceding_failed_pose001"].get(old_failure_file.relative_to(self.repo).as_posix()) == sha(old_failure_file)
            and read(old_failure_file)["status"] == "failed" and read(old_failure_file)["failure"]["code"] == "time_limit",
            "Prior pose001 is not the closed failed context")
        ref_sources = contract["reference_sources"]
        own = Path(__file__).resolve().relative_to(self.repo).as_posix()
        core = PRIVATE_CORE.relative_to(self.repo).as_posix()
        counter = COUNTER_FILE.relative_to(self.repo).as_posix()
        self.check(ref_sources.get(own) == sha(Path(__file__)) and ref_sources.get(core) == CORE_PIN
            and ref_sources.get(counter) == COUNTER_PIN and len({Path(n).name for n in ref_sources}) == len(ref_sources),
            "Independent reference source closure is not bound")
        ref_caps = self.output/"reference_sources"; ref_caps.mkdir()
        for name,pin in ref_sources.items():
            self.bind(self.repo/name,pin)
            shutil.copyfile(self.repo/name,ref_caps/Path(name).name)
            self.bind(ref_caps/Path(name).name,pin)
        # The counter helper is pure saved-data logic, imported only after its card pin is checked.
        self.bind(COUNTER_FILE,ref_sources[counter])
        spec = importlib.util.spec_from_file_location("shift_reference_counter",COUNTER_FILE)
        counter_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(counter_module)
        self.attempt_counts = counter_module.reconstruct
        inventory_file,receipt_file,freeze_file = (self.stage/n for n in
            ("input_inventory.json","execution_receipt.json","source_freeze.json"))
        for path,key in ((inventory_file,"input_inventory_sha256"),(receipt_file,"production_receipt_sha256"),
                         (freeze_file,"source_freeze_sha256")):
            self.bind(path,contract[key])
        inventory,receipt,freeze = map(read,(inventory_file,receipt_file,freeze_file))
        row = inventory["case"]
        self.check(inventory["schema_version"] == "native-workpiece-cycle-input-inventory-1.0"
            and inventory["baseline_commit"] == contract["baseline_commit"]
            and row["alias"] == "gripper_coarse_square_x71" and row["source_alias"] == "gripper_canonical"
            and row["targets_mm"] == TARGETS and row["geometry_id"] == GEOMETRY_ID
            and (row["elements"],row["dofs"],row["fixed_DOFs"],row["free_DOFs"]) == (3200,6642,376,6266)
            and all(row[k] == v for k,v in PINS.items()) and inventory["settings"] == SETTINGS
            and inventory["gates"] == GATES and inventory["source_freeze_sha256"] == sha(freeze_file)
            and all(inventory[k] == MECHANICAL_AVAILABILITY[k] for k in ("response_mode","response_contract","auxiliary_material_energy"))
            and inventory["execution_limits"] == dict(production_seconds=1500,production_outer_seconds=1560,
                sampled_RSS_bytes=RSS_LIMIT,preparation_seconds=120,preparation_outer_seconds=150),
            "Shifted pose inventory changed physics/settings or original gates")
        self.check(receipt["schema_version"] == "native-mean-execution-1.0" and receipt["status"] == "pass"
            and receipt["baseline_commit"] == inventory["baseline_commit"] and receipt["invocations"] == 1
            and receipt["input_inventory_sha256"] == sha(inventory_file)
            and receipt["source_freeze_sha256"] == sha(freeze_file)
            and receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
            and receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
            and receipt["seconds_limit"] == 1500 and receipt["sampled_RSS_limit_bytes"] == RSS_LIMIT
            and np.isfinite(receipt["elapsed_seconds"]) and 0 <= receipt["elapsed_seconds"] <= 1500
            and 0 <= receipt["sampled_peak_RSS_bytes"] <= RSS_LIMIT
            and receipt["force_hook_restored"] is receipt["tangent_hook_restored"] is True,
            "Complete production/frozen source/input/resource precondition failed")
        launch_file = self.repo/contract["production_launch_file"]
        self.bind(launch_file,contract["production_launch_sha256"])
        launch = read(launch_file)
        self.check(launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
            and launch["all_bindings_unchanged"] is True and launch["stop_reason"] is None
            and 0 <= launch["elapsed_seconds"] <= 1560 and 0 <= launch["peak_sampled_tree_RSS_bytes"] <= RSS_LIMIT,
            "Production terminal outcome/resource precondition failed")
        self.bind(PREVIOUS/"source_freeze.json",PREVIOUS_FREEZE_PIN)
        previous_sources = read(PREVIOUS/"source_freeze.json")["sources"]
        tangent_key = "hf_repo/src/hf_eval/split_numpy_tangent.py"
        transition = contract["source_transition"]
        self.check(set(transition) <= {tangent_key}
            and all(v["previous_sha256"] == previous_sources[n] for n,v in transition.items()),
            "Only the independently declared tangent-source transition is supported")
        expected = dict(previous_sources,**{n:v["current_sha256"] for n,v in transition.items()})
        sources = freeze["sources"]
        extra = set(sources)-set(previous_sources)
        self.check(freeze["schema_version"] == "native-workpiece-cycle-source-freeze-1.0"
            and freeze["inherited_source_freeze_sha256"] == PREVIOUS_FREEZE_PIN
            and freeze.get("source_transition",{}) == inventory["source_transition"] == transition
            and len(previous_sources) == 68 and len(sources) == inventory["source_count"] == 70
            and len({Path(n).name for n in sources}) == len(sources)
            and {Path(n).name for n in extra} == {"prepare_shift_pose.py","execute_shift_pose.py"}
            and all(sources.get(n) == pin for n,pin in expected.items()),
            "Production closure differs beyond explicit one-source transition and two wrappers")
        for name,pin in previous_sources.items(): self.bind(PREVIOUS/"sources"/Path(name).name,pin)
        for name,item in transition.items():
            for role in ("previous_capsule","qualification_protocol","qualification_launch","qualification_receipt"):
                self.bind(self.repo/item[role+"_file"],item[role+"_sha256"])
            self.check(item["previous_capsule_sha256"] == previous_sources[name],"Historical tangent capsule pin differs")
            repair_protocol,repair_launch,repair = (read(self.repo/item[k+"_file"]) for k in
                ("qualification_protocol","qualification_launch","qualification_receipt"))
            self.check(repair_protocol["schema_version"] == "t44-direction-scaling-repair-1.0"
                and repair_protocol["source_transition"] == dict(path=name,previous_sha256=item["previous_sha256"],current_sha256=item["current_sha256"])
                and repair_launch["protocol_sha256"] == item["qualification_protocol_sha256"]
                and repair_launch["status"] == repair["status"] == "pass" and repair_launch["exit_code"] == 0
                and repair_launch["all_bindings_unchanged"] is repair["all_bindings_unchanged"] is True
                and repair_launch["stop_reason"] is None and repair["pytest_exit_code"] == 0
                and all(repair["tests"][k] == 0 for k in ("errors","failures","skipped"))
                and repair["cached_tangent_started"] == repair["cached_tangent_completed"] == 2
                and repair["HP_calls_started"] == repair["HP_calls_completed"] == 2
                and repair["full_chunk_all_tensors_byte_equal"] is True and repair["local_and_global_checks"] == 9603
                and repair["production_force_changed"] is repair["range_guards_changed"] is False,
                "Declared bounded tangent transition has no completed independent proof")
        for name,pin in sources.items():
            self.bind(self.repo/name,pin); self.bind(self.stage/"sources"/Path(name).name,pin)
            shutil.copyfile(self.stage/"sources"/Path(name).name,self.output/"sources"/Path(name).name)
            self.bind(self.output/"sources"/Path(name).name,pin); self.sources[name] = pin
        for name,pin in inventory["input_bindings"].items(): self.bind(self.repo/name,pin)
        for name,pin in CORE_PINS.items(): self.check(sources["hf_repo/scripts/"+name] == pin,"Inherited HP/math helper changed")
        self.check(sources["hf_repo/scripts/audit_native_workpiece_cycle.py"] == WP_PIN
            and sources["hf_repo/src/hf_eval/tangent_action.py"] == CONSUMER_PIN,
            "Workpiece projection or saved-tensor consumer changed")
        for path in (inventory_file,receipt_file,freeze_file,contract_file):
            shutil.copyfile(path,self.output/path.name)
        for key,pin in (("geometry_file","geometry_file_sha256"),("geometry_npz_file","geometry_npz_sha256"),
            ("prior_model_file","prior_model_sha256"),("prior_task_file","prior_task_sha256"),
            ("task_file","task_file_sha256"),("direction_file","direction_file_sha256"),
            ("workpiece_model_file","workpiece_model_sha256"),("comparison_model_file","comparison_model_sha256")):
            self.bind(self.repo/row[key],row[pin])
        self.origin = self.stage/row["result_directory"]; self.result_file = self.origin/"result.json"
        self.bind(self.result_file,contract["production_result_sha256"])
        self.bind(self.result_file,receipt["result_sha256"])
        result = read(self.result_file); verify_descriptor(result)
        self.check(result["schema_version"] == "hf-native-mean-result-1.2" and result["status"] == "success"
            and all(result[k] is True for k in ("production_converged","target_reached","task_target_executed",
                "path_completed","loading_peak_reached","unload_endpoint_reached","lift_origin_zero","lift_shape_zero"))
            and result["path_kind"] == "ordered_cycle" and result["targets_mm"] == TARGETS
            and result["task_target_mm"] == 1.8 and result["reached_displacement"] == result["target_origin"] == 0.
            and result["settings"] == SETTINGS and result["backend"] == "numpy" and result["matrix_units"] == "N/mm"
            and result["k_out_N_per_mm"] == 0. and result["force_scale_per_length"] == 20. and result["failure"] is None
            and result["save_force_calls"] == result["save_tangent_calls"] == 0
            and all(result[k] is False for k in ("equilibrium_qualified","independent_HP_qualified","HF_qualified"))
            and result["tangent_execution"] == inventory["tangent_execution"]
                == dict(mode="chunk256",element_block_size=256,global_selector_scope="full_batch")
            and all(result[k] == receipt[k] == MECHANICAL_AVAILABILITY[k] for k in MECHANICAL_AVAILABILITY)
            and all(s["tangent_execution"] == result["tangent_execution"] for s in result["states"])
            and all(sources.get(n) == pin for n,pin in result["mechanics_source_sha256"].items()),
            "Complete mechanical cycle availability/cached execution/source scope differs")
        model_file,metadata_file = (self.origin/result["model"][k] for k in ("arrays_path","descriptor_path"))
        self.bind(model_file,contract["production_model_sha256"]); self.bind(model_file,receipt["model_sha256"])
        self.bind(model_file,result["model"]["arrays_sha256"])
        self.bind(metadata_file,result["model"]["descriptor_file_sha256"])
        model,metadata = npz(model_file),read(metadata_file); verify_descriptor(metadata)
        verify_fields(model,metadata["arrays"]["fields"])
        prior,prior_metadata = npz(self.repo/row["prior_model_file"]),read((self.repo/row["prior_model_file"]).with_suffix(".json"))
        self.bind((self.repo/row["prior_model_file"]).with_suffix(".json")); verify_descriptor(prior_metadata)
        self.check(prior_metadata["arrays"]["sha256"] == row["prior_model_sha256"],"Prior23 descriptor/array pin differs")
        intrinsic = set(prior)-{"fixed_dofs","free_dofs"}
        same_arrays({n:model[n] for n in intrinsic},{n:prior[n] for n in intrinsic},"Original21 intrinsic arrays")
        same_arrays(model,npz(self.repo/row["workpiece_model_file"]),"Declared shifted27 fixture arrays")
        self.check(row["comparison_model_sha256"] == COMPARISON_MODEL_PIN,"Prior x70 square comparison pin differs")
        comparison = npz(self.repo/row["comparison_model_file"])
        actual_delta = sorted(n for n in model if model[n].dtype != comparison[n].dtype
            or model[n].shape != comparison[n].shape or model[n].tobytes() != comparison[n].tobytes())
        self.check(set(model) == set(comparison) and actual_delta == sorted(OVERLAY)
            == row["expected_model_changed_fields"] == inventory["model_comparison"]["actual_changed_fields"]
            and inventory["model_comparison"]["parameter_case"] == "pose_only"
            and receipt["declared_workpiece_model_arrays_equal"] is True
            and receipt["declared_workpiece_model_sha256"] == row["workpiece_model_sha256"]
            and receipt["model_arrays_compared"] == 27 and receipt["model_comparison"] == inventory["model_comparison"],
            "Only the six declared kinematic overlay fields may differ")
        task,prior_task,previous_task = read(self.repo/row["task_file"]),read(self.repo/row["prior_task_file"]),read(PREVIOUS/"task.json")
        self.bind(PREVIOUS/"task.json",inventory["input_bindings"][(PREVIOUS/"task.json").relative_to(self.repo).as_posix()])
        descriptive = {"task_id","purpose","parameter_origin","description"}
        expected_task = dict(previous_task,workpiece=BODY)
        self.check({k:v for k,v in task.items() if k not in descriptive} == {k:v for k,v in expected_task.items() if k not in descriptive}
            and task["schema_version"] == "hf-native-project-task-1.1" and task["case_family"] == "gripper"
            and task["input"] == dict(prior_task["input"],target_mm=1.8)
            and task["workpiece"] == BODY and task["path"] == dict(kind="ordered_cycle",targets_mm=TARGETS)
            and metadata["schema_version"] == "hf-native-project-model-1.1" and metadata["task"] == task
            and metadata["task_sha256"] == result["task_sha256"] == receipt["task_sha256"] == canonical_hash(task)
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == sha(model_file),"Shifted task/model identity differs")
        self.check(all(metadata[k] == prior_metadata[k] for k in ("grid","model_extent","units","material","quadrature",
            "element_node_order","dof_order","analysis_grid_policy","native_geometry_preserved","qualification",
            "constraints_applied","material_assigned","task_created","response_evaluated")),"Original model/material semantics changed")
        source = metadata["source_geometry"]
        expected_source = dict(source,snapshot={k:"model/"+p for k,p in source["snapshot"].items()})
        self.check(source == prior_metadata["source_geometry"] and result["source_geometry"] == expected_source
            and source["geometry_id"] == GEOMETRY_ID and source["descriptor_sha256"] == GEOMETRY_DESCRIPTOR_SHA
            and source["descriptor_file_sha256"] == row["geometry_file_sha256"]
            and source["arrays_sha256"] == row["geometry_npz_sha256"],
            "Original geometry identity changed")
        for key,pin in (("descriptor","geometry_file_sha256"),("arrays","geometry_npz_sha256")):
            self.bind(self.origin/expected_source["snapshot"][key],row[pin])
        conn,coords = model["connectivity"],model["coordinates"]
        centres = coords[conn].mean(axis=1)
        cells = np.flatnonzero((centres[:,0] >= 63.) & (centres[:,0] <= 79.) & (centres[:,1] >= 32.) & (centres[:,1] <= 40.))
        nodes = np.unique(conn[cells]); dofs = (2*nodes[:,None]+np.arange(2)).ravel()
        groups = {n:prior_metadata["region_metadata"][n]["dofs"] for n in ("support","entity_symmetry","background_symmetry")}
        overlap = np.intersect1d(dofs,groups["background_symmetry"])
        extra_arrays = dict(workpiece_cells=cells,workpiece_nodes=nodes,workpiece_dofs=dofs,
            workpiece_background_symmetry_overlap_dofs=overlap)
        self.check(len(prior) == 23 and set(model) == set(prior)|set(extra_arrays)
            and (len(cells),len(nodes),len(dofs),len(overlap)) == (128,153,306,17)
            and all(model[n].dtype == np.dtype("int64") and np.array_equal(model[n],v) for n,v in extra_arrays.items())
            and all(np.array_equal(model[n],comparison[n]+offset) for n,offset in
                (("workpiece_cells",1),("workpiece_nodes",1),("workpiece_dofs",2),("workpiece_background_symmetry_overlap_dofs",2)))
            and np.all(npz(self.repo/row["geometry_npz_file"])["passive_void"].ravel()[cells])
            and not np.intersect1d(nodes,model["solid_nodes"]).size,"Independent shifted body cells/nodes/DOFs differ")
        regions,body = metadata["region_metadata"],metadata["region_metadata"]["workpiece"]
        fixed = np.union1d(prior["fixed_dofs"],dofs); edofs = (2*conn[:,:,None]+np.arange(2)).reshape(-1,8)
        self.check(len(fixed) == 376 and np.array_equal(fixed,model["fixed_dofs"])
            and np.array_equal(np.setdiff1d(np.arange(6642),fixed),model["free_dofs"])
            and np.array_equal(edofs,model["edofs"]) and regions["fixed_dofs"] == fixed.tolist()
            and all(regions[n] == prior_metadata["region_metadata"][n] for n in groups)
            and regions["ports"] == prior_metadata["region_metadata"]["ports"]
            and regions["source_background"] == prior_metadata["region_metadata"]["source_background"]
            and body["definition"] == BODY and body["initial_gaps_mm"] == dict(left=3.,bottom=2.)
            and all(body[n] == v.tolist() for n,v in (("cells",cells),("nodes",nodes),("dofs",dofs),("background_symmetry_overlap_dofs",overlap)))
            and regions["effective_boundary"] == dict(task_sha256=canonical_hash(task),
                fixed_dofs_sha256=hashlib.sha256(model["fixed_dofs"].astype("<i8").tobytes()).hexdigest(),
                workpiece_constraint_overlay=True,source_geometry_masks_preserved=True,source_material_arrays_preserved=True,
                material_phase_classification="original mechanism solid and original medium; workpiece is a kinematic overlay"),
            "Shifted fixed overlay or group metadata differs")
        self.check(regions["counts"] == result["counts"] == dict(prior_metadata["region_metadata"]["counts"],fixed_dofs=376,free_dofs=6266)
            and regions["solid_constraint_dofs"] == prior_metadata["region_metadata"]["solid_constraint_dofs"]
            and (body["selected_cells"],body["incident_nodes"],body["fixed_dofs"]) == (128,153,306)
            and np.flatnonzero(model["b_in"]).tolist() == [6156,6318,6480]
            and np.flatnonzero(model["b_out"]).tolist() == [4697,4859,5021]
            and model["b_in"][[6156,6318,6480]].tolist() == model["b_out"][[4697,4859,5021]].tolist() == [.25,.5,.25],
            "Material counts or signed port identities differ")
        directions = npz(self.repo/row["direction_file"]); v = directions["direction"]
        expected_v = model["b_in"]/abs(model["b_in"]).max(); expected_v[fixed] = 0.
        self.check(set(directions) == {"direction","multiplier_direction"} and v.dtype == np.dtype("float64")
            and v.shape == (6642,) and v.tobytes() == expected_v.tobytes()
            and hashlib.sha256(v.tobytes()).hexdigest() == row["direction_array_sha256"]
            and float(directions["multiplier_direction"]) == 0.,"Original fixed-compatible PORT direction differs")
        states = result["states"]; original = [s for s in states if s["is_original_target"]]
        self.check(len(states) >= len(TARGETS) and len(states) == result["accepted_states"] == receipt["accepted_states"]
            and [s["state_sha256"] for s in states] == receipt["state_sha256"]
            and [s["d"] for s in original] == TARGETS
            and [s["original_target_index"] for s in original] == list(range(len(TARGETS)))
            and all(s["original_target_displacement"] == TARGETS[i] for i,s in enumerate(original))
            and all(s["target_origin"] == 0. and s["physical_mean_target_mm"] == s["d"] for s in states)
            and states[0]["d"] == states[-1]["d"] == 0. and states[0]["leg"] == "origin"
            and states[0]["bisection_depth"] == 0
            and contract["actual_accepted_states"] == len(states)
            and contract["expected_new_HP80_120_calls"] == 2*len(states),"Every original target/actual accepted index must be retained")
        for a,b in zip(states,states[1:]):
            leg = b["original_target_index"]; oldleg = a["original_target_index"]
            self.check(type(leg) is int and 1 <= leg < len(TARGETS) and leg in (oldleg,oldleg+1)
                and (leg == oldleg or a["is_original_target"] is True)
                and b["original_target_displacement"] == TARGETS[leg]
                and b["leg"] == ("loading" if TARGETS[leg] > TARGETS[leg-1] else "unloading")
                and (a["d"] < b["d"] <= TARGETS[leg] if TARGETS[leg] > TARGETS[leg-1] else TARGETS[leg] <= b["d"] < a["d"])
                and 0 <= b["bisection_depth"] <= SETTINGS["max_bisections"],"Actual accepted leg/bisection order differs")
        self.model,self.edofs,self.direction = model,edofs,v
        self.inventory,self.receipt,self.result,self.metadata = inventory,receipt,result,metadata
        self.workpiece_dofs,self.groups = dofs,groups
        self.accounting = self.reconstruct_counts(result,receipt)
        self.check(receipt["observed_force_calls_completed"] == result["call_counts"]["force_calls_completed"]
            and receipt["observed_tangent_calls"] == result["call_counts"]["tangent_calls"]
            and receipt["observed_tangent_calls_completed"] == result["call_counts"]["tangent_calls_completed"],"Observed completed counters differ")
        self.first_range_observation = self.verify_first_range_observation(result,receipt,model)
        if self.accounting["all_Newton_base_and_tangent_calls_completed"]:
            self.check(receipt["first_tangent_range_input"] is None and not (self.stage/"first_tangent_range_input").exists(),
                "Complete tangent trace cannot contain an unexplained capture")
        else:
            self.tangent_range_observation = self.verify_tangent_range_observation(receipt,model)
        self.checkpoint()

    def reconstruct_counts(self,result,receipt):
        return self.attempt_counts(result,receipt,SETTINGS,self.check)


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
        self.checkpoint(); self.load()
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        self.reference_class = DecimalSplitQ1Reference
        for index,row in enumerate(self.result["states"]):
            self.run_state(index,row)
            self.workpiece_checks(index,row)
        self.check(self.hp_started == self.hp_completed == 2*len(self.result["states"]),"Fresh all-accepted HP coverage/calls differ")
        for path,pin in self.bindings.items(): self.check(sha(path) == pin,"Bound input/source changed: "+str(path))
        self.checkpoint()
        summary = dict(schema_version="native-workpiece-cycle-independent-audit-1.0",status="pass",
            alias="gripper_coarse_square_x71",source_alias="gripper_canonical",case_family="gripper",
            baseline_commit=self.inventory["baseline_commit"],audited_targets_mm=TARGETS,path_kind="ordered_cycle",workpiece=BODY,
            accepted_states=len(self.rows),states=self.rows,result_sha256=sha(self.result_file),
            checks_completed=self.checks,HP_calls_started=self.hp_started,HP_calls_completed=self.hp_completed,
            HP_matrix_columns_exhaustively_checked=False,full_element_and_DOF_coverage=True,
            gates=GATES,global_scatter_precision=3000,global_scatter_inexact_trap=True,
            reference_scope="All actual accepted states/elements/real DOFs; fixed-lift PORT direction, deltaR=0; original signed workpiece and disjoint holding projections",
            qualification="Accepted mechanical states of this explicit complete x71 pose002 coarse square cycle; no pressure, clamp, contact, auxiliary energy, stress-HP, rejected-state, all-column, H2/H3 or HF5 qualification",
            **MECHANICAL_AVAILABILITY,analytic_HP_energy_scope="Archived reference only, without candidate comparison or energy qualification",
            contact_qualified=False,clamp_qualified=False,pressure_qualified=False,
            original_run_state_source_sha256=CORE_PINS["audit_native_mean.py"],private_run_state_source_sha256=CORE_PIN,
            inherited_workpiece_checker_sha256=WP_PIN,tangent_action_consumer_sha256=CONSUMER_PIN,
            tangent_execution=self.result["tangent_execution"],counter_accounting=self.accounting,counter_helper_sha256=COUNTER_PIN,
            first_force_range_input=self.first_range_observation,first_tangent_range_input=self.tangent_range_observation,
            independent_reference_contract_sha256=self.reference_contract_sha256,
            independent_reference_source_bindings=self.reference_contract["reference_sources"],
            source_bindings=self.sources,input_bindings={p.relative_to(self.repo).as_posix():h for p,h in self.bindings.items()},
            candidate_force_calls=0,tangent_calls=0,solver_calls=0,model_constructions=0,
            elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit,sampled_RSS_limit_bytes=RSS_LIMIT)
        write(self.output/"summary.json",summary); self.checkpoint(); self.lifecycle("pass"); self.checkpoint()
        print(dict(status="pass",accepted_states=len(self.rows),HP_calls=self.hp_completed,checks_completed=self.checks),flush=True)
        self.checkpoint()


def main():
    require(np.isfinite(ARGS.time_limit) and ARGS.time_limit > 0.,"Reference window must be explicitly supplied and pre-frozen")
    audit = ShiftPoseAudit(ARGS)
    try:
        audit.run()
    except BaseException as error:
        audit.lifecycle("not_pass",repr(error))
        write(audit.output/"summary.json",dict(status="not_pass",error=repr(error),states=audit.rows,
            accepted_states=len(audit.rows),HP_calls_started=audit.hp_started,HP_calls_completed=audit.hp_completed,
            checks_completed=audit.checks,elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__":
    main()
