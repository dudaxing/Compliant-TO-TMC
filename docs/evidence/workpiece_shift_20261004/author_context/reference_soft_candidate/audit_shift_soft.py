"""Future softened x71 square reference; load/material roles only are new.

Requires genuine complete pose002 production plus fresh HP qualification,
then independent fresh2N reference of this separate soft case. Not executed.
"""
from time import perf_counter
_SOFT_STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
POSE_INTERFACE_PIN = "0fcf7f372ccdc10dbf0f66e3473ae59282b8667663e6e070f0a5a1625f87c9ea"
_pose_file = Path(__file__).with_name("audit_shift_pose.py")
if sha256(_pose_file.read_bytes()).hexdigest() != POSE_INTERFACE_PIN:
    raise ValueError("Approved pose reference interface source changed")
from audit_shift_pose import *
STARTED = _SOFT_STARTED
SETTINGS = dict(SETTINGS,time_limit_seconds=1800.)
MATERIAL_FIELDS = {"lam","mu","gamma","force_scale_per_length"}


class SoftShiftAudit(ShiftPoseAudit):
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
        self.check(contract["schema_version"] == "shift-square-softened-reference-contract-1.0"
            and contract["production_stage"] == self.stage.relative_to(self.repo).as_posix()
            and contract["limits"] == dict(helper_seconds=self.limit,outer_seconds=self.limit+60,sampled_RSS_bytes=RSS_LIMIT)
            and contract["workpiece"] == BODY and contract["targets_mm"] == TARGETS
            and self.stage.name == "run_001" and self.stage.parent.name == "shift_square_soft_001"
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
            and row["alias"] == "gripper_coarse_square_x71_soft" and row["source_alias"] == "gripper_canonical"
            and row["targets_mm"] == TARGETS and row["geometry_id"] == GEOMETRY_ID
            and (row["elements"],row["dofs"],row["fixed_DOFs"],row["free_DOFs"]) == (3200,6642,376,6266)
            and all(row[k] == v for k,v in PINS.items()) and inventory["settings"] == SETTINGS
            and inventory["gates"] == GATES and inventory["source_freeze_sha256"] == sha(freeze_file)
            and all(inventory[k] == MECHANICAL_AVAILABILITY[k] for k in ("response_mode","response_contract","auxiliary_material_energy"))
            and inventory["execution_limits"] == dict(production_seconds=1800,production_outer_seconds=1860,
                sampled_RSS_bytes=RSS_LIMIT,preparation_seconds=120,preparation_outer_seconds=150),
            "Shifted pose inventory changed physics/settings or original gates")
        self.check(receipt["schema_version"] == "native-mean-execution-1.0" and receipt["status"] == "pass"
            and receipt["baseline_commit"] == inventory["baseline_commit"] and receipt["invocations"] == 1
            and receipt["input_inventory_sha256"] == sha(inventory_file)
            and receipt["source_freeze_sha256"] == sha(freeze_file)
            and receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
            and receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
            and receipt["seconds_limit"] == 1800 and receipt["sampled_RSS_limit_bytes"] == RSS_LIMIT
            and np.isfinite(receipt["elapsed_seconds"]) and 0 <= receipt["elapsed_seconds"] <= 1800
            and 0 <= receipt["sampled_peak_RSS_bytes"] <= RSS_LIMIT
            and receipt["force_hook_restored"] is receipt["tangent_hook_restored"] is True,
            "Complete production/frozen source/input/resource precondition failed")
        launch_file = self.repo/contract["production_launch_file"]
        self.bind(launch_file,contract["production_launch_sha256"])
        launch = read(launch_file)
        self.check(launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
            and launch["all_bindings_unchanged"] is True and launch["stop_reason"] is None
            and 0 <= launch["elapsed_seconds"] <= 1860 and 0 <= launch["peak_sampled_tree_RSS_bytes"] <= RSS_LIMIT,
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
            and result["k_out_N_per_mm"] == 0. and result["force_scale_per_length"] == 10. and result["failure"] is None
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
        intrinsic = set(prior)-{"fixed_dofs","free_dofs"}-MATERIAL_FIELDS
        same_arrays({n:model[n] for n in intrinsic},{n:prior[n] for n in intrinsic},"Original17 non-material intrinsic arrays")
        same_arrays(model,npz(self.repo/row["workpiece_model_file"]),"Declared shifted27 fixture arrays")
        self.check(row["comparison_model_sha256"] == COMPARISON_MODEL_PIN,"Prior x70 square comparison pin differs")
        comparison = npz(self.repo/row["comparison_model_file"])
        actual_delta = sorted(n for n in model if model[n].dtype != comparison[n].dtype
            or model[n].shape != comparison[n].shape or model[n].tobytes() != comparison[n].tobytes())
        self.check(set(model) == set(comparison) and actual_delta == sorted(OVERLAY|MATERIAL_FIELDS)
            == row["expected_model_changed_fields"] == inventory["model_comparison"]["actual_changed_fields"]
            and inventory["model_comparison"]["parameter_case"] == "explicit_softened_parameters"
            and receipt["declared_workpiece_model_arrays_equal"] is True
            and receipt["declared_workpiece_model_sha256"] == row["workpiece_model_sha256"]
            and receipt["model_arrays_compared"] == 27 and receipt["model_comparison"] == inventory["model_comparison"],
            "Only six overlay and four explicit material fields may differ from original x70")
        task,prior_task,previous_task = read(self.repo/row["task_file"]),read(self.repo/row["prior_task_file"]),read(PREVIOUS/"task.json")
        self.bind(PREVIOUS/"task.json",inventory["input_bindings"][(PREVIOUS/"task.json").relative_to(self.repo).as_posix()])
        descriptive = {"task_id","purpose","parameter_origin","description"}
        expected_task = dict(previous_task,workpiece=BODY,
            material=dict(previous_task["material"],E_MPa=.5),third_medium=dict(gamma=2e-6),
            regularization=dict(previous_task["regularization"],alpha=2e-6))
        self.check({k:v for k,v in task.items() if k not in descriptive} == {k:v for k,v in expected_task.items() if k not in descriptive}
            and task["schema_version"] == "hf-native-project-task-1.1" and task["case_family"] == "gripper"
            and task["input"] == dict(prior_task["input"],target_mm=1.8)
            and task["workpiece"] == BODY and task["path"] == dict(kind="ordered_cycle",targets_mm=TARGETS)
            and metadata["schema_version"] == "hf-native-project-model-1.1" and metadata["task"] == task
            and metadata["task_sha256"] == result["task_sha256"] == receipt["task_sha256"] == canonical_hash(task)
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == sha(model_file),"Shifted task/model identity differs")
        self.check(all(metadata[k] == prior_metadata[k] for k in ("grid","model_extent","units","quadrature",
            "element_node_order","dof_order","analysis_grid_policy","native_geometry_preserved","qualification",
            "constraints_applied","material_assigned","task_created","response_evaluated")),"Original non-material model semantics changed")
        pose = inventory["prerequisite_pose_reference"]
        self.check(contract["qualified_pose"] == pose and pose["stage"] == "lf_data_preparation/native_workpiece_001/shift_square_pose_002",
            "The softened case has no explicit genuine pose002 prerequisite")
        for name,pin in pose["files"].items(): self.bind(self.repo/name,pin)
        for role in ("model","task","result","summary"):
            self.bind(self.repo/pose[role+"_file"],pose[role+"_sha256"])
            self.check(pose["files"].get(pose[role+"_file"]) == pose[role+"_sha256"], "Pose role is outside its bound proof files")
        pose_control = self.repo/pose["stage"]
        pose_launch,pose_ref_launch,pose_lifecycle = (read(pose_control/name) for name in
            ("production_launch.json","reference_launch.json","reference/lifecycle.json"))
        pose_contract,pose_ref_protocol = read(pose_control/"reference_contract.json"),read(pose_control/"reference_protocol.json")
        pose_result,pose_summary,pose_task = (read(self.repo/pose[k+"_file"]) for k in ("result","summary","task"))
        self.check(pose_launch["status"] == pose_ref_launch["status"] == pose_lifecycle["status"] == pose_summary["status"] == "pass"
            and pose_launch["exit_code"] == pose_ref_launch["exit_code"] == 0
            and pose_launch["stop_reason"] is pose_ref_launch["stop_reason"] is None
            and pose_launch["all_bindings_unchanged"] is pose_ref_launch["all_bindings_unchanged"] is True
            and pose_result["status"] == "success" and pose_result["failure"] is None
            and pose_summary["alias"] == "gripper_coarse_square_x71" and pose_summary["audited_targets_mm"] == TARGETS
            and pose_summary["result_sha256"] == pose_contract["production_result_sha256"] == pose["result_sha256"]
            and pose_contract["production_model_sha256"] == pose["model_sha256"]
            and pose_summary["independent_reference_contract_sha256"] == sha(pose_control/"reference_contract.json")
            and pose_ref_launch["protocol_sha256"] == sha(pose_control/"reference_protocol.json")
            and pose_ref_launch["bindings"] == pose_ref_protocol["bindings"]
            and pose_summary["accepted_states"] == pose_result["accepted_states"] == len(pose_result["states"])
            and pose_summary["HP_calls_started"] == pose_summary["HP_calls_completed"]
                == pose_lifecycle["HP_calls_started"] == pose_lifecycle["HP_calls_completed"] == 2*len(pose_result["states"])
            and [r["state_sha256"] for r in pose_summary["states"]] == [r["state_sha256"] for r in pose_result["states"]]
            and pose_summary["full_element_and_DOF_coverage"] is True
            and pose_summary["HP_matrix_columns_exhaustively_checked"] is False
            and pose_task["material"]["E_MPa"] == 1. and pose_task["third_medium"]["gamma"] == pose_task["regularization"]["alpha"] == 1e-6,
            "Pose002 actual complete production/fresh-reference prerequisite failed")
        self.check({k:v for k,v in task.items() if k not in descriptive}
            == {k:v for k,v in dict(pose_task,material=dict(pose_task["material"],E_MPa=.5),
                third_medium=dict(gamma=2e-6),regularization=dict(pose_task["regularization"],alpha=2e-6)).items() if k not in descriptive},
            "Only the explicit three parameter values may change from the actual qualified pose task")
        self.bind(self.repo/row["qualified_pose_model_file"],row["qualified_pose_model_sha256"])
        self.check(row["qualified_pose_model_file"] == pose["model_file"] and row["qualified_pose_model_sha256"] == pose["model_sha256"],
            "Qualified pose model role differs")
        pose_model = npz(self.repo/pose["model_file"])
        self.check(set(model) == set(pose_model) and sorted(n for n in model if model[n].dtype != pose_model[n].dtype
                or model[n].shape != pose_model[n].shape or model[n].tobytes() != pose_model[n].tobytes())
            == sorted(MATERIAL_FIELDS) == row["pose_expected_model_changed_fields"]
            == inventory["pose_model_comparison"]["actual_changed_fields"]
            and row["pose_unchanged_model_fields"] == sorted(set(model)-MATERIAL_FIELDS)
            == inventory["pose_model_comparison"]["unchanged_fields"]
            and inventory["pose_model_comparison"]["total_fields"] == 27
            and inventory["pose_model_comparison"]["parameter_case"] == "material_only_after_qualified_pose",
            "Soft model must differ from genuine pose in exactly four material fields")
        same_arrays({n:model[n] for n in set(model)-MATERIAL_FIELDS},
            {n:pose_model[n] for n in set(model)-MATERIAL_FIELDS},"Pose overlay and all non-material arrays")
        for name in ("lam","mu"):
            expected = pose_model[name].copy(); expected[model["solid"]] *= .5
            same_arrays({name:model[name]},{name:expected},"Half-solid stiffness and exact unchanged medium "+name)
        expected_gamma = np.where(model["solid"],1.,2e-6).astype(np.float64)
        same_arrays({"gamma":model["gamma"]},{"gamma":expected_gamma},"Explicit material factors")
        self.check(model["force_scale_per_length"].dtype == np.dtype("float64")
            and model["force_scale_per_length"].shape == () and float(model["force_scale_per_length"]) == 10.
            and float(pose_model["force_scale_per_length"]) == 20., "Et10 scale is not the explicit saved model value")
        pose_metadata = read((self.repo/pose["model_file"]).with_suffix(".json")); verify_descriptor(pose_metadata)
        self.check(pose_metadata["arrays"]["sha256"] == pose["model_sha256"], "Qualified pose model descriptor pin differs")
        expected_material = dict(pose_metadata["material"],E_MPa=.5,third_medium_gamma=2e-6,alpha=2e-6,force_scale_per_length=10.)
        for key in ("lambda_s_MPa","mu_s_MPa","kappa_s_MPa"): expected_material[key] *= .5
        self.check(metadata["material"] == expected_material, "Explicit material metadata or unchanged global kr differs")
        self.qualified_pose = pose
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
            alias="gripper_coarse_square_x71_soft",source_alias="gripper_canonical",case_family="gripper",
            baseline_commit=self.inventory["baseline_commit"],audited_targets_mm=TARGETS,path_kind="ordered_cycle",workpiece=BODY,
            accepted_states=len(self.rows),states=self.rows,result_sha256=sha(self.result_file),
            checks_completed=self.checks,HP_calls_started=self.hp_started,HP_calls_completed=self.hp_completed,
            HP_matrix_columns_exhaustively_checked=False,full_element_and_DOF_coverage=True,
            gates=GATES,global_scatter_precision=3000,global_scatter_inexact_trap=True,
            reference_scope="All actual accepted states/elements/real DOFs; fixed-lift PORT direction, deltaR=0; original signed workpiece and disjoint holding projections",
            qualification="Accepted mechanical states of this explicit x71 softened coarse square cycle; no pressure, clamp, contact, auxiliary energy, stress-HP, rejected-state, all-column, H2/H3 or HF5 qualification",
            **MECHANICAL_AVAILABILITY,analytic_HP_energy_scope="Archived reference only, without candidate comparison or energy qualification",
            contact_qualified=False,clamp_qualified=False,pressure_qualified=False,
            original_run_state_source_sha256=CORE_PINS["audit_native_mean.py"],private_run_state_source_sha256=CORE_PIN,
            inherited_workpiece_checker_sha256=WP_PIN,tangent_action_consumer_sha256=CONSUMER_PIN,
            material_parameters=dict(E_MPa=.5,gamma=2e-6,alpha=2e-6,force_scale_per_length=10.),qualified_pose_prerequisite=self.qualified_pose,
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
    require(np.isfinite(ARGS.time_limit) and ARGS.time_limit > 0.,"Reference window must be explicit and pre-frozen")
    audit = SoftShiftAudit(ARGS)
    try:
        audit.run()
    except BaseException as error:
        audit.lifecycle("not_pass",repr(error))
        write(audit.output/"summary.json",dict(status="not_pass",error=repr(error),states=audit.rows,
            accepted_states=len(audit.rows),HP_calls_started=audit.hp_started,HP_calls_completed=audit.hp_completed,
            checks_completed=audit.checks,elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__": main()
