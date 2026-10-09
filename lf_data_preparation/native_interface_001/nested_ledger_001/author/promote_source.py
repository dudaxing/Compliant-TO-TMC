"""Promote reviewed M-LEDGER1 source only; no algorithm/API/plot execution."""
import argparse
import ast
from datetime import datetime,timezone
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
EXTERNAL = Path(__file__).parent
STAGE_REL = "lf_data_preparation/native_interface_001/nested_ledger_001"
STAGE = ROOT/STAGE_REL
MODULE_REL = "hf_repo/src/hf_eval/saved_workpiece_loads.py"
BASELINE = "909d7ba6a4bd3ba6bd11b97af830f4aeeef203c7"
sha = lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path:json.loads(path.read_text(encoding="utf-8"))
dump = lambda path,value:path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-sha",required=True)
    args = parser.parse_args()
    review_file = EXTERNAL/"preliminary_static_review.json"
    if sha(review_file) != args.review_sha:
        raise ValueError("Preliminary source review SHA differs")
    review = read(review_file)
    if not review["status"].startswith("pass") or review.get("required_corrections",[]):
        raise ValueError("Actual preliminary source PASS with no required corrections needed")
    if STAGE.exists() or (ROOT/MODULE_REL).exists():
        raise FileExistsError("Promotion targets must be new")
    module = EXTERNAL/"saved_workpiece_loads.py"
    old_worker = EXTERNAL/"prepare_worker.py"
    launcher = EXTERNAL/"launch_ledger.py"
    if (sha(module),sha(old_worker),sha(launcher)) != (
        "2359a89d4969b98c68baa8b932fb0001c426b898004cb579f76ff8bc727c5070",
        "01d206d0e3c5c9bfbab28b3e5d5fdbb6323ef92da5ca01925aeeec25094cbe77",
        "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"):
        raise ValueError("Concrete reviewed module/worker/launcher changed")
    original = old_worker.read_bytes().decode("utf-8")
    prepared = original.replace('"""M-LEDGER1 external source candidate; not authorized and not executed."""',
        '"""Frozen M-LEDGER1 source; separate card execution authorization required; not executed."""',1)
    old_tree,new_tree = ast.parse(original),ast.parse(prepared)
    old_tree.body.pop(0)
    new_tree.body.pop(0)
    assert ast.dump(old_tree,include_attributes=False) == ast.dump(new_tree,include_attributes=False)
    ast.parse(module.read_text(encoding="utf-8"))
    ast.parse(launcher.read_text(encoding="utf-8"))
    protocol = read(EXTERNAL/"protocol_draft.json")
    old_pins = protocol["existing_input_bindings"]
    assert len(old_pins) == 11 and protocol["source_baseline_commit"] == BASELINE
    for name,pin in old_pins.items():
        if sha(ROOT/name) != pin:
            raise ValueError("Closed input/source changed: "+name)
    publication_source = Path("D:/hf-native-workpiece-api-author-20261009/MLINK1_execution_review_001/publication_receipt.json")
    publication = read(publication_source)
    assert publication["status"] == "published_and_incrementally_restored_pass" and publication["published_commit"] == BASELINE
    assert publication["source_and_restore_clean"] and publication["remote_main_confirmed_equal"]
    STAGE.mkdir()
    author = STAGE/"author"
    author.mkdir()
    (ROOT/MODULE_REL).write_bytes(module.read_bytes())
    (STAGE/"execute_saved_ledger.py").write_bytes(prepared.encode("utf-8"))
    (STAGE/"launch_ledger.py").write_bytes(launcher.read_bytes())
    archive = {}
    for source,name in ((EXTERNAL/"input_scope_review.json","input_scope_review.json"),
        (EXTERNAL/"source_preparation.json","external_source_preparation.json"),
        (review_file,"preliminary_static_review.json"),(old_worker,"prepare_worker.py.source.raw"),
        (EXTERNAL/"M-LEDGER1_CARD_DRAFT.md","M-LEDGER1_CARD_DRAFT.md.raw"),
        (EXTERNAL/"protocol_draft.json","protocol_draft.json.raw"),
        (publication_source,"MLINK1_publication_receipt.json"),(Path(__file__),"promote_source.py")):
        destination = author/name
        destination.write_bytes(source.read_bytes())
        assert destination.read_bytes() == source.read_bytes()
        archive[name] = dict(source_path=str(source),sha256=sha(destination),bytes=destination.stat().st_size,byte_exact=True)
    card = (EXTERNAL/"M-LEDGER1_CARD_DRAFT.md").read_text(encoding="utf-8")
    card = card.replace("# M-LEDGER1 外部来源草案：", "# M-LEDGER1：",1)
    card = card.replace("**来源准备，尚未正式冻结、尚未授权执行、尚未执行算法或绘图。**",
        "**正式来源已准备并绑定，尚未获本卡执行授权、尚未执行算法或绘图。**",1)
    card = card.replace("目录中的 `input_scope_review.json` 是只读输入合同，不是执行许可。",
        "`author/input_scope_review.json` 与 `author/preliminary_static_review.json` 是来源静审，不是运行证据或执行许可。",1)
    card = card.replace("prepare_worker.py","execute_saved_ledger.py")
    card = card.replace("拟新阶段","本新阶段",1)
    card = card.replace("`positions.png`：固定工件参考位置与类别／角点／切面节点。",
        "`positions.png`：固定工件参考位置与类别／角点／切面节点；该坐标图无力箭头。",1)
    card = card.replace("本草案不允许直接执行。拟正式启动命令（当前不可执行，cwd仓库根）：",
        "本卡尚未获执行授权，不允许直接执行。授权后的唯一启动命令（cwd仓库根）：",1)
    card = card.replace("根代理独立审阅实际源码与输入合同后，才提升正式来源、冻结卡／协议、发布恢复并请求具体资源授权。",
        "根代理对本次正式来源／卡／协议完成独立最终静审、发布恢复后，才请求具体资源授权。",1)
    conditions = """## 执行通过与异常停止条件

通过需取得唯一实际执行的exit0、无stop，17份绑定前后SHA一致；旧24态登记身份匹配，但新账本严格四态0／8／13／23。每态703标准节点ID与原坐标完整、唯一，七类互斥并保留角点／交点，原六力字符串不变。直接whole fsums精确复现旧nodal／case整体；回并旧四组counts保持，六分量差在原8eps·L1界内，零界要求零差。一次ledger完成、三PNG写入和全部七项新输出齐全，收据记录真实资源与计算／显示范围。

首个输入／身份／分类／闭合／文件／渲染错误，或协作stop／时间／采样RSS越界，均not_pass并停止；不得重试、修复重跑、延期或force。来源AST／rawSHA静审仅证明待执行来源一致，不是上述运行通过证据。参考坐标图不显示力箭头，载荷在分量柱形与四缓存态类别曲线中显示；原结构变形仍查看M-VIEW1已有图件。

"""
    card = card.replace("## 资源与之后流程\n",conditions+"## 资源与之后流程\n",1)
    (STAGE/"M-LEDGER1_CARD.md").write_text(card,encoding="utf-8")
    (STAGE/"README.md").write_text("""# M-LEDGER1正式来源已准备，未授权／未执行

[执行卡](M-LEDGER1_CARD.md) · [协议](protocol.json) · [公共stdlib来源](../../../hf_repo/src/hf_eval/saved_workpiece_loads.py) · [薄调用器](execute_saved_ledger.py) · [来源收据](author/source_preparation.json)

main基线909d7ba的M-LINK1已经实际推送／恢复。最近的物理功能是从已有节点表组织载荷账本，保留材料＋Hu和共享角点；本阶段仅准备来源。原24态身份是登记输入，当前新输出限定0／8／13／23四态、每态703标准节点，不授予全24新账本或压力资格。公共模块可在将来接收全部记录，但本caller锁定四态。

拟新增两CSV、账本JSON、三Matplotlib诊断图与执行收据；位置图只有固定工件参考节点／类别，没有力箭头。原力字符串、符号与微小残量保留，直接whole fsum复现旧记录，七到四分区沿用无绝对地板的8eps·L1算术合同。本轮没有运行候选、分类／求和／绘图或任何NPZ／力核／HP／模型／求解。

公共模块与通用launcher原字节提升；151行caller只改首docstring和文件名，执行AST不变。原input scope、外部准备收据、预静审、worker／card／protocol草案和M-LINK1实际发布收据原字节归档。来源静审不是运行证据。下一步正式最终静审、发布恢复后请求一次180／240s、采样8GiB新卡授权；首错停止，无重试／延期／force。

外邻材料P诊断及材料＋Hu总边界力重建仍待账本实际结果之后决定。压力／有效夹持、网格／域收敛、全列切线及HF5尚未完成。旧结果／response／view／phase和资格均不改。
""",encoding="utf-8")
    protocol["status"] = "source_prepared_not_authorized_not_executed"
    protocol["created_utc"] = datetime.now(timezone.utc).isoformat()
    protocol["stage"] = protocol.pop("future_stage")
    protocol.pop("future_source_bindings")
    protocol["phases"]["ledger"]["argv"][0] = STAGE_REL+"/execute_saved_ledger.py"
    new_names = [MODULE_REL,STAGE_REL+"/execute_saved_ledger.py",STAGE_REL+"/launch_ledger.py",
        STAGE_REL+"/M-LEDGER1_CARD.md",STAGE_REL+"/author/input_scope_review.json",STAGE_REL+"/author/MLINK1_publication_receipt.json"]
    new_pins = {name:sha(ROOT/name) for name in new_names}
    protocol["prepared_source_and_provenance_bindings"] = new_pins
    protocol["bindings"] = dict(sorted({**old_pins,**new_pins}.items()))
    assert len(protocol["bindings"]) == 17
    protocol["pending"] = "Root independent final static review of exact formal source/card/protocol, publication/restoration, then separate human new-card execution authorization"
    dump(STAGE/"protocol.json",protocol)
    for name,pin in protocol["bindings"].items():
        assert sha(ROOT/name) == pin
    diff = "".join(difflib.unified_diff(original.splitlines(keepends=True),prepared.splitlines(keepends=True),
        fromfile="external_prepare_worker.py",tofile="formal_execute_saved_ledger.py"))
    receipt = dict(schema_version="M-LEDGER1-formal-source-preparation-1.0",status="source_prepared_not_authorized_not_executed",
        created_utc=datetime.now(timezone.utc).isoformat(),client_source_date="2026-10-10",source_baseline_commit=BASELINE,
        authorized_write_scope=[MODULE_REL,STAGE_REL+"/"],existing_files_modified=0,run_output_created=False,
        execution_authorized=False,execution_started=False,formal_final_static_review_pending=True,
        source_preliminary_review=dict(path="author/preliminary_static_review.json",sha256=args.review_sha,status=review["status"],source_review_not_runtime_evidence=True),
        preserved_archives=archive,module_byte_identical=True,module_sha256=sha(ROOT/MODULE_REL),
        original_worker_sha256=sha(old_worker),formal_worker_sha256=sha(STAGE/"execute_saved_ledger.py"),worker_lines=len(prepared.splitlines()),
        worker_executable_AST_identical=True,worker_docstring_only_diff=diff,worker_file_rename="prepare_worker.py -> execute_saved_ledger.py",
        launcher_byte_identical=True,launcher_sha256=sha(STAGE/"launch_ledger.py"),card_sha256=sha(STAGE/"M-LEDGER1_CARD.md"),protocol_sha256=sha(STAGE/"protocol.json"),
        protocol_bindings=17,old_input_bindings=11,new_source_card_scope_publication_bindings=6,all17_resolve_and_raw_SHA_match=True,
        publication_receipt_original_SHA256=sha(publication_source),selected_new_states=[0,8,13,23],registered_old_states=24,
        promoted_writer_path="author/promote_source.py",promoted_writer_sha256=sha(author/"promote_source.py"),
        source_only_actions=dict(candidate_imports_calls=0,CSV_rows_parsed_classified_summed=0,force_sums=0,Matplotlib_import_render=0,
            tests=0,HF_API=0,NPZ_HP_F_T_model_solve_observer=0,source_AST_and_raw_SHA_only=True),
        qualification="Selected4 saved-node classification candidate only; old15HP gates not rerun, no newpressure/full24/totalHu boundary/effectivegrip/convergence/HF5",
        resources=dict(helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=8*1024**3,once_first_error_no_retry_repair_rerun_extension_force=True))
    dump(author/"source_preparation.json",receipt)
    files = sorted([ROOT/MODULE_REL]+[path for path in STAGE.rglob("*") if path.is_file()])
    print(json.dumps(dict(status=receipt["status"],files=[path.relative_to(ROOT).as_posix() for path in files],
        files_count=len(files),bytes=sum(path.stat().st_size for path in files),card_sha256=receipt["card_sha256"],protocol_sha256=receipt["protocol_sha256"],
        source_preparation_sha256=sha(author/"source_preparation.json"),module_sha256=receipt["module_sha256"],worker_sha256=receipt["formal_worker_sha256"],
        source_promotion_writer_sha256=receipt["promoted_writer_sha256"],bindings=17,run_created=False),indent=2))

if __name__ == "__main__":
    main()
