"""Read final saved JSON, file SHA and image metadata; no numerical/HF imports."""
from hashlib import sha256
import json
from pathlib import Path
from PIL import Image

ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
AUTHOR = Path("D:/hf-workpiece-enlarge-author-20261007")
OUT = AUTHOR/"final_runtime_evidence_review.json"
VIEW = ROOT/"functional_views/workpiece_gamma_20261007/complete_001"
OLD = ROOT/"lf_data_preparation/native_workpiece_001/enlarged_square_projection_001"
NEW = ROOT/"lf_data_preparation/native_workpiece_001/gamma_half_cycle_001"
digest = lambda p:sha256(p.read_bytes()).hexdigest()
pins = {}

def bind(path, expected=None):
    path = path.resolve()
    name = path.relative_to(ROOT).as_posix()
    if name not in pins:pins[name] = digest(path)
    assert expected is None or pins[name] == expected, name
    return pins[name]

def read(path):
    bind(path)
    return json.loads(path.read_text(encoding="utf-8"))

def binding_map(mapping, base=ROOT):
    for name, pin in mapping.items():bind(base/name,pin)
    return len(mapping)

def launch_check(control, protocol_name, launch_name, phase):
    protocol = read(control/protocol_name);launch = read(control/launch_name)
    assert launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
    assert launch["all_bindings_unchanged"] is True and launch["stop_reason"] is None
    assert launch["protocol_sha256"] == bind(control/protocol_name) and launch["bindings"] == protocol["bindings"]
    assert launch["outer_seconds"] == protocol["phases"][phase]["outer_seconds"]
    assert 0 <= launch["elapsed_seconds"] <= launch["outer_seconds"]
    assert launch["sampled_RSS_limit_bytes"] == protocol["sampled_RSS_bytes"] == 8*1024**3
    assert 0 <= launch["peak_sampled_tree_RSS_bytes"] <= launch["sampled_RSS_limit_bytes"]
    assert not (control/"stop_requested.txt").exists()
    binding_map(protocol["bindings"])
    return protocol,launch

def gate_flags(value):
    if isinstance(value,dict):
        if "pass_gate" in value:assert value["pass_gate"] is True
        for child in value.values():gate_flags(child)
    elif isinstance(value,list):
        for child in value:gate_flags(child)

