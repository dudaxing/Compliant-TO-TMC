"""Ordinary saved-record and source audit; never import scientific modules."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

ROOT = Path(r"D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
EXT = Path(__file__).parent
STAGE = "lf_data_preparation/native_interface_001/regularization_sensitivity_001"
HEAD = "9e2e37cce7f0441af042337d1c26c50ae660acc0"
names = {
    "result": STAGE + "/run_001/alpha_half/result.json",
    "response": STAGE + "/run_001/alpha_half/response.json",
    "receipt": STAGE + "/run_001/execution_receipt.json",
    "outer": STAGE + "/production_launch.json",
    "progress": STAGE + "/run_001/accepted_progress.jsonl",
    "peak_state": STAGE + "/run_001/alpha_half/accepted/013/state.json",
    "controller": "hf_repo/src/hf_eval/split_displacement.py",
    "native_mean": "hf_repo/src/hf_eval/native_mean.py",
    "native_evaluate": "hf_repo/src/hf_eval/native_evaluate.py",
    "native_batch": "hf_repo/src/hf_eval/native_batch.py",
    "CLI": "hf_repo/scripts/evaluate_native.py",
    "kernel_timing": "hf_repo/src/hf_eval/split_kernel_invariants_hu.py",
    "worker": STAGE + "/execute_alpha_cycle.py",
}

def read(name):
    return json.loads((ROOT / names[name]).read_text(encoding="utf-8"))

def pin(name):
    path = ROOT / names[name]
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": sha256(raw).hexdigest(), "bytes": len(raw)}

r, response, receipt, outer, peak = (read(k) for k in ("result", "response", "receipt", "outer", "peak_state"))
d = r["path_diagnostics"]
def after_last_peak(rows, key):
    boundary = [i for i, row in enumerate(rows) if row[key] == 1.2][-1]
    return rows[boundary + 1:]

base_checks = after_last_peak(d["newton_history"], "d")
trials = after_last_peak(d["trials"], "target_displacement")
linear = after_last_peak(d["linear_solve_diagnostics"], "target_displacement")
progress = [json.loads(line) for line in (ROOT / names["progress"]).read_text(encoding="utf-8").splitlines() if line.strip()]
# These checks concern identity, sequence and record inventory; not new numerical gates.
assert all(row["d"] == 1.15 for row in base_checks)
assert all(row["target_displacement"] == 1.15 for row in trials + linear)
assert r["accepted_states"] == len(r["states"]) == len(progress) == 14
assert r["states"][-1]["state_sha256"] == peak["state_sha256"] == progress[-1]["state_sha256"]
sources = {name: pin(name) for name in names}
evidence = [
    {"source": "controller", "lines": [55, 109], "meaning": "Lower-level warm state contract: explicit origin/multiplier, bitwise lift match, fixed zero; nonnegative stages starting0, load/cycle ordering. Not a public saved-state continuation API."},
    {"source": "controller", "lines": [113, 145], "meaning": "Controller timer starts at113; evaluate clock before and after assembly, all-attempt wall time in finally, field timing only returned assembly, positiveJ checks."},
    {"source": "controller", "lines": [214, 256], "meaning": "Sparse step clocks before/after LU; predictor retains priorK and port projection seeds fluctuation; Newton history appended only after evaluate returns; acceptance requires residual and mean bound."},
    {"source": "controller", "lines": [265, 296], "meaning": "Trialaccepted only updates localcandidate/R. Recoverable errors logged; time_limit propagates before new trial record append. Trial merit and accepted equilibrium are separate."},
    {"source": "controller", "lines": [299, 333], "meaning": "Durable state/R/s/K only assigned after newton returns; failedattempt verifies split state/R byte equality, s equality andK object identity, not a fresh K-array byte/numerical comparison. time_limit does not bisect; on_accept only after accepted record."},
    {"source": "controller", "lines": [335, 362], "meaning": "Outer controller catches error and returns partial accepted states plus diagnostics and originalfailure; endpoint false."},
    {"source": "native_mean", "lines": [113, 126], "meaning": "Public native Mean signature starts undeformed/zero-lift and exposes no savedstate/initialR/origin resume option."},
    {"source": "native_mean", "lines": [155, 212], "meaning": "Temporary last_tangent updated by tangent assembly; capture verifies same state, copies/read-only accepted arrays/tensors and matrix, then publishes accepted snapshot. Nativecall does not pass lower-level warm parameters."},
    {"source": "native_mean", "lines": [215, 253], "meaning": "Partial status/flags/diagnostics/copiedcounts preserved. Orderedcycle tasktarget-executed requires completed path and recordedpeak."},
    {"source": "native_mean", "lines": [256, 286], "meaning": "Writer iterates accepted snapshots only and persists cache; no final temporary tangent/candidate dump or force/tangent refresh."},
    {"source": "native_evaluate", "lines": [21, 81], "meaning": "One fresh native solve→cachedwrite→ordinarysummary. Controller time scope excludes imports/persistence; output must be new, no continuation parameters."},
    {"source": "native_batch", "lines": [14, 16], "meaning": "Batch options include initialization mode, not initialsavedstate/multiplier/origin."},
    {"source": "native_batch", "lines": [68, 80], "meaning": "Sharedtargets begin0 and nonnegative and must match taskpath; direct[1.20,1.15] not valid batchpath."},
    {"source": "CLI", "lines": [13, 28], "meaning": "CLI supports targets/time-limit/modes/initial-guess; no resume-file/warmstate argument. initial-guess is not a savedstate."},
    {"source": "kernel_timing", "lines": [350, 374], "meaning": "Original assembly field kernel_and_transfer label combines forcekernel and conversion; native Mean adds tangent duration to this label. No separately saved force/tangent percall profiling exists here."},
    {"source": "worker", "lines": [108, 129], "meaning": "Thin observed wrapper preserves originalrecoverable errors and started/completed asymmetry; it does not restartoriginalcontroller."},
    {"source": "worker", "lines": [173, 191], "meaning": "Originalsolve partial accepted cache gates, then batch terminal non-success before viewer launch. Gates do not convert partial path to success."},
]
peak_values = {k: peak[k] for k in ("d", "leg", "state_sha256", "assembler_state_sha256", "assembler_force_call", "assembler_tangent_call", "elapsed_seconds", "R_input", "q_out", "relative_residual", "minimum_J", "max_abs_Hu_per_mm")}
audit = {
    "status": "completed_saved_record_source_cost_audit",
    "current_repository_HEAD": HEAD,
    "original_authorized_source_commit": receipt["approved_source_commit"],
    "original_protocol_sha256": receipt["protocol_sha256"],
    "scope": "Bounded read of one actual alpha-half ordinary result/response/receipt/progress/peakJSON and relevant source. Only copied saved numbers/times/counts and ordinary identities/record inventory. No historical bulk scan, NPZ, HF import/API, observer, force/tangent/solver/HP, new scientific difference/ratio or plot.",
    "sources": sources,
    "source_line_evidence": evidence,
    "record_selection": "Only suffix after last loading1.20 entry in each ordered diagnostic list; same numerical1.15 loading entries earlier in path are excluded by sequence, not treated as unloading. Selected base/trial/linear fields retain original source order.",
    "actual_path_original": {k: r[k] for k in ("status", "accepted_states", "loading_peak_reached", "path_completed", "unload_endpoint_reached", "task_target_executed", "failure")},
    "original_settings": r["settings"],
    "selected_peak_original": peak_values,
    "selected_peak_progress_original": progress[-1],
    "selected_unload_failed_attempts_original": d["failed_attempts"],
    "selected_unload_newton_base_records_original": base_checks,
    "selected_unload_line_search_records_original": trials,
    "selected_unload_linear_records_original": linear,
    "ordinary_record_inventory": {
        "all_accepted_JSON_records": len(r["states"]), "all_progress_records": len(progress),
        "all_Newton_base_records": len(d["newton_history"]), "all_line_search_records": len(d["trials"]),
        "all_linear_records": len(d["linear_solve_diagnostics"]),
        "selected_unload_Newton_base_records": len(base_checks), "selected_unload_trial_records": len(trials),
        "selected_unload_linear_records": len(linear),
        "all_rejected_trial_reason_counts": dict(Counter(x.get("reason", "no_reason") for x in d["trials"] if not x["accepted"])),
        "selected_unload_rejected_trial_reason_counts": dict(Counter(x.get("reason", "no_reason") for x in trials if not x["accepted"])),
        "original_force_tangent_counts": r["call_counts"],
        "original_maximum_bisection_depth": d["maximum_bisection_depth"],
    },
    "copied_timing_records": {"controller_path": d["timing_seconds"], "native_mean": r["timing_seconds"], "response": response["timing_seconds"],
        "response_through_summary_seconds": response["evaluation_elapsed_seconds"],
        "helper": {k: receipt[k] for k in ("elapsed_seconds", "peak_sampled_RSS_bytes", "elapsed_scope")},
        "outer": {k: outer[k] for k in ("elapsed_seconds", "peak_sampled_tree_RSS_bytes", "stop_reason", "exit_code")}},
    "proved": [
        "Actual terminal is controller time_limit, from1.20 to1.15 atdepth0 with recorded durable bitwise rollback.14 accepted origin/loading states includingpeak persisted; no accepted unload or bisection. Outerstopnull and view0 mean this was not an external/view failure.",
        "Unloading actually ran a port_projection predictor and5logged Newton bases, with1full-step invalidJ rejection then validhalf-step and subsequent accepted line-search trials. Sixlinear diagnostics are retained with generalunsymmetrizedLU and mixed-unit backward errors explicitly diagnosticonly. Finaltrialaccepted is not equilibriumaccepted.",
        "Time checks are cooperative at controller evaluate/step/accept boundaries;9000 is not a hard interrupt inside assembly. Controller time starts after controller validation/setup entry, includes original callback and real solve, and differs from Mean/API/helper/outer clocks. Record9031.857919999995s total therefore does not itself prove a budget override.",
        "Controller durable state/R/s/K remains previousaccepted until newton returns. Rollback assert tests splitstate/R bytes, s equality andK object identity, not fresh K numerical or byte verification. Native accepted snapshots copied arrays/read-only tensors/matrix and writer persists only thattuple. Temporary last_tangent is not the durable controllercache and is not promised to roll back; no accepted peak overwrite or rejected-state persistence is shown.",
        "Kernel_and_transfer8850.413170600033s, all_assembly_attempts_wall8995.9231345s, sparse_solve31.222233099935693s and assembly2.150289499972132s are original aggregate labels. Their source accumulation has distinct scopes; failedassemblies wall is retained in finally but their absent returnfields are not added to fieldtiming. No cost fractions/differences or force-vs-tangent breakdown computed.",
        "Public nativeMean/API/CLI/batch currently expose no savedstate/multiplier/physical-origin resume parameters. Lower-level initial_state exists under restrictive origin/fixed/stage contracts; source starts stage0 withKNone and re-evaluates initial state. It is not an accepted-cache/no-compute replay or ready arbitrary descent from1.20to1.15."
    ],
    "supported_inference_not_direct_trace": "126 completed tangent calls versus125 logged Newtonbases, last peakcache tangentcall120 and selected5unloadbases, and source history appended only after evaluate returns support a later tangent assembly stopped at a budget check before its base record. The post-assembly clock at145 is a compatible source location. Actual logs do not carry per-clock stack/timestamps or the unlogged candidate; do not mark an exact executed clockline/candidate value as directly observed.",
    "not_proved": [
        "No accepted1.15 unloading equilibrium or complete unload/hysteresis/return path; finaltrial merit is not a fresh convergedbase.",
        "No evidence of Newtonlimit, exhaustedbacktracking, LUfailure, physicalbranchinstability/nonuniqueness or force/tangentbug as terminal cause. Timeout cannot prove absence of a future convergence difficulty either.",
        "No exact per-unload-call timestamps, separateforce/tangent/block costprofile, failedkernel detailedtime, or exact snapshot value of live last_tangent afterfailure. Aggregate timing cannot identify an optimization without separate evidence.",
        "No generic public nonzero saved-state continuation or downhill-origin contract has been implemented/validated merely because lower-level warm parameters exist. No newmodel/task restart semantics or acceptedsourcequalification established by this audit."
    ],
    "existing_cache_qualification_original": receipt["cached_production_gates"],
    "next_choice": {
        "now": "Use existing14 accepted snapshots for separately prepared saved-state actualdeformation/body3component display. Keep actual NOT_PASS, state/model identity, noHP and partialpath labels. No solve required for visualization; do not inject unsavedtrial5 asframe15.",
        "diagnosis": "Current source/records suffice to attribute terminal to budget exhaustion and identify cache/clock semantics. Do not rerun loading, relaxproductiongates or rewriteHu kernel to fix a nonexistent demonstratedbug; this read-only audit adds no qualification.",
        "later_if_needed": "Ifactualviews justify completingretraction, prepare an explicit saved-state/native continuation contract for physicalinitialmean, unchangedsplitstate/source/material/BC, multiplier and descendingtargets and cache revalidation. Review that functionalgap before choosing a minimal local experiment; do not silently mapinitial_guess toresume or force oldorigin semantics. No numericalcard/resourcewindow is created here.",
    },
    "actions": {"new_scientific_numbers_or_ratios": 0, "new_NPZ_decodes": 0, "new_HF_imports_or_calls": 0, "new_plots": 0, "formal_repository_mutations": 0},
    "qualification": "Saved-record/source cost audit only. Original M-ALPHA1 NOT_PASS and closedwindow, baseline24states/48HP, newalphaHP0, pressure/effectiveclamp/meshparameterstability/HF5 gaps remain unchanged.",
}
(EXT / "unload_cost_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def link(name, line):
    return f"[{Path(names[name]).name}:{line}]({(ROOT / names[name]).as_posix()}:{line})"

lines = [
    "# M-ALPHA1 保存回撤记录与耗时静查", "",
    "状态：`completed_saved_record_source_cost_audit`。这是一份现有普通记录／源码审计，不是新数值通过；未读NPZ、导入HF、调用observer/F/T/HP/solver、计算新科学差值/比率或绘图，未改正式代码。", "",
    f"当前正式main `{HEAD}`；原批准源码 `{receipt['approved_source_commit']}`。仅选择真实alpha-half result、response、回执、progress和相关入口，没有扫描旧9GB历史。文件SHA、逐条原记录及源码行号在unload_cost_audit.json。", "",
    "## 已证明的停止原因", "",
    "14个origin/loading状态接受并保存到1.20 mm；1.20→1.15 mm在depth0因原controller `time_limit: split average path wall-time budget exceeded` 停止，失败记录rollback_bitwise_equal=true。outer exit1、stop_reason=null，view_child0。停止不是外部stop或viewer失败；没有卸载接受态或二分接受态。原14缓存门passed不补齐15目标合同，也不新增HP/物理资格。", "",
    "选取各诊断列表最后loading1.20条目之后的有序后缀，排除此前loading1.15同数值记录。现有回撤包括1个predictor、Newton基点1..5、6条line-search和6条linear记录。predictor为port_projection：applied_dw=false、applied_dR=true；第一全步invalid_J后半步通过，后续trial继续。记录general sparse LU、未对称和mixed-unit backward error仅诊断的含义保持。", "",
    "| 回撤基点原记录 | relative_residual | minJ | R_input N | q_out mm |",
    "| --- | --- | --- | --- | --- |",
]
for row in base_checks:
    lines.append(f"| {row['newton_check']} | {row['relative_residual']} | {row['minimum_J']} | {row['R_input']} | {row['q_out']} |")
lines += ["", "第5基点后原trial5为factor1、accepted=true、phi=7.609458874889267e−07、minJ=2.3740207303790917e−05、R=0.3470376718304425 N。trial accepted只更新Newton局部候选；后续合格基点没有记录，不能当成卸载平衡态或可恢复第15帧。", "",
    "全路径force304开始／259完成、tangent126／126；125条Newton基点、178条trial、125条linear。拒绝库存为45条invalid_J和22条Armijo，属于原控制器内的bounded试探，不是外部重跑；计数未隐藏。回撤后缀中1条invalid_J，其余5条trial接受。", "",
    "## 时间范围及能解释到哪里", "",
    f"Controller在初始化后开始计时；evaluate前／组装后均检查，sparse step前／后检查，接受callback后再检查。源码：{link('controller',113)}、{link('controller',126)}、{link('controller',214)}、{link('controller',325)}。9000秒是这些检查点的协作限制，不能中断正执行的组装，因此记录略过9000秒不等于擅自延期。API明确该时间不含imports／persistence，见{link('native_evaluate',25)}。", "",
    "| 原记录时间／范围 | 原值 s |",
    "| --- | --- |",
    f"| peak接受controller elapsed | {peak['elapsed_seconds']} |",
    f"| peak progress callback helper elapsed | {progress[-1]['elapsed_seconds']} |",
    f"| controller path total | {d['timing_seconds']['total']} |",
    f"| kernel_and_transfer | {d['timing_seconds']['kernel_and_transfer']} |",
    f"| all_assembly_attempts_wall | {d['timing_seconds']['all_assembly_attempts_wall']} |",
    f"| assembly | {d['timing_seconds']['assembly']} |",
    f"| sparse_solve | {d['timing_seconds']['sparse_solve']} |",
    f"| callback | {d['timing_seconds']['callback']} |",
    f"| native Mean evaluation | {r['timing_seconds']['evaluation']} |",
    f"| response through-summary | {response['evaluation_elapsed_seconds']} |",
    f"| helper | {receipt['elapsed_seconds']} |",
    f"| outer | {outer['elapsed_seconds']} |", "",
    "上述全部复制原字段；不相减、不算成本占比、不估剩余回撤时间。kernel_and_transfer标签在Mean中还加上切线时长；成功返回的fields才进入该累计，而all_assembly_attempts_wall在finally覆盖未返回组装。两者不能当成同范围，也不能从聚合值判断45次invalid_J的单次成本或强行选一个优化。没有每个force/tangent/block的独立时间。", "",
    "126个完成切线调用与125条logged基点、峰值assembler_tangent_call120及5个卸载logged基点一致支持：下一次切线组装在预算检查处止步，基点尚未记录。evaluate组装后clock是符合源码的候选位置；日志没有每个clock的stack/timestamp，不能把具体执行行和未记录候选值写成直接观测。", "",
    "## 持久状态和临时缓存必须分开", "",
    f"控制器在newton返回后才赋durable state/R/s/K；失败assert检查split位移／R的逐bit相同、s相同及K对象身份，不是重新核K矩阵的字节或数值。time_limit直接传播不二分。见{link('controller',299)}、{link('controller',311)}、{link('controller',317)}。原峰值state及assembler_state SHA均为`{peak['state_sha256']}`，接受状态、独立state JSON与progress身份一致。", "",
    f"native_mean的last_tangent是每次tangent更新的临时cache，源码没有承诺把它随失败回滚。capture先核同状态，再copy数组、只读tensors及matrix并追加accepted；writer仅遍历accepted。见{link('native_mean',173)}、{link('native_mean',177)}、{link('native_mean',192)}、{link('native_mean',256)}。因此不能说‘所有缓存回滚’，但已保存的峰值接受缓存不会被失败候选覆写；最后trial或临时切线不在正式保存态中。此审计未读取任何实际NPZ值或临时cache。", "",
    "## 是否已有现成非零续算入口", "",
    f"公共solve_native_mean从zero lift／undeformed状态开始，signature没有initial_state／initial_R／target_origin；调用底层时也未传这些参数。见{link('native_mean',113)}、{link('native_mean',209)}。evaluate_native、CLI与batch只有initial_guess(tangent/port_projection)，不是resume-file。见{link('native_evaluate',21)}、{link('CLI',13)}、{link('native_batch',14)}。", "",
    f"底层确有warm-start实现：明确lift_origin、initial_state、initial_R、target_origin，warm lift必须bitwise匹配origin且fixed fluctuation为零。不能写成完全没有warm-start代码。但stage s必须从0开始且非负，物理mean=target_origin+s，初始K=None并重测初始态。见{link('controller',55)}、{link('controller',88)}、{link('controller',98)}、{link('controller',114)}。从physical1.20直接到1.15需要的下降不能靠[1.20,1.15]或负stage直接塞入现有合同；也不能把任意初始mean塞进不同target_origin并假称等价。不存在已验证的公共saved-state下降续算功能。", "",
    "## 最近取舍与未证明事项", "",
    "最近可见功能应是读取14接受保存态，复用现有square实际变形／三分量节点作用viewer；保持partial/failed、无新HP、原身份和压力／夹持限制，不把未接受trial补成卸载帧。这个显示不需要重做平衡。本静查已经定位time_limit与缓存语义，不必再长加载来证明相同事实。", "",
    "目前没有Newton上限、全回溯失败、LU失败、物理分支失稳／非唯一性或Hu力核／切线bug作为终态原因的证据；也不能反向保证以后增加时间一定会收敛。最后trial merit并不替代新基点验收。不能据这次超时放宽门、改Hu核、重扫参数或延长原卡。", "",
    "如果保存态显示后仍需要完成回撤，先准备原状态身份、物理初始mean、split representation、multiplier与下降目标的明确续算合同，区分可重复使用的接受缓存和必须重测的切线；再决定最小局部诊断。这里只给粗路线，不实现续算、不创建新数值卡或资源窗口。原24态／48HP仍属原alpha；本次alpha新态HP0及pressure／effective clamp／meshparameter stability／HF5缺口不变。", "",
    "## 原文件与身份", "",
]
for name in ("result", "response", "receipt", "outer", "progress", "peak_state", "controller", "native_mean", "native_evaluate"):
    lines.append(f"- [{names[name]}]({sources[name]['path']}) — SHA `{sources[name]['sha256']}`")
lines += ["", "其余源码SHA及选中原字段见同目录unload_cost_audit.json。所有审阅产物仅位于外部准备目录。", ""]
(EXT / "UNLOAD_COST_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({name: sha256((EXT / name).read_bytes()).hexdigest() for name in ("UNLOAD_COST_AUDIT.md", "unload_cost_audit.json")}, ensure_ascii=False))
