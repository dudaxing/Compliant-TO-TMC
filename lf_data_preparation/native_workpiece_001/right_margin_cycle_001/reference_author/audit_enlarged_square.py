"""Fresh accepted-state reference for the complete x71 side18 port-projection cycle.

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
COUNTER_PIN = "a751fe07a682ff89c88b16d8d69325b1990d45c26114b8715414116580737ed9"
ORIGINAL_COUNTER_PIN = "b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3"
COUNTER_SCHEMA = "shift-complete-attempt-counter-recovered-invalid-J-1.1"
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

TARGETS = [0., .25, .5, .65, .75, .8, .85, .9, .95, 1., 1.05, 1.1, 1.15, 1.2, 1.15, 1.1, 1., .9, .8, .75, .65, .5, .25, 0.]
BODY = dict(kind="fixed_rigid", shape="square", center_mm=[71.,40.], side_mm=18., fixed_components=[0,1])
INITIAL_GUESS = "port_projection"
PREDICTOR_INITIALIZATION = dict(displacement_mode=INITIAL_GUESS, applied_dw=False, applied_dR=True,
    port_adjustment="distributed normalized free-port weights", predictor_LU_role="reaction increment estimator",
    linear_residual_scope="Actual computed KKT solution; not the applied displacement seed.")
SETTINGS = dict(tolerance=1e-9, constraint_tolerance=1e-10, displacement_scale_floor=1e-6,
    force_scale_floor_factor=1e-8, max_checks=25, armijo_c=1e-4, max_backtracks=12,
    max_bisections=4, minimum_increment=.1/16, time_limit_seconds=4500.)
OVERLAY = {"fixed_dofs", "free_dofs", "workpiece_cells", "workpiece_nodes", "workpiece_dofs",
           "workpiece_background_symmetry_overlap_dofs"}


class EnlargedSquareContactAudit(CoreAudit, WorkpieceCycleAudit):
    # run_state and signed workpiece_checks resolve to the unchanged frozen methods.
    def __init__(self, args):
        super().__init__(args)
        self.repo = ROOT
        require(np.isfinite(self.limit) and self.limit > 0., "An explicit pre-frozen positive reference window is required")
        self.accounting = self.first_range_observation = self.tangent_range_observation = None

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "Enlarged-square reference time limit exceeded")
        require(self.peak <= RSS_LIMIT, "Enlarged-square reference sampled RSS exceeds 8 GiB")
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
        self.check(contract["schema_version"] == "right-margin-reference-contract-1.0"
            and contract["production_stage"] == self.stage.relative_to(self.repo).as_posix()
            and contract["limits"] == dict(helper_seconds=self.limit,outer_seconds=self.limit+60,sampled_RSS_bytes=RSS_LIMIT)
            and self.limit == 1500. and contract["workpiece"] == BODY and contract["targets_mm"] == TARGETS
            and self.stage.name == "run_001" and self.stage.parent.name == "right_margin_cycle_001"
            and contract["initial_guess"] == INITIAL_GUESS and contract["predictor_initialization"] == PREDICTOR_INITIALIZATION
            and contract["counter_schema"] == COUNTER_SCHEMA and contract["counter_helper_sha256"] == COUNTER_PIN
            and contract["gamma"] == 1e-6 and contract["parameter_case"] == "right_medium_domain_margin"
            and contract["direction_archive_fields"] == ["direction"] and contract["multiplier_direction"] == 0.
            and contract["comparison_baseline_stage"] == "lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/run_001"
            and contract["preparation_stage"] == "lf_data_preparation/native_workpiece_001/right_margin_preparation_001/run_001"
            and isinstance(contract["reference_budget_basis"],str) and contract["reference_budget_basis"].strip(),
            "Wrong explicit right-margin reference card")
        self.reference_contract,self.reference_contract_sha256 = contract,sha(contract_file)
        ref_sources = contract["reference_sources"]
        own = Path(__file__).resolve().relative_to(self.repo).as_posix()
        core = PRIVATE_CORE.relative_to(self.repo).as_posix()
        counter = COUNTER_FILE.relative_to(self.repo).as_posix()
        self.check(ref_sources.get(own) == sha(Path(__file__)) and ref_sources.get(core) == CORE_PIN
            and ref_sources.get(counter) == COUNTER_PIN and len({Path(p).name for p in ref_sources}) == len(ref_sources) == 37,"Reference closure differs")
        original_counter = Path(__file__).with_name("counter_original_B028.py").relative_to(self.repo).as_posix()
        self.check(ref_sources.get(original_counter) == ORIGINAL_COUNTER_PIN,"Original B028 role differs")
        ref_caps = self.output/"reference_sources";ref_caps.mkdir()
        for name,pin in ref_sources.items():
            self.bind(self.repo/name,pin)
            shutil.copyfile(self.repo/name,ref_caps/Path(name).name)
            self.bind(ref_caps/Path(name).name,pin)
        from reference_contract_builder import verify_complete_production,verify_accounting_transition,verify_padding_arrays,COUNTS
        inventory,receipt,freeze,result = verify_complete_production(self.repo,self.stage,self.bind)
        self.check(contract["input_inventory_sha256"] == sha(self.stage/"input_inventory.json")
            and contract["production_receipt_sha256"] == sha(self.stage/"execution_receipt.json")
            and contract["source_freeze_sha256"] == sha(self.stage/"source_freeze.json")
            and contract["baseline_commit"] == inventory["baseline_commit"]
            and contract["production_launch_file"] == (self.stage.parent/"production_launch.json").relative_to(self.repo).as_posix()
            and contract["production_launch_sha256"] == sha(self.stage.parent/"production_launch.json"),"Production card pins differ")
        verify_accounting_transition(self.repo,self.stage.parent,contract["accounting_source_transition"],self.bind)
        self.bind(COUNTER_FILE,ref_sources[counter])
        spec = importlib.util.spec_from_file_location("shift_reference_counter",COUNTER_FILE)
        counter_module = importlib.util.module_from_spec(spec);spec.loader.exec_module(counter_module)
        self.attempt_counts = counter_module.reconstruct
        sources = freeze["sources"]
        self.check({p:pin for p,pin in sources.items() if p.startswith("hf_repo/src/hf_eval/")} ==
            {p:pin for p,pin in ref_sources.items() if p.startswith("hf_repo/src/hf_eval/")},"Production/reference core identities differ")
        for name,pin in sources.items():
            self.bind(self.repo/name,pin);self.bind(self.stage/"sources"/Path(name).name,pin)
            shutil.copyfile(self.stage/"sources"/Path(name).name,self.output/"sources"/Path(name).name)
            self.bind(self.output/"sources"/Path(name).name,pin);self.sources[name] = pin
        for name,pin in CORE_PINS.items():
            self.check(ref_sources["hf_repo/scripts/"+name] == pin,"HP/math helper changed")
        self.check(ref_sources["hf_repo/scripts/audit_native_workpiece_cycle.py"] == WP_PIN
            and sources["hf_repo/src/hf_eval/tangent_action.py"] == CONSUMER_PIN,"Workpiece/PORT consumer changed")
        for file in ("input_inventory.json","execution_receipt.json","source_freeze.json"):
            shutil.copyfile(self.stage/file,self.output/file)
        shutil.copyfile(contract_file,self.output/contract_file.name)
        row = inventory["case"]
        for key,pin in (("geometry_file","geometry_file_sha256"),("geometry_npz_file","geometry_npz_sha256"),
            ("task_file","task_file_sha256"),("direction_file","direction_file_sha256"),
            ("workpiece_model_file","workpiece_model_sha256"),("comparison_model_file","comparison_model_sha256")):
            self.bind(self.repo/row[key],row[pin])
        self.origin = self.stage/row["result_directory"];self.result_file = self.origin/"result.json"
        self.bind(self.result_file,contract["production_result_sha256"])
        verify_descriptor(result)
        self.check(result["schema_version"] == "hf-native-mean-result-1.2" and result["status"] == "success"
            and all(result[k] is True for k in ("production_converged","target_reached","task_target_executed",
                "path_completed","loading_peak_reached","unload_endpoint_reached","lift_origin_zero","lift_shape_zero"))
            and result["path_kind"] == "ordered_cycle" and result["targets_mm"] == TARGETS
            and result["task_target_mm"] == 1.2 and result["reached_displacement"] == result["target_origin"] == 0.
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
        comparison_file = self.repo/row["comparison_model_file"]
        comparison_metadata_file = comparison_file.with_suffix(".json")
        self.bind(comparison_metadata_file)
        comparison,comparison_metadata = npz(comparison_file),read(comparison_metadata_file)
        verify_descriptor(comparison_metadata);verify_fields(comparison,comparison_metadata["arrays"]["fields"])
        same_arrays(model,npz(self.repo/row["workpiece_model_file"]),"Declared padded27 fixture arrays")
        maps,actual_comparison = verify_padding_arrays(np,comparison,model,comparison_metadata,metadata)
        prep = self.repo/self.reference_contract["preparation_stage"]
        prep_comparison_file = prep/"model_comparison.json"
        self.bind(prep_comparison_file,inventory["model_comparison"]["preparation_comparison_sha256"])
        self.check(actual_comparison == read(prep_comparison_file),"All27 saved physical mapping comparisons differ")
        expected_delta = sorted(n for n,v in actual_comparison["fields"].items() if not v["raw_equal"])
        self.check(expected_delta == inventory["model_comparison"]["actual_changed_fields"]
            and actual_comparison["raw_equal_fields"] == inventory["model_comparison"]["unchanged_fields"],"Explicit padding raw-field delta differs")
        task,baseline_task = read(self.repo/row["task_file"]),comparison_metadata["task"]
        descriptive = {"task_id","purpose","parameter_origin","description"}
        expected_task = dict(baseline_task,geometry=task["geometry"],background_symmetry=dict(points_mm=[[0.,40.],[82.,40.]],components=[1]))
        self.check({k:v for k,v in task.items() if k not in descriptive} == {k:v for k,v in expected_task.items() if k not in descriptive}
            and task["schema_version"] == "hf-native-project-task-1.1" and task["case_family"] == "gripper"
            and task["workpiece"] == BODY and task["path"] == dict(kind="ordered_cycle",targets_mm=TARGETS)
            and metadata["schema_version"] == "hf-native-project-model-1.1" and metadata["task"] == task
            and metadata["task_sha256"] == result["task_sha256"] == receipt["task_sha256"] == canonical_hash(task)
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == sha(model_file),"New right-margin task/model identity differs")
        self.check(metadata["material"] == comparison_metadata["material"]
            and task["third_medium"] == baseline_task["third_medium"] == dict(gamma=1e-6)
            and task["regularization"] == baseline_task["regularization"] == dict(alpha=1e-6,length_mm=80.)
            and metadata["material"]["force_scale_per_length"] == 20.,"Original material and Lr80 must remain exact")
        self.check(all(metadata[k] == comparison_metadata[k] for k in ("model_extent","units","quadrature",
            "element_node_order","dof_order","analysis_grid_policy","native_geometry_preserved",
            "constraints_applied","material_assigned","task_created","response_evaluated")),"Unchanged model semantics differ")
        source = metadata["source_geometry"]
        expected_source = dict(source,snapshot={k:"model/"+p for k,p in source["snapshot"].items()})
        geometry = read(self.repo/row["geometry_file"])
        verify_descriptor(geometry)
        self.check(source["geometry_id"] == task["geometry"]["geometry_id"] == geometry["geometry_id"] == row["geometry_id"]
            and source["descriptor_sha256"] == task["geometry"]["descriptor_sha256"] == geometry["descriptor_sha256"]
            and source["geometry_id"] != GEOMETRY_ID and source["descriptor_sha256"] != GEOMETRY_DESCRIPTOR_SHA
            and result["source_geometry"] == expected_source
            and source["descriptor_file_sha256"] == row["geometry_file_sha256"]
            and source["arrays_sha256"] == row["geometry_npz_sha256"],"Derived HF geometry identity differs")
        derivation = geometry["provenance"]["hf_analysis_domain_derivations"][-1]
        parent_file = self.repo/"lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/run_001/result/model/source_geometry/geometry.json"
        self.bind(parent_file);parent_geometry = read(parent_file)
        self.bind(parent_file.with_suffix(".npz"))
        self.check(derivation["operation"] == "right_passive_void_padding" and derivation["right_columns"] == 2
            and derivation["margin_mm"] == 2. and derivation["parent_cell_slice_yx"] == [[0,40],[0,80]]
            and derivation["parent_hf_geometry"]["geometry_id"] == GEOMETRY_ID
            and derivation["parent_hf_geometry"]["descriptor_sha256"] == GEOMETRY_DESCRIPTOR_SHA
            and derivation["parent_hf_geometry"]["geometry_json_sha256"] == sha(parent_file)
            and derivation["parent_hf_geometry"]["geometry_npz_sha256"] == sha(parent_file.with_suffix(".npz"))
            and geometry["provenance"]["lf_v2"] == parent_geometry["provenance"]["lf_v2"]
            and geometry["region_tags"] == parent_geometry["region_tags"]
            and geometry["processing"]["whole_grid_is_LF_native"] is False
            and geometry["processing"]["background_boundary_applied"] is False,"HF derivation and retained LF history differ")
        expected_grid = dict(parent_geometry["grid"],shape_yx=[40,82],extent_mm=[82.,40.])
        self.check(metadata["grid"] == geometry["grid"] == expected_grid,"Derived domain grid differs")
        padded_masks,parent_masks = npz(self.repo/row["geometry_npz_file"]),npz(parent_file.with_suffix(".npz"))
        self.check(set(padded_masks) == set(parent_masks) and all(padded_masks[k].dtype == parent_masks[k].dtype
            and padded_masks[k].shape == (40,82) and padded_masks[k][:,:80].tobytes() == parent_masks[k].tobytes()
            and np.all(padded_masks[k][:,80:] == (1 if k == "passive_void" else 0)) for k in parent_masks),"Original four masks and added medium columns differ")
        for key,pin in (("descriptor","geometry_file_sha256"),("arrays","geometry_npz_sha256")):
            self.bind(self.origin/expected_source["snapshot"][key],row[pin])
        conn,coords = model["connectivity"],model["coordinates"]
        centres = coords[conn].mean(axis=1)
        cells = np.flatnonzero((centres[:,0] >= 62.) & (centres[:,0] <= 80.) & (centres[:,1] >= 31.) & (centres[:,1] <= 40.))
        nodes = np.unique(conn[cells]);dofs = (2*nodes[:,None]+np.arange(2)).ravel()
        regions,body = metadata["region_metadata"],metadata["region_metadata"]["workpiece"]
        groups = {n:regions[n]["dofs"] for n in ("support","entity_symmetry","background_symmetry")}
        top_nodes = np.flatnonzero(coords[:,1] == 40.)
        self.check(groups["background_symmetry"] == (2*top_nodes+1).tolist()
            and regions["background_symmetry"]["points_mm"] == [[0.,40.],[82.,40.]],"Applied full-domain top constraint differs")
        overlap = np.intersect1d(dofs,groups["background_symmetry"])
        self.check((len(cells),len(nodes),len(dofs),len(overlap)) == (162,190,380,19)
            and all(np.array_equal(model[name],value) for name,value in
                dict(workpiece_cells=cells,workpiece_nodes=nodes,workpiece_dofs=dofs,workpiece_background_symmetry_overlap_dofs=overlap).items())
            and np.all(padded_masks["passive_void"].ravel()[cells])
            and not np.intersect1d(nodes,model["solid_nodes"]).size,"Independent body coverage differs")
        expected_body = dict(comparison_metadata["region_metadata"]["workpiece"],cells=cells.tolist(),nodes=nodes.tolist(),dofs=dofs.tolist(),background_symmetry_overlap_dofs=overlap.tolist())
        fixed = np.unique(np.concatenate([np.asarray(value) for value in groups.values()]+[dofs]))
        edofs = (2*conn[:,:,None]+np.arange(2)).reshape(-1,8)
        self.check(len(fixed) == 450 and np.array_equal(fixed,model["fixed_dofs"])
            and np.array_equal(np.setdiff1d(np.arange(6806),fixed),model["free_dofs"])
            and np.array_equal(edofs,model["edofs"]) and regions["fixed_dofs"] == fixed.tolist()
            and regions["source_background"] == comparison_metadata["region_metadata"]["source_background"]
            and body == expected_body and body["definition"] == BODY
            and regions["effective_boundary"] == dict(task_sha256=canonical_hash(task),
                fixed_dofs_sha256=hashlib.sha256(model["fixed_dofs"].astype("<i8").tobytes()).hexdigest(),
                workpiece_constraint_overlay=True,source_geometry_masks_preserved=True,source_material_arrays_preserved=True,
                material_phase_classification="original mechanism solid and original medium; workpiece is a kinematic overlay"),"Mapped fixed overlay/groups differ")
        inlet_nodes = np.flatnonzero((coords[:,0] == 0.) & np.isin(coords[:,1],[38.,39.,40.]))
        outlet_nodes = np.flatnonzero((coords[:,0] == 80.) & np.isin(coords[:,1],[28.,29.,30.]))
        self.check(regions["counts"] == result["counts"] == COUNTS
            and regions["solid_constraint_dofs"] == maps["dof_map"][comparison_metadata["region_metadata"]["solid_constraint_dofs"]].tolist()
            and np.array_equal(np.flatnonzero(model["b_in"]),2*inlet_nodes)
            and np.array_equal(np.flatnonzero(model["b_out"]),2*outlet_nodes+1)
            and model["b_in"][2*inlet_nodes].tolist() == model["b_out"][2*outlet_nodes+1].tolist() == [.25,.5,.25],"Actual counts/physical ports differ")
        directions = npz(self.repo/row["direction_file"]);v = directions["direction"]
        expected_v = model["b_in"]/abs(model["b_in"]).max();expected_v[fixed] = 0.
        self.check(set(directions) == set(contract["direction_archive_fields"]) and v.dtype == np.dtype("float64")
            and v.shape == (6806,) and v.tobytes() == expected_v.tobytes()
            and hashlib.sha256(v.tobytes()).hexdigest() == row["direction_array_sha256"]
            and contract["multiplier_direction"] == 0.,"New fixed-compatible6806 PORT direction differs")
        placement = contract["boundary_placement"]
        self.check(placement == dict(body_box_mm=[62.,80.,31.,40.],right_outer_boundary_mm=82.,right_medium_margin_mm=2.,workpiece_touches_analysis_boundary=False)
            and coords[:,0].max() == 82.,"Explicit right-medium boundary placement differs")
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
        self.check(all(arrays[key].dtype == np.dtype("float64") and arrays[key].shape == (len(model["coordinates"])*2,)
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
        self.check(all(arrays[k].dtype == np.dtype("float64") and arrays[k].shape == (len(model["coordinates"])*2,)
                and np.isfinite(arrays[k]).all() for k in ("lift","fluctuation"))
            and np.count_nonzero(arrays["lift"]) == 0
            and np.count_nonzero(arrays["fluctuation"][model["fixed_dofs"]]) == 0
            and state_hash(arrays) == observation["state_sha256"]
            and all(np.isfinite(v).all() for v in fields.values())
            and fields["J"].shape == (len(model["connectivity"]),9) and np.all(fields["J"] > 0)
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
            alias="gripper_coarse_square_x71_side18_right_margin2",source_alias="gripper_canonical",case_family="gripper",
            baseline_commit=self.inventory["baseline_commit"],audited_targets_mm=TARGETS,path_kind="ordered_cycle",workpiece=BODY,
            accepted_states=len(self.rows),states=self.rows,result_sha256=sha(self.result_file),
            checks_completed=self.checks,HP_calls_started=self.hp_started,HP_calls_completed=self.hp_completed,
            HP_matrix_columns_exhaustively_checked=False,full_element_and_DOF_coverage=True,
            gates=GATES,global_scatter_precision=3000,global_scatter_inexact_trap=True,
            reference_scope="All actual accepted states/elements/real DOFs; fixed-lift PORT direction, deltaR=0; original signed workpiece and disjoint holding projections",
            qualification="Accepted mechanical states of this explicit complete gamma1e-6 x71 side18 coarse square cycle with2mm right medium margin; no pressure, clamp, contact, auxiliary energy, stress-HP, rejected-state, all-column, H2/H3 or HF5 qualification",
            **MECHANICAL_AVAILABILITY,analytic_HP_energy_scope="Archived reference only, without candidate comparison or energy qualification",
            contact_qualified=False,clamp_qualified=False,pressure_qualified=False,
            original_run_state_source_sha256=CORE_PINS["audit_native_mean.py"],private_run_state_source_sha256=CORE_PIN,
            inherited_workpiece_checker_sha256=WP_PIN,tangent_action_consumer_sha256=CONSUMER_PIN,
            tangent_execution=self.result["tangent_execution"],counter_accounting=self.accounting,counter_helper_sha256=COUNTER_PIN,
            counter_schema=COUNTER_SCHEMA,accounting_source_transition=self.reference_contract["accounting_source_transition"],
            first_force_range_input=self.first_range_observation,first_tangent_range_input=self.tangent_range_observation,
            comparison_baseline_stage=self.reference_contract["comparison_baseline_stage"],
            initial_guess=self.result["initial_guess"],predictor_initialization=self.receipt["predictor_initialization"],
            parameter_case="right_medium_domain_margin",
            gamma=1e-6,
            prerequisite_scope="Identity and cost contexts only; no reference or new-state qualification is inherited",
            boundary_placement=self.reference_contract["boundary_placement"],
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
    audit = EnlargedSquareContactAudit(ARGS)
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