cases = {}
for label,control in (("gamma1e6",OLD),("gamma5em7",NEW)):
    stage = control/"run_001";result = read(stage/"result/result.json")
    receipt = read(stage/"execution_receipt.json");freeze = read(stage/"source_freeze.json")
    inventory = read(stage/"input_inventory.json")
    production_protocol,production_launch = launch_check(control,"production_protocol.json","production_launch.json","production")
    reference_protocol,reference_launch = launch_check(control,"reference_protocol.json","reference_launch.json","reference")
    summary = read(control/"reference/summary.json");lifecycle = read(control/"reference/lifecycle.json")
    contract = read(control/"reference_contract.json")
    assert receipt["status"] == "pass" and result["status"] == "success" and result["path_completed"] is True
    assert result["unload_endpoint_reached"] is result["loading_peak_reached"] is True
    assert result["accepted_states"] == receipt["accepted_states"] == summary["accepted_states"] == lifecycle["accepted_states_completed"] == 24
    assert receipt["result_sha256"] == summary["result_sha256"] == bind(stage/"result/result.json")
    assert receipt["sources"] == freeze["sources"] and receipt["call_counts"] == result["call_counts"] == summary["counter_accounting"]["counts"]
    assert receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
    assert receipt["force_hook_restored"] is receipt["tangent_hook_restored"] is True
    assert summary["status"] == lifecycle["status"] == "pass" and lifecycle["error"] is None
    assert summary["HP_calls_started"] == summary["HP_calls_completed"] == lifecycle["HP_calls_started"] == lifecycle["HP_calls_completed"] == 48
    assert summary["checks_completed"] == lifecycle["checks_completed"]
    assert summary["full_element_and_DOF_coverage"] is True and summary["HP_matrix_columns_exhaustively_checked"] is False
    assert all(summary[k] is False for k in ("contact_qualified","clamp_qualified","pressure_qualified"))
    assert all(summary[k] == 0 for k in ("candidate_force_calls","tangent_calls","solver_calls","model_constructions"))
    assert summary["response_mode"] == "mechanical"
    if label == "gamma5em7":assert summary["gamma"] == 5e-7
    assert summary["independent_reference_contract_sha256"] == bind(control/"reference_contract.json")
    assert summary["independent_reference_source_bindings"] == contract["reference_sources"]
    assert contract["actual_accepted_states"] == 24 and contract["expected_new_HP80_120_calls"] == 48
    binding_map(summary["input_bindings"]);binding_map(summary["source_bindings"]);binding_map(contract["reference_sources"])
    assert [r["d"] for r in result["states"]] == summary["audited_targets_mm"] == result["targets_mm"]
    archives = []
    for index,(saved,ref) in enumerate(zip(result["states"],summary["states"])):
        assert ref["index"] == index and ref["status"] == "pass" and ref["HP_calls"] == 2
        assert (ref["state_sha256"],ref["target_mm"],ref["leg"],ref["original_target_index"]) == (saved["state_sha256"],saved["d"],saved["leg"],saved["original_target_index"])
        assert ref["elements_compared"] == 3200 and ref["global_DOFs_compared"] == 6642
        assert len(ref["references"]) == 2
        assert [Path(r["path"]).name for r in ref["references"]] == ["hp80_full_local.json.gz","hp120_full_local.json.gz"]
        gate_flags(ref)
        for record in ref["references"]:
            path = control/"reference"/record["path"]
            bind(path,record["sha256"]);assert path.stat().st_size>0;archives.append(record)
    assert len(archives) == 48 and len({r["path"] for r in archives}) == 48
    core = {name:pin for name,pin in freeze["sources"].items() if name.startswith("hf_repo/src/hf_eval/")}
    assert len(core) == 24
    binding_map(core)
    for name,pin in core.items():bind(stage/"sources"/Path(name).name,pin)
    cases[label] = dict(control=control,result=result,receipt=receipt,inventory=inventory,core=core,summary=summary,
        production_launch=production_launch,reference_launch=reference_launch,lifecycle=lifecycle,
        production_binding_count=len(production_protocol["bindings"]),reference_binding_count=len(reference_protocol["bindings"]),
        HP_archive_count=48)

assert cases["gamma5em7"]["summary"]["checks_completed"] == 465255
assert cases["gamma1e6"]["summary"]["checks_completed"] == 465220
assert cases["gamma1e6"]["core"] == cases["gamma5em7"]["core"]

previous_file = AUTHOR/"final_physical_data_review.json"
previous_pin = digest(previous_file)
assert previous_pin == "f1b32c5afcde453988866ff94dd33f833f557934b76ae659017283e6b7f965f6"
previous = json.loads(previous_file.read_text(encoding="utf-8"))
assert previous["independent_gamma_half_reference_status"] == "running_per_root_message_not_read_or_qualified_by_this_review"
for label,old_label in (("gamma1e6","gamma_baseline"),("gamma5em7","gamma_half")):
    model = cases[label]["control"]/"run_001/result/model/model.npz"
    assert bind(model) == previous["input_bindings"][model.relative_to(ROOT).as_posix()]
    assert cases[label]["receipt"]["model_sha256"] == bind(model)
assert previous["model_comparison"]["changed_fields"] == ["gamma","lam","mu"]
assert len(previous["model_comparison"]["unchanged_fields"]) == 24
assert all(value.get("byte_exact",False) or (value.get("solid_values_byte_exact",False) and value.get("medium_values_exact_half",False)) for value in previous["model_comparison"]["field_proof"].values())

