"""Independent ordinary-source/AST review record; no candidate imports or runs."""
import ast
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
names = ("execute_resume.py","resume_focused_budget.py","runner_source_author_receipt.json",
         "PREPARATION_RUNNER_NOTES.md","candidate_author_receipt.json")
pins = {name:sha256((HERE/name).read_bytes()).hexdigest() for name in names}
assert pins["execute_resume.py"] == "cf77839f81a8dbd55951161ae8e1cf92a2c35195d864d84e05aec52ae7ad7fd1"
assert pins["resume_focused_budget.py"] == "c1f7e596d76132c18f0054c1e10ac723808a3472e69b56b6ea946c6b2c4d9251"
runner = json.loads((HERE/"runner_source_author_receipt.json").read_bytes())
candidate = json.loads((HERE/"candidate_author_receipt.json").read_bytes())
for name in names[:2]:
    ast.parse((HERE/name).read_bytes(),filename=name)
    assert runner["sources"][name]["sha256"] == pins[name]
assert runner["candidate_author_receipt_sha256"] == pins["candidate_author_receipt.json"]
assert runner["notes_sha256"] == pins["PREPARATION_RUNNER_NOTES.md"]
assert runner["authorized"] is runner["executed"] is candidate["authorized"] is candidate["executed"] is False
assert runner["focused_test_nodeids"] == candidate["focused_test_nodeids"]
plan = runner["runtime_source_plan"]
assert len(plan) == 60 and len([p for p in plan if p.startswith("src/hf_eval/")]) == 52
for name,spec in plan.items():
    source = (HERE if spec["source_kind"] in ("reviewed_candidate_overlay","new_focused_budget_plugin") else ROOT)/spec["source"]
    assert sha256(source.read_bytes()).hexdigest() == spec["sha256"]
report = dict(status="pass_static_continuation_helper_plugin_interface_and_source_scope_no_execution",
    card="M-RESUME1",authorized=False,executed=False,
    reviewed_external_SHA256=pins,
    checks=[
        "Final helper/plugin AST parsed without imports; author receipts bind exact source bytes and five selected nodeids.",
        "Raw direct-human evidence, actual source publication and approved HEAD/protocol identities precede any candidate/test entry.",
        "Sixty-file runtime plan covers 52 HF modules, two CLIs, five test/fixture sources and plugin; all source bytes match its recorded SHA.",
        "Tests are separate, finite, -x, exact selected nodeids, with explicit autouse no-legacy/compiled guard and runtime HF import-path checks.",
        "Four controller fixtures and the real16-cell integration are distinct from production13440-cell F/T accounting; tests are not claimed to have zero F/T.",
        "One public API(None,None,...saved_result/index) uses the candidate reader/solver; wrapper does not rewrite task or duplicate continuation mechanics.",
        "Actual model/task/material/BC/source metadata checked before first production force; parent settings/options and original gates preserved except explicit new clock.",
        "Fresh nonzero anchor/K=None and original indices13/14 match the candidate; selected original split/R identity and parent failed/time_limit flags retained.",
        "Typed controller failures retain cached partial result/response before wrapper stops; resource/import failures promise only real existing artifacts.",
        "Successful segment requires actualN2..9, original target13/14, signed anchor identity, original cached gates and no qualification upgrade.",
        "F/T hooks correspond to production entries/result counters; save and summary add zero F/T; no claim of global hook coverage or new HP.",
        "Pure viewer uses a separate formal pure package, bindings to newly saved result/model/state/forces only, 3PNG/N-frameGIF and original no-qualification checks.",
        "Cooperative test/view children and wholehelper clock/RSS share stopfile and remainingwindow; wait real termination without timeout kill/force or retry.",
        "Final hashes/pins/source identities are checked before receipt plus late checkpoint; actual nonzero outer/helper overrides a provisional pass receipt."
    ],
    refinements="Final wrapper checks full-original/task flags at public result/response.path. Earlier continuation-only keys also exist in frozenf16a; their alleged absence was not an actual defect.",
    remaining_blockers=[],review_limits="Source/interface/AST only; future frozen protocol/card/packet require final ordinary review, and no runtime behavior or numerical success is claimed.",
    actual_actions=dict(candidate_import=0,HF_import=0,tests=0,NPZ_decode=0,force=0,tangent=0,
                        solver=0,observer=0,HP=0,JIT=0,render=0,formal_repository_mutation=0))
(HERE/"wrapper_peer_review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
md = """# M-RESUME1 包装／测试插件独立静审

结论：最终源码／接口静审通过，无待修阻断。仅普通 source、作者收据、SHA 与 AST；未导入候选、运行测试、解码 NPZ 或执行力学／绘图。authorized=false、executed=false，静审不代表未来数值通过。

两脚本与冻结候选一致：一次 API 使用保存原绝对 suffix，fresh anchor/K=None，原 gates／options／settings（除新clock）保持；局部与原目标索引、子段成功及父 NOT_PASS 区分。五项测试的真实16-cell F/T与13440-cell生产计数隔离。typed controller失败先保存实际缓存部分产物，资源／导入错误仅记录真实既存文件。成功后才调用独立原 pure viewer，不读新切线／矩阵作显示，也不转移父资格。

60个runtime源码条目及其SHA已普通核对，覆盖52个HF模块、2CLI、5test/fixture和plugin。auth/source proof须从未来真实批准来源建立；现脚本／AST不构成授权。有限子进程和wholehelper使用现stopfile及协作检查，无force／重跑；最后晚检查失败仍以实际outer为准。

最终包装在result及response.path核完整原路径标记。冻结候选continuation本来亦有这两字段，先前“字段不存在”推断不适用于真实冻结字节；修订未改变科学范围。协议和正式发布packet尚待最终静审，当前无新数值结果。

精确文件绑定和14项检查见 `wrapper_peer_review.json`。
"""
(HERE/"WRAPPER_PEER_REVIEW.md").write_text(md,encoding="utf-8")
print(json.dumps(dict(status=report["status"],JSON_sha256=sha256((HERE/"wrapper_peer_review.json").read_bytes()).hexdigest(),
                     MD_sha256=sha256((HERE/"WRAPPER_PEER_REVIEW.md").read_bytes()).hexdigest(),reviewed=pins),indent=2))
