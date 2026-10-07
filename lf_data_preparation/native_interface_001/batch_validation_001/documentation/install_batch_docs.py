"""Record actual mock-only batch results and link the next unexecuted task."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/batch_validation_001'
sha = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    review_file = AUTHOR/'review/batch_documentation_review.json'
    review = json.loads(review_file.read_bytes())
    assert review['status'] == 'pass_saved_only' and review['blocking_findings'] == []
    pairs = {'documentation/docs/NATIVE_BATCH_INTERFACE.md':'docs/NATIVE_BATCH_INTERFACE.md',
             'documentation/stage/RESULTS.md':STAGE+'/RESULTS.md'}
    for source,target in pairs.items():
        assert sha(AUTHOR/source) == review['source_sha256'][source]
        assert not (ROOT/target).exists()
    receipt = json.loads((ROOT/STAGE/'run_001/execution_receipt.json').read_bytes())
    launch = json.loads((ROOT/STAGE/'functional_launch.json').read_bytes())
    assert receipt['status'] == launch['status'] == 'pass'
    prefixes = {
        'README.md': '## 当前：薄批量入口已通过纯功能检查\n\n两例顺序评价入口与 CLI 已实现，15项 JSON/mock 检查通过；真实科学调用为0。各例保持独立输入、输出与失败/参考/图来源，首个非success停止。新两例0.025mm计算尚未执行，HF5整体未完成。[批量用法与功能流程](docs/NATIVE_BATCH_INTERFACE.md)；[当前进度](docs/CURRENT_STATUS.md)。\n',
        'docs/CURRENT_STATUS.md': '## 当前：两例批量入口功能验证完成\n\n新增 native_batch API/CLI，15项纯功能检查一次通过：mock10 started /8 returned /2 escaped，9类科学计数为0，helper3.1671813s /outer4.2031513s。既有25份力学/几何相关源与2份单例接口保持原字节。全批先核共享物理声明和新输出，再顺序各例一次，首非success保留原失败/partial并记录后续not_run原因。\n\n真实两例仍待下一阶段：原canonical/native_fine各自0.025mm任务，明确[0,.005,.010,.025]、minimum_increment6.25e-5，complete/full/tangent；新whole2400/outer2460s、8GiB与共享controller1800s只是下一卡计划，尚未执行。两设计和native网格均不同，不作排名或收敛结论。原固定工件24态/48HP物理证据及单例真实API证据保留，HF5/压力/有效接触/匹配网格等整体边界不扩。[接口与示例](NATIVE_BATCH_INTERFACE.md)；[实际功能结果](../lf_data_preparation/native_interface_001/batch_validation_001/RESULTS.md)。\n',
        'docs/NATIVE_EVALUATION_INTERFACE.md': '## 当前补充：顺序两例批量接口\n\n既有单例接口不变；新增 evaluate_native_batch 与 CLI，完整用法见[批量接口](NATIVE_BATCH_INTERFACE.md)。15项 JSON/mock 检查通过，覆盖共同物理声明、首错停止及独立身份；新两例真实0.025mm运行尚未执行。本次功能不增加数值、参考、压力、接触或HF5资格。\n',
        'docs/RESUME_DEVELOPMENT.md': '## 最近恢复入口：批量功能已完成，真实两例待执行\n\n先读[当前状态](CURRENT_STATUS.md)和[批量接口用法](NATIVE_BATCH_INTERFACE.md)。main新增两例顺序入口并通过15项mock检查；下一项是明确manifest中的两个原0.025mm任务及新资源卡。旧科学窗口均已关闭，新批量没有真实结果；不复用旧单例参考或图作为新batch资格。\n',
    }
    changes = []
    for name,prefix in prefixes.items():
        path = ROOT/name
        before = path.read_bytes()
        history = '\n---\n\n以下完整原字节保留为7e54e34阶段历史；批量当前状态以上方为准。\n\n'
        path.write_bytes((prefix+history).encode('utf-8')+before)
        changes.append(dict(path=name,before_sha256=sha256(before).hexdigest(),after_sha256=sha(path)))
    for source,target in pairs.items():
        (ROOT/target).write_bytes((AUTHOR/source).read_bytes())
        changes.append(dict(path=target,source=source,sha256=sha(ROOT/target)))
    context = ROOT/STAGE/'documentation'
    context.mkdir()
    for source in ('documentation/data_check.json','review/batch_documentation_review.json','install_batch_docs.py'):
        (context/Path(source).name).write_bytes((AUTHOR/source).read_bytes())
    progress = dict(schema_version='native-batch-functional-progress-1.0',status='functional_pass',
        baseline_commit='7e54e34d82b5a98191c6d777f0fc85942f03eee7',
        actual_tests=receipt['tests'],actual_mock_calls=receipt['mock_transport_calls'],
        actual_scientific_calls=receipt['scientific_calls'],
        helper_seconds=receipt['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
        helper_RSS_bytes=receipt['peak_sampled_RSS_bytes'],outer_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
        protocol_sha256=receipt['protocol_sha256'],reference_HP_calls=0,new_physical_views=0,
        HF5_qualified=False,ranking_qualified=False,real_batch_executed=False,
        next='New two-case .025mm four-target forward window, then each actual-N independent reference and views',
        completed_utc=receipt['completed_utc'])
    (ROOT/STAGE/'closure_progress.json').write_text(json.dumps(progress,indent=2)+'\n',encoding='utf-8')
    record=dict(status='installed',documentation_review_sha256=sha(review_file),files=changes,
        new_scientific_calls=0,created_utc=datetime.now(timezone.utc).isoformat())
    (ROOT/STAGE/'documentation_install.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='installed',current_links=len(prefixes),new_docs=len(pairs),new_scientific_calls=0)))


if __name__ == '__main__':
    main()