view_protocol,view_launch = launch_check(VIEW,"protocol.json","view_launch.json","view")
view = read(VIEW/"view/view.json");phase = read(VIEW/"view/phase_view.json")
comparison = read(VIEW/"view/gamma_comparison/cached_comparison.json")
assert view["status"] == phase["status"] == comparison["status"] == "pass"
assert view["failure"] is phase["failure"] is None
assert view["geometry_started"] == view["geometry_completed"] == view["nodal_started"] == view["nodal_completed"] == 48
assert view["new_F_T_model_solver_HP_calls"] == phase["cached_geometry_nodal_F_T_model_solver_HP_calls"] == comparison["new_geometry_nodal_F_T_model_solver_HP_calls"] == 0
assert view["contact_pressure_clamping_qualified"] is False
assert phase["original_view_sha256"] == bind(VIEW/"view/view.json")
assert phase["cached_comparison"] == comparison and phase["final_resource_check_passed"] is True and phase["final_resource_error"] is None
assert comparison["matched_states"] == 24 and comparison["saved_states"] == {"gamma1e6":24,"gamma5em7":24}
assert all(not value for value in comparison["unmatched_original_target_indices"].values())
assert all(not value for value in comparison["extra_bisection_indices"].values())
binding_map(view["input_source_bindings"])
binding_map(comparison["source_bindings"],VIEW/"view")
binding_map(view["outputs"],VIEW/"view");binding_map(phase["outputs"],VIEW/"view")
assert len(view["cases"]) == 2
views = {};image_meta = {}
for label,case in cases.items():
    saved_summary = read(VIEW/"view"/label/"summary.json")
    assert saved_summary["accepted_states"] == 24 and saved_summary["production_status"] == "success" and saved_summary["reference_available"] is True
    descriptor = next(r for r in view["cases"] if r["label"] == label)
    assert descriptor["saved_accepted_states"] == descriptor["observed_states"] == 24
    assert descriptor["peak_index"] == 13 and descriptor["last_index"] == 23 and descriptor["reference_available"] is True
    assert descriptor["model_sha256"] == case["receipt"]["model_sha256"]
    frames = [];stored_scope_differences = []
    for index,(row,state) in enumerate(zip(saved_summary["rows"],case["result"]["states"])):
        derived = read(VIEW/"view"/label/f"{index:03}"/"derived.json")
        assert derived["row"] == row
        assert (row["index"],row["state_sha256"],row["leg"],row["original_target_index"],row["d_mm"]) == (index,state["state_sha256"],state["leg"],state["original_target_index"],state["d"])
        assert row["R_input_N"] == state["R_input"] and row["q_out_mm"] == state["q_out"]
        assert row["total_body_Fy_N"] == state["workpiece"]["force_on_lower_body_N"]["total"][1]
        assert row["medium_min_J"] >= state["minimum_J"] and row["medium_max_abs_Hu_per_mm"] <= state["max_abs_Hu_per_mm"]
        if row["medium_min_J"] != state["minimum_J"] or row["medium_max_abs_Hu_per_mm"] != state["max_abs_Hu_per_mm"]:
            stored_scope_differences.append(dict(index=index,d_mm=row["d_mm"],global_minimum_J=state["minimum_J"],medium_minimum_J=row["medium_min_J"],global_max_abs_Hu_per_mm=state["max_abs_Hu_per_mm"],medium_max_abs_Hu_per_mm=row["medium_max_abs_Hu_per_mm"]))
        frames.append(dict(index=index,original_target_index=row["original_target_index"],leg=row["leg"],d_mm=row["d_mm"],state_sha256=row["state_sha256"],derived_file=(VIEW/"view"/label/f"{index:03}"/"derived.json").relative_to(ROOT).as_posix()))
    gif = VIEW/"view"/label/"actual_states.gif"
    bind(gif,view["outputs"][label+"/actual_states.gif"])
    with Image.open(gif) as image:
        assert image.format == "GIF" and image.n_frames == 24
        meta = dict(format=image.format,size=list(image.size),frames=image.n_frames,duration_ms=image.info.get("duration"),loop=image.info.get("loop"))
    image_meta[gif.relative_to(ROOT).as_posix()] = dict(sha256=bind(gif),**meta)
    views[label] = dict(peak=saved_summary["rows"][13],origin=saved_summary["rows"][0],unload_endpoint=saved_summary["rows"][-1],frame_source_order=frames,stored_phase_vs_global_stat_differences=stored_scope_differences)

