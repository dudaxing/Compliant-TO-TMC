"""Collect actual closed right-margin records into external documentation proposals."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

BASELINE = "abf62b04d0a384f3c9cfa352dd6232ad1d4ab3d1"
BASE = "lf_data_preparation/native_workpiece_001/"
TESTS = BASE + "right_margin_validation_001"
PREP = BASE + "right_margin_preparation_001"
CASES = {"gamma1e6": BASE+"enlarged_square_projection_001", "right2col": BASE+"right_margin_cycle_001"}
VIEWS = "functional_views/right_margin_20261007/complete_001"
PROGRESS = "docs/evidence/workpiece_enlargement_20261007/right_margin_progress.json"
CONTEXT = "docs/evidence/workpiece_enlargement_20261007/right_margin_source_context"
REPORT = "docs/WORKPIECE_ENLARGEMENT_20261007.md"
ORIGINAL = {"README.md":"1db3ede1a9c1165421a1c3279cefcd7fc659559110399915f2276029a0b19c3b",
    "hf_repo/README.md":"5f559bf1fc3bd9e23dd1f710f2282561bfe627dab6f774b03d53daf5c086ce17",
    "docs/CURRENT_STATUS.md":"6221661d4fdd5c1fb6d45897edc674aa2a6fbff2b8ff9dda8dd8b99c4014999a",
    "docs/RESUME_DEVELOPMENT.md":"52be089970180bc6a8dcd1f1a88fc628dd8a5da668fbd8beae86a19ef009d875",
    REPORT:"01646c89a8256f67a226938516cfebf2436a1bdfbc563d020ed2af61c1064a8a"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True,help="actual Git repository root, read only")
    parser.add_argument("--output",type=Path,required=True,help="new external proposal directory")
    args = parser.parse_args()
    root,output = args.repo.resolve(),args.output.resolve()
    assert not output.exists() and not output.is_relative_to(root), "New external proposal output required"
    bindings = {}

    def raw(name):
        payload = (root/name).read_bytes(); bindings[name] = sha256(payload).hexdigest(); return payload

    def read(name):
        return json.loads(raw(name).decode("utf-8"))

    def closed(control,phase,protocol_name=None):
        protocol_name = protocol_name or phase+"_protocol.json"
        protocol = read(control+"/"+protocol_name)
        launch = read(control+"/"+phase+"_launch.json")
        assert launch["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
        assert launch["stop_reason"] is None and launch["all_bindings_unchanged"]
        assert launch["protocol_sha256"] == bindings[control+"/"+protocol_name]
        assert launch["bindings"] == protocol["bindings"]
        limits = protocol["phases"][phase]
        assert launch["elapsed_seconds"] <= limits["outer_seconds"] and launch["peak_sampled_tree_RSS_bytes"] <= protocol["sampled_RSS_bytes"]
        return launch

    closed(TESTS,"tests","adapter_test_protocol.json")
    tests = read(TESTS+"/run_001/test_receipt.json")
    assert tests["status"] == "pass" and tests["pytest_exit_code"] == 0 and tests["tests_collected"] == tests["tests_passed"] == 5
    assert tests["constructor_invocations"] == 2 and tests["all_bindings_unchanged"]
    assert all(tests[k] == 0 for k in ("new_force_calls","new_tangent_calls","new_equilibrium_calls","new_HP_calls"))
    prep_launch = closed(PREP,"prepare","preparation_protocol.json")
    prep = read(PREP+"/run_001/preparation_receipt.json")
    comparison = read(PREP+"/run_001/model_comparison.json")
    prepared_inventory = read(PREP+"/run_001/input_inventory.json")
    assert prep["status"] == "pass" and prep["final_resource_check_passed"] and prep["inputs_and_sources_unchanged"]
    assert comparison == prep["model_comparison"] == prepared_inventory["model_comparison"]
    assert comparison["total_fields"] == 27 and len(comparison["raw_equal_fields"]) == 10 and len(comparison["physically_mapped_fields"]) == 17
    assert comparison["parent_physical_subdomain_byte_exact"]
    assert all(prep[k] == 0 for k in ("force_calls","tangent_calls","solver_calls","HP_calls","JIT_calls","LF_imports"))
    source_view = read("functional_views/right_margin_20261007/geometry_001/view/receipt.json")
    assert source_view["status"] == "pass" and source_view["all_bindings_unchanged"]
    assert all(source_view[k] == 0 for k in ("new_F","new_T","new_solver","new_HP","new_model_constructions"))
    cases = {}
    for label,control in CASES.items():
        production = closed(control,"production")
        execution = read(control+"/run_001/execution_receipt.json")
        result_name = control+"/run_001/result/result.json"
        result = read(result_name)
        assert result["status"] == "success" and execution["status"] == "pass"
        assert execution["result_sha256"] == bindings[result_name]
        assert all(result[k] for k in ("path_completed","loading_peak_reached","unload_endpoint_reached","task_target_executed"))
        assert result["accepted_states"] == len(result["states"]) == execution["accepted_states"]
        ref_launch = closed(control,"reference")
        reference = read(control+"/reference/summary.json")
        assert reference["status"] == "pass" and reference["result_sha256"] == bindings[result_name]
        assert reference["accepted_states"] == len(reference["states"]) == result["accepted_states"]
        assert reference["HP_calls_started"] == reference["HP_calls_completed"] == 2*result["accepted_states"]
        model_name = control+"/run_001/result/"+result["model"]["descriptor_path"]
        model = read(model_name)
        assert bindings[model_name] == result["model"]["descriptor_file_sha256"]
        assert model["task_sha256"] == result["task_sha256"]
        cases[label] = dict(result_sha256=bindings[result_name],model_sha256=model["arrays"]["sha256"],task_sha256=model["task_sha256"],
            task=model["task"],counts=model["region_metadata"]["counts"],accepted_states=result["accepted_states"],
            call_counts=result["call_counts"],production_elapsed_seconds=production["elapsed_seconds"],reference_elapsed_seconds=ref_launch["elapsed_seconds"],
            HP_started=reference["HP_calls_started"],HP_completed=reference["HP_calls_completed"],checks_completed=reference["checks_completed"])
    old,new = cases["gamma1e6"]["task"],cases["right2col"]["task"]
    assert old["third_medium"] == new["third_medium"] == {"gamma":1e-6}
    assert all(new[k]==v for k,v in old.items() if k not in {"geometry","background_symmetry","task_id","purpose","parameter_origin","description"})
    assert new["background_symmetry"] == {**old["background_symmetry"],"points_mm":[[0.,40.],[82.,40.]]}
    view_launch = closed(VIEWS,"view","protocol.json")
    phase = read(VIEWS+"/view/phase_view.json")
    view = read(VIEWS+"/view/view.json")
    assert phase["status"] == view["status"] == "pass" and phase["final_resource_check_passed"]
    assert phase["original_view_sha256"] == bindings[VIEWS+"/view/view.json"]
    assert phase["new_geometry_nodal_F_T_model_solver_HP_calls_outside_raw_viewer"] == view["new_F_T_model_solver_HP_calls"] == 0
    assert phase["elapsed_seconds"] <= 180 and phase["sampled_peak_helper_RSS_bytes"] <= 8*1024**3
    expected = sum(c["accepted_states"] for c in cases.values())
    assert all(view[k]==expected for k in ("geometry_started","geometry_completed","nodal_started","nodal_completed"))
    assert set(c["label"] for c in view["cases"]) == set(CASES)
    for label,control in CASES.items():
        result_name = control+"/run_001/result/result.json"
        assert view["input_source_bindings"][result_name] == cases[label]["result_sha256"]
        assert view["input_source_bindings"][control+"/reference/summary.json"] == bindings[control+"/reference/summary.json"]
    view_cases = {c["label"]:c for c in view["cases"]}
    for label,case in cases.items():
        c = view_cases[label]
        assert c["task"] == case["task"] and c["model_sha256"] == case["model_sha256"]
        assert c["reference_available"] and c["production_path_completed"] and c["unload_endpoint_reached"]
        assert c["saved_accepted_states"] == c["observed_states"] == case["accepted_states"]
        summary_name = label+"/summary.json"
        rows = read(VIEWS+"/view/"+summary_name)["rows"]
        assert bindings[VIEWS+"/view/"+summary_name] == view["outputs"][summary_name] == phase["outputs"][summary_name]
        assert len(rows) == case["accepted_states"]
        case.update(tip_node=c["tip_node"],loading_peak=rows[c["peak_index"]],return_state=rows[c["last_index"]])
        assert case["loading_peak"]["leg"] == "loading" and case["loading_peak"]["d_mm"] == 1.2
        original_loading = [row for row in rows if row["leg"] == "loading" and row["d_mm"] == case["task"]["path"]["targets_mm"][row["original_target_index"]]]
        case["original_loading_rows"] = original_loading
    figures = ["comparison.png","distances_forces.png","peak_fields.png","gamma1e6/actual_states.gif","right2col/actual_states.gif"]
    for name in figures:
        assert sha256(raw(VIEWS+"/view/"+name)).hexdigest() == view["outputs"][name]
    summary = dict(schema_version="right-margin-final-documentation-proposal-1.0",status="complete_mechanical_reference_views_project_incomplete",
        qualification="Actual complete new production and allN fresh2N mechanical reference; no pressure/contact-definition/free-body or HF5 qualification",
        source_stage=dict(tests_passed=5,tests_constructors=2,prep_actual_counts=prep["actual_counts"],mapped_fields=17,raw_equal_fields=10,
            prep_helper_seconds=prep["elapsed_seconds"],prep_outer_seconds=prep_launch["elapsed_seconds"],prepared_layout_passed=True),
        cases=cases,view=dict(observations_each=expected,helper_seconds=phase["elapsed_seconds"],outer_seconds=view_launch["elapsed_seconds"],new_F_T_model_solver_HP_calls=0),
        next="Use observed2mm-margin evidence to choose matched mesh and domain-margin sensitivity; then define pressure/contact criteria, circles/free bodies and HF5 coupling",
        input_json_and_figure_sha256=bindings)
    originals = {name:raw(CONTEXT+"/"+name) for name in ORIGINAL}
    assert all(sha256(originals[n]).hexdigest()==pin for n,pin in ORIGINAL.items())
    report_current = raw(REPORT)
    assert report_current.startswith(originals[REPORT]), "Keep entire abf report and source-phase append"
    new_peak = cases["right2col"]["loading_peak"]
    metric_fields = ["d_mm","R_input_N","q_out_mm","total_body_Fy_N","material_body_Fy_N","regularization_body_Fy_N","cached_two_sided_normal_magnitude_sum_N","tip_to_bottom_mm","medium_min_J","medium_max_abs_Hu_per_mm"]
    table = "| case | " + " | ".join(metric_fields) + " |\n|---|" + "---|"*len(metric_fields) + "\n"
    for label in cases:
        table += "| " + label + " | " + " | ".join(format(cases[label]["loading_peak"][k],".9g") for k in metric_fields) + " |\n"
    common_table = "| loading d [mm] | baseline R [N] | right2col R [N] | baseline Fy [N] | right2col Fy [N] |\n|---|---|---|---|---|\n"
    for d in (.5,.75,.8,.85,1.):
        matched = [[r for r in c["original_loading_rows"] if r["d_mm"]==d] for c in cases.values()]
        assert all(len(rows)==1 for rows in matched)
        common_table += f"| {d:g} | {matched[0][0]['R_input_N']:.9g} | {matched[1][0]['R_input_N']:.9g} | {matched[0][0]['total_body_Fy_N']:.9g} | {matched[1][0]['total_body_Fy_N']:.9g} |\n"
    append = f"\n\n## 右介质余量2 mm：完整路径、独立参考与实际效果（2026-10-07）\n\nHF本项目仅提供独立有限变形/TMC正向评估，不含优化器；复用LF/N4研究成果，供外部LF/N4研究层比较、优选并推进HF5评价接口。此前紧贴x80域边界可能影响钳尖附近的第三介质；本次保留全部原40×80物理单元、标签、h1/E1/gamma1e-6/alpha1e-6/Lr80与工件，新增右侧2列介质到x82，并一致延长task背景顶边。新增analysis_domain API/CLI只写派生几何，task绑定、DOF及PORT direction由准备阶段重建。\n\n小测试5/5、2小模型构造；实际准备27字段10raw相同/17按物理映射保持，3280单元/3403节点/6806DOF、450固定/6356自由，body162/190/380。来源测试、准备和未变形图阶段均无F/T/平衡/HP；这些阶段没有赋予力学资格。之后新生产实际接受{cases['right2col']['accepted_states']}态完成0→1.2→0，{cases['right2col']['HP_completed']}次全新HP80/120与{cases['right2col']['checks_completed']}检查通过。保存态视图{expected}次几何/{expected}次节点力观察通过，无新F/T/构造/求解/HP。二分态若存在完整保留；下表共同点只选原加载目标。\n\n{table}\n{common_table}\nR是半模型输入端反力；lower-body Fy、材料/Hu分量与2|Fy|两侧法向幅值和分别解释，2|Fy|不是完整装配净力。q_out仍为加权竖向端口位移；有限钳尖距离另列。每个case的tip由保存参考坐标(80,30)唯一选择。比较同工件同加载目标下的域余量作用，不使用gamma减半数据代替新结果，也不把某一峰值变化概括成全路径不敏感或域/网格收敛。保存Green应变为binary64观察，完整力、PORT方向切线作用、离散平衡/固定工件力的参考资格不扩展到连续压力、物理接触判据、摩擦或自由体稳定夹持。\n\n[未变形域/工件/端口](../functional_views/right_margin_20261007/geometry_001/view/prepared_domain.png)；[完整结构/力曲线](../{VIEWS}/view/comparison.png)；[距离/力](../{VIEWS}/view/distances_forces.png)；[峰值场](../{VIEWS}/view/peak_fields.png)；[新实际动画](../{VIEWS}/view/right2col/actual_states.gif)。此前source-phase段是当时来源准备快照，本节为其后实际终态。\n\n下一项须依据上述实际域余量效果选择匹配网格与域余量敏感性，再明确压力/接触定义、圆体/自由工件和HF5。默认tangent初猜与机械核心保持；探索任务显式用已有port_projection。本次仍没有完成整个HF项目。\n"
    output.mkdir()
    proposals = output/"proposals"; proposals.mkdir()
    historical = {}
    for name in ORIGINAL:
        if name == REPORT: continue
        current = raw(name); assert current.endswith(originals[name]), "Historical abf front suffix must remain exact"
        banner = current[:-len(originals[name])]
        history_path = output/"interim_banners"/(name+".prefix.md"); history_path.parent.mkdir(parents=True,exist_ok=True); history_path.write_bytes(banner)
        prefix_path = "../" if name.startswith("hf_repo/") else "../" if name.startswith("docs/") else ""
        report_link = "WORKPIECE_ENLARGEMENT_20261007.md" if name.startswith("docs/") else prefix_path+REPORT
        progress_link = "evidence/workpiece_enlargement_20261007/right_margin_progress.json" if name.startswith("docs/") else prefix_path+PROGRESS
        prefix = f"<!-- current-front right-margin actualcomplete; predecessor {BASELINE} -->\n\n## 当前：右侧2 mm介质域完整对照已完成（2026-10-07）\n\nHF本项目仅提供独立有限变形/TMC正向评估，不含优化器；复用LF/N4成果，供外部LF/N4研究层比较、优选并推进HF5评价接口；开发统一main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，HF5尚未实现。固定side18中心(71,40)、右面80，分析域80→82；原物理坐标、h1/E1/gamma1e-6/alpha1e-6/Lr80/端口/支撑保持，只新增右介质列和相应顶边。\n\n新analysis_domain API write_right_medium_geometry(parent_path,output_dir,right_columns:int)->Path，与prepare_analysis_domain.py CLI只生成新HF几何；原LF数据/provenance保留，全域不冒称LF native。任务geometry身份、DOF和PORT direction另行重建，tip按坐标(80,30)选择。5测试和准备27字段映射已通过；新完整{cases['right2col']['accepted_states']}态、{cases['right2col']['HP_completed']}新HP80/120、{cases['right2col']['checks_completed']}检查及实际视图通过。\n\n新加载峰值d={new_peak['d_mm']:g} mm：半模型R={new_peak['R_input_N']:.9g} N，下半体Fy={new_peak['total_body_Fy_N']:.9g} N，2|Fy|幅值和={new_peak['cached_two_sided_normal_magnitude_sum_N']:.9g} N，钳尖底面距={new_peak['tip_to_bottom_mm']:.9g} mm。2|Fy|不是完整装配净力；q_out为原加权端口位移。压力/接触判据、网格及域收敛、圆体/自由工件/摩擦仍待验证或实现。默认tangent不切换，探索仍显式port_projection。\n\n[完整记录]({report_link})；[实际进度]({progress_link})；[结构/力]({prefix_path}{VIEWS}/view/comparison.png)；[距离/力]({prefix_path}{VIEWS}/view/distances_forces.png)；[新实际动画]({prefix_path}{VIEWS}/view/right2col/actual_states.gif)。\n\n从任意目录恢复main后按实际仓库根定位文件；几何CLI示意：python <仓库根>/hf_repo/scripts/prepare_analysis_domain.py --geometry <父geometry.json> --output <全新目录> --right-columns 2（不创建task或求解）。下一步根据本轮实际效果选择匹配网格和域余量敏感性，再推进压力/接触定义及HF5；未执行后续科学卡，旧资格不能转给新模型。\n\n---\n\n下面完整原文是abf62b04阶段历史，原字节保留；当前进度以上方和最新报告为准，旧已关闭卡不重跑。\n\n"
        target = proposals/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(prefix.encode("utf-8")+originals[name])
        historical[name] = dict(sha256=ORIGINAL[name],bytes=len(originals[name]),new_suffix_offset_bytes=len(prefix.encode("utf-8")),interim_banner_sha256=sha256(banner).hexdigest())
    target = proposals/REPORT; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(report_current+append.encode("utf-8"))
    progress = read(PROGRESS)
    progress["status"] = summary["status"]
    progress["prior_production_snapshot"] = progress["production"]
    progress["production"] = {**progress["production"],"status":"pass","accepted_states":cases["right2col"]["accepted_states"],"actual_call_counts":cases["right2col"]["call_counts"],"result_sha256":cases["right2col"]["result_sha256"]}
    progress["final_reference_view_observations"] = summary
    progress["qualification"] = summary["qualification"]; progress["next"] = summary["next"]
    p = proposals/PROGRESS; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(progress,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    summary["historical_suffixes"] = historical
    summary["main_report_before_append_sha256"] = sha256(report_current).hexdigest()
    summary["proposal_sha256"] = {p.relative_to(proposals).as_posix():sha256(p.read_bytes()).hexdigest() for p in proposals.rglob("*") if p.is_file()}
    (output/"final_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(dict(status="external_proposals_only",output=str(output),new_accepted_states=cases["right2col"]["accepted_states"],new_HP_calls=cases["right2col"]["HP_completed"],proposed_files=list(summary["proposal_sha256"])),ensure_ascii=False))


if __name__ == "__main__":
    main()
