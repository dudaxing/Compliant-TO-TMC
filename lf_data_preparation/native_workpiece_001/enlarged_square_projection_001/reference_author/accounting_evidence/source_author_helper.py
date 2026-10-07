"""Finalize external accounting source/diff records only; no additional reconstruction or FE."""
from pathlib import Path
from hashlib import sha256
import ast
import difflib
import json

AUTHOR = Path("D:/hf-workpiece-enlarge-author-20261007/projection_accounting_candidate")
BASE = AUTHOR/"counter_original_B028.py"
CURRENT = AUTHOR/"counter_attempts.py"
digest = lambda path:sha256(path.read_bytes()).hexdigest()
old,new = BASE.read_text(encoding="utf-8"),CURRENT.read_text(encoding="utf-8")
assert digest(BASE) == "b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3"
assert digest(CURRENT) == "a751fe07a682ff89c88b16d8d69325b1990d45c26114b8715414116580737ed9"
replacements = [
    ("fail closed. Predictor invalid-J bases are distinct from rejected trials.","fail closed. Predictor invalid-J bases and recovered invalid-J trials are distinct."),
    ("events, caches, attempts, invalid_bases, range_trials, failed_tangents = [], [], [], [], [], []",
     "events, caches, attempts, invalid_bases, range_trials, invalid_trials, failed_tangents = [], [], [], [], [], [], []"),
    ('incomplete = row["accepted"] is False and reason == "unsupported_arithmetic_range"',
     'incomplete = row["accepted"] is False and reason in ("unsupported_arithmetic_range", "invalid_J")'),
    ("Rejected range force has contradictory fields or no supported half-factor continuation",
     "Rejected incomplete force has contradictory fields or no supported half-factor continuation"),
    ("Range trial lacks the same-base half factor","Incomplete trial lacks the same-base half factor"),
    ('range_trials.append(dict(row, trial_index=ti, force_call=e["force_call"]))',
     '(invalid_trials if reason == "invalid_J" else range_trials).append(dict(row, trial_index=ti, force_call=e["force_call"]))'),
    ("rejected_range_trials=range_trials,","rejected_range_trials=range_trials,\n        rejected_invalid_J_trials=invalid_trials,")]
expected = old
for previous,current in replacements:
    assert expected.count(previous) == 1
    expected = expected.replace(previous,current)
assert expected == new
for path in (BASE,CURRENT,AUTHOR/"validate_saved_accounting.py"):
    source = path.read_text(encoding="utf-8");ast.parse(source);compile(source,str(path),"exec")
(AUTHOR/"counter_delta.diff").write_text("".join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
    fromfile="counter_original_B028.py",tofile="counter_attempts.py")),encoding="utf-8")
proof_file = AUTHOR/"saved_reproduction_001/report.json"
proof = json.loads(proof_file.read_text(encoding="utf-8"))
assert proof["status"] == "saved_only_reproduction_pass" and proof["all_bindings_unchanged"]
note = dict(status="external_accounting_candidate_with_saved_only_reproduction",source_transition=dict(
    role="Independent reference saved chronology counter",previous_file=BASE.name,previous_sha256=digest(BASE),
    current_file=CURRENT.name,current_sha256=digest(CURRENT),proof_kind="recovered_invalid_J_saved_accounting",
    prospective_formal_path="lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/reference_author/counter_attempts.py"),
    exact_source_delta="Seven explicit replacements; includes header/two error labels, incomplete reason union, one independent list, one routing expression and output field. No other source difference.",
    qualification_source=dict(file=proof_file.relative_to(AUTHOR).as_posix(),sha256=digest(proof_file)),
    original_failure=dict(file="../b028_saved_preflight_001/report.json",status="saved_accounting_unsupported",
        first_error="Unknown trial reason/completion cannot be attributed",checks_completed=619),
    actual_path=dict(complete_states=24,failed_attempts=0,newton_bases=176,trials=178,
        accepted_trials=152,armijo_rejected_complete_trials=2,invalid_J_incomplete_trials=14,range_incomplete_trials=10,
        force_started=354,force_completed=330,tangent_started=176,tangent_completed=176,linear_solves=175,
        predictor_solves=23,corrector_solves=152,first_range_force_ordinal=325),
    saved_reproduction_checks=proof["checks_completed"],regressions=proof["regressions"],tampered_chronologies=proof["tampered_chronologies"],
    unchanged_scope="All recursive attempts, predictor invalid_J bases, tangent-range branches, LU finite records, same-base/factor continuation, Armijo, mean/J/convergence checks, cache ordinals, full coverage and aggregate counters retain original conditions.",
    range_scope="rejected_range_trials still contains only unsupported_arithmetic_range; original first-range ordinal and input capture semantics unchanged.",
    invalid_J_scope="Explicit recovered line-search rejection counted as force-started/not-completed, no tangent. No fields or HP are computed for rejected states; their reason label is source/chronology evidence only, without state qualification.",
    unchanged_math="B850/aa86/B52/HP loop unchanged; production-bound70/sourcefreezes/results/force/tangent/controller not written.",
    no_reference_frozen_or_started=True,calls=proof["calls"],
    next_step="Independent source/saved-data review, then root explicitly adopts new counter role/pin/schema and binds this proof before any full reference freeze.")
(AUTHOR/"author_note.json").write_text(json.dumps(note,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
(AUTHOR/"README.md").write_text("""# 保存轨迹计数的最小 invalid_J 适配候选

新工件生产已完整通过24个目标。原 B028 在第619项计数检查拒绝当前轨迹，因为它只支持线搜索中的算术范围拒绝，尚未支持实际14次 `invalid_J` 拒绝。所有14条记录均无已完成力的 phi/J/R 字段，并按同一 Newton 基础的半步长继续；它们不能被算作完成的力或切线，也不获得独立物理资格。

此候选只把该原因列入未完成线搜索力分支，另用 `rejected_invalid_J_trials` 列表保存。原 `rejected_range_trials` 保持仅10条算术范围拒绝，首次范围力 ordinal仍325。原反力预测LU、递归尝试、Newton、Armijo、J/约束、缓存来源、范围输入与总计数门完全保留；不改生产力、切线、控制器或任何生产冻结文件。

纯保存数据验证得到176个完成Newton基础和178次trial，共354次力启动；152次接受trial加2次完整Armijo拒绝，共154次完整trial，因此力完成330次。14次J拒绝加10次范围拒绝共24次未完成力，均无切线。切线176次全部完成，LU175次为23次predictor与152次corrector，24个接受缓存全部对应完成且收敛的基础。核查共1817项。

旧010、pose002和soft001的原B028与新候选输出，在去除唯一新增空列表后逐项相等。伪造已完成phi、破坏半步长接续均被拒绝。验证仅解析JSON和运行纯计数逻辑，无模型、力、切线、求解、HP、几何API或渲染调用。

`counter_original_B028.py` 保留原SHA256 `b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3`，新候选SHA256为 `a751fe07a682ff89c88b16d8d69325b1990d45c26114b8715414116580737ed9`。`counter_delta.diff` 精确展示七处替换；`saved_reproduction_001`含完整计数和来源绑定，`author_note.json`记录范围与下一步。仍须独立审阅后，由root明确采用新参考counter角色、SHA和schema并绑定证明；当前未改参考候选、未冻结或启动任何正式参考。
""",encoding="utf-8")
print(json.dumps(dict(status="external_accounting_source_finalized",source_sha256=digest(CURRENT),
    original_sha256=digest(BASE),proof_sha256=digest(proof_file),source_exact_seven_replacements=True)))