for name,pin in phase["outputs"].items():
    if name.endswith(".png"):
        path = VIEW/"view"/name
        with Image.open(path) as image:
            assert image.format == "PNG" and image.width>0 and image.height>0
            image_meta[path.relative_to(ROOT).as_posix()] = dict(sha256=bind(path,pin),format=image.format,size=list(image.size),mode=image.mode)

viewer_source = VIEW/"saved_shift_views.py"
source = viewer_source.read_text(encoding="utf-8")
assert 'for index,r in enumerate(result["states"])' in source and 'for index,x in enumerate(case["cache"])' in source
assert 'append_images=frames[1:]' in source and 'if gif.n_frames!=len(case["cache"])' in source
bind(viewer_source)
old_peak,new_peak = views["gamma1e6"]["peak"],views["gamma5em7"]["peak"]
assert old_peak["d_mm"] == new_peak["d_mm"] == 1.2
assert old_peak["medium_min_J"] == cases["gamma1e6"]["result"]["states"][13]["minimum_J"]
assert new_peak["medium_min_J"] == cases["gamma5em7"]["result"]["states"][13]["minimum_J"]

report = dict(schema_version="gamma-half-final-runtime-evidence-review-1.0",status="pass_saved_evidence_only",
    reviewer_source=dict(file=Path(__file__).as_posix(),sha256=digest(Path(__file__))),
    scope="Final production/reference/view saved evidence and SHA/PNG/GIF metadata only. No new FE, HP, geometry, nodal, strain, rendering, plotting or numerical qualification execution. Documents and Git changes were not reviewed.",
    prior_review_retained=dict(file=previous_file.as_posix(),sha256=previous_pin,original_scope=previous["scope"],not_overwritten=True),
    reviewer_selfcheck=dict(first_attempt_status="Stopped before report creation on an overly strong medium-only/global equality assertion",
        first_source_file=(AUTHOR/"review_final_runtime_evidence_first_scope_assert.py").as_posix(),first_source_sha256=digest(AUTHOR/"review_final_runtime_evidence_first_scope_assert.py"),
        finding="Only the two unloaded endpoint Hu maxima differ: global includes the solid phase, medium-only does not. MinJ equality still holds for these stored states; correct scope relation is globalMinJ<=mediumMinJ and globalMaxHu>=mediumMaxHu.",
        scientific_evidence_modified=False,new_scientific_calls=0,formal_phase_status_basis="Actual existing receipts/launches; this reviewer's failed assumption is not a production/reference/view failure"),
    all_input_source_output_bindings=pins,
    production={label:dict(status="pass",accepted_states=24,targets=case["result"]["targets_mm"],counts=case["result"]["call_counts"],
        binding_count=case["production_binding_count"],all_bindings_current_SHA_match=True,helper_elapsed_seconds=case["receipt"]["elapsed_seconds"],outer_elapsed_seconds=case["production_launch"]["elapsed_seconds"]) for label,case in cases.items()},
    reference={label:dict(status="pass",actual_accepted_states=24,HP_calls_started=48,HP_calls_completed=48,HP_archive_count=case["HP_archive_count"],checks_completed=case["summary"]["checks_completed"],
        every_state_matches_current_production=True,mechanical_only=True,contact_pressure_clamp_qualified=False,
        lifecycle_elapsed_seconds=case["lifecycle"]["elapsed_seconds"],outer_elapsed_seconds=case["reference_launch"]["elapsed_seconds"],
        source_identity=case["summary"]["independent_reference_source_bindings"],binding_count=case["reference_binding_count"],all_bindings_current_SHA_match=True) for label,case in cases.items()},
    core24=dict(byte_identical_to_baseline=True,SHA256=cases["gamma1e6"]["core"]),
    model_identity=dict(physical_changed_fields=["gamma","lam","mu"],medium_coefficients_exact_half=True,solid_coefficients_byte_exact=True,other24_fields_byte_exact=True,
        verification_origin="Previous saved-only NPZ byte/half proof reused because both entire model NPZ SHAs remain exact. No new NPZ load or array observation in this review.",prior_field_proof=previous["model_comparison"]),
    view=dict(status="pass",geometry_observations_original=48,nodal_observations_original=48,new_mechanics_calls_original_view=0,new_observations_this_review=0,
        matching="24 actual states with exact leg/index/task target; no nearest-state substitution or interpolation",binding_count=len(view_protocol["bindings"]),all_bindings_current_SHA_match=True,
        helper_elapsed_seconds=phase["elapsed_seconds"],outer_elapsed_seconds=view_launch["elapsed_seconds"],image_metadata=image_meta,
        GIF_provenance="Pinned saved viewer loops through every saved accepted index and caches in that order; 24 derived rows match production state hashes and each GIF has24 frames. Pixel values do not embed state hashes; provenance comes from source/order/saved-output bindings.",
        common_nodal_force_scale=view["common_nodal_force_scale"],common_peak_field_ranges=view["common_peak_field_ranges"],cases=views),
    actual_peak_comparison=dict(input_mm=1.2,baseline=old_peak,gamma_half=new_peak,
        medium_min_J_ratio=new_peak["medium_min_J"]/old_peak["medium_min_J"],
        bottom_tip_gap_ratio=new_peak["tip_to_bottom_mm"]/old_peak["tip_to_bottom_mm"],
        bottom_tip_gap_difference_um=1000*(new_peak["tip_to_bottom_mm"]-old_peak["tip_to_bottom_mm"]),
        body_Fy_difference_percent=100*(new_peak["total_body_Fy_N"]-old_peak["total_body_Fy_N"])/old_peak["total_body_Fy_N"],
        interpretation="At this fixed boundary task, medium minJ roughly halves while the finite tip-to-bottom gap changes only about3% and peakFy about0.33%. Different observables are not assumed proportional; this is not pressure/contact, gamma convergence or boundary-independence proof."),
    baseline_preservation="Baseline result/model/core/source/reference remain exact under current frozen bindings; new task has its own fresh24-state48HP result. Previous incomplete-reference review retained as historical state.",
    activity=dict(candidate_module_imports=0,FE=0,force=0,tangent=0,solver=0,HP=0,geometry=0,nodal=0,strain=0,plot=0,render=0,NPZ_array_reads=0,formal_repository_writes=0,Git_mutations=0))
assert digest(previous_file) == previous_pin
with OUT.open("x",encoding="utf-8") as handle:json.dump(report,handle,indent=2,allow_nan=False);handle.write("\n")
print(json.dumps(dict(status=report["status"],report_sha256=digest(OUT),bound_files=len(pins),new_reference=report["reference"]["gamma5em7"],
    gap_ratio=report["actual_peak_comparison"]["bottom_tip_gap_ratio"],gap_difference_um=report["actual_peak_comparison"]["bottom_tip_gap_difference_um"],
    minJ_ratio=report["actual_peak_comparison"]["medium_min_J_ratio"],Fy_difference_percent=report["actual_peak_comparison"]["body_Fy_difference_percent"],
    GIFs={k:v for k,v in image_meta.items() if v["format"]=="GIF"})))
