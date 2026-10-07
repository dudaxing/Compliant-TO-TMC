"""Record a closed saved-only interface phase, without executing mechanics."""
from pathlib import Path
from hashlib import sha256
import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    relative = 'lf_data_preparation/native_interface_001/api_validation_001'
    stage = root / relative
    read = lambda name: json.loads((stage / name).read_bytes())
    receipt = read('run_001/execution_receipt.json')
    launch = read('functional_launch.json')
    protocol = read('functional_protocol.json')
    installation = read('installation_receipt.json')
    assert receipt['status'] == launch['status'] == 'pass'
    assert receipt['tests_failed'] == receipt['tests_errors'] == receipt['tests_skipped'] == 0
    assert receipt['tests_passed'] == protocol['expected_tests']
    assert receipt['formatter_calls_completed'] == 4
    assert not any(receipt['scientific_calls'].values())
    assert receipt['all_bindings_unchanged'] and launch['all_bindings_unchanged']
    assert all(sha256((root / name).read_bytes()).hexdigest() == pin
               for name, pin in installation['original_core_sha256'].items())
    exports = receipt['response_exports']
    four = json.loads((root / exports['right4col']['file']).read_bytes())
    failed = json.loads((root / exports['failed_prefix']['file']).read_bytes())
    assert four['path']['completed'] and four['independent_reference']['full_path_reference_pass']
    assert failed['status'] == 'failed' and failed['target_response'] is None
    progress = dict(status='functional_pass_no_new_mechanics', baseline_commit=protocol['baseline_commit'],
        tests_passed=receipt['tests_passed'], helper_seconds=receipt['elapsed_seconds'],
        outer_seconds=launch['elapsed_seconds'], sampled_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
        limits=protocol['phases']['functional'], sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        scientific_calls=receipt['scientific_calls'], mock_transport_calls=receipt['mock_transport_calls'],
        exports=exports, original_core_files_unchanged=len(installation['original_core_sha256']),
        scope='Saved JSON semantics and mocked call integration; no new real forward, HP, observation or physical qualification',
        next_step='One separately bounded small real evaluation through the new API, then same-task comparisons and small batches; no reopened historical cards')
    (stage / 'closure_progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    guide = f'''# 原生正向评价接口

整体目标是让外部 LF/N4 研究层把普通几何和明确任务交给 HF，取得独立的有限变形/TMC 响应。HF 不包含优化器，也不导入、安装或子进程调用 dmftd。本次新增薄接口，复用已实现的 native_mean 求解器；25 个既有核心源文件保持原字节。

## 已完成的功能与本轮验证

`hf_eval.native_evaluate.evaluate_native` 依次调用一次现有 solver、一次缓存保存和一次紧凑响应生成。它不预先重复构模、不修复重试；已有输出目录会被拒绝。现有 `solve_native_mean.py` CLI 仅新增显式 `--initial-guess` 参数，默认仍为 tangent。

本轮一次纯功能窗口 helper120 s / outer150 s / 采样8 GiB：{receipt['tests_passed']} 项通过，helper 实际 {receipt['elapsed_seconds']:.3f} s，外层 {launch['elapsed_seconds']:.3f} s。四份真实保存结果已导出；短路径第五例只作测试。模拟 transport solve/write 调用为 {receipt['mock_transport_calls']}，包括受控错误，它们不是力学调用。真实模型、F/T、solver、HP、几何/节点观察、NPZ 读取均为0；不运行旧科学回归套件。

验证覆盖完整2/4mm工件周期、无工件、真实失败前缀、成功短路径但未执行任务目标、不匹配/不完整参考、图像工况归属、任意cwd调用、选项传递、阶段错误以及拒写已有目录。图像归属核对实际同label summary的全部保存态，阻止重名或互换label借用另一工况动画。

本轮尚未通过新入口执行真实平衡路径，因此此处的集成证据是模拟调用，数值证据来自已闭卡的原结果。原力学资格不扩展到压力、有效接触/夹持定义、全切线列、HF5、网格/域收敛或一般工件。

## 一次新评价

在 HF 环境把 `<repo>/hf_repo/src` 放入 Python 模块路径，调用：

```python
from hf_eval.native_evaluate import evaluate_native

repo = "/path/to/your/checkout"
response = evaluate_native(
    "jobs/case/geometry.json", "jobs/case/task.json", "results/new_case",
    repo_root=repo, response_mode="mechanical", tangent_mode="chunk256",
    initial_guess="port_projection", time_limit_seconds=180.0,
)
```

几何必须是现有原生适配器支持的普通几何描述，任务必须符合现有 native_mean 合同；接口本身不重采样、不优化或修改几何。例中的jobs路径是用户新任务的占位路径，不是已执行的科学卡。

从任何工作目录使用 `<HF Python> <repo>/hf_repo/scripts/evaluate_native.py --repo <repo> --geometry jobs/case/geometry.json --task jobs/case/task.json --output results/new_case`。相对输入/输出按明确repo解析，绝对路径保持其位置。省略repo时按调用者cwd解析。

选项默认为 complete/full/tangent；机械模式、chunk256及port_projection均须显式指定。任务自带有序path时默认执行该path；`--targets`可显式给出目标，但任务含path时必须与之精确一致，改变加载/卸载路径须先修改明确task。未指定minimum_increment时继续使用原CLI规则：目标列表第二个值除16（即targets[1]/16）；这不是自动搜索其它非零目标。直接API也可传入DisplacementSettings；自定义settings与单独的非默认控制限不能混用。

`--time-limit`是控制器求解时钟，构模、保存和CLI启动不全在此时钟内。response中的evaluation_elapsed_seconds计到summary结束，不含response写出和CLI启动/stdout；需要完整资源窗口时由外层启动器另行控制。CLI exit0表示原路径success，failed/error为exit1；已有输出不会覆盖。

## 只读取已有结果

`hf_eval.native_response.summarize_saved_native_result`只读取JSON、声明的参考源文件和已有图像字节，不打开NPZ或调用力学。配套`hf_repo/scripts/summarize_native_mean.py`提供 --repo/--result/--output，以及可选 --reference/--view-manifest。output是全新JSON文件；该CLI的exit0只表示摘要写出成功，原计算status仍可能failed。

| 字段 | 含义 |
|---|---|
| status/path.completed | 原求解状态及请求路径是否完成；参考不匹配不改写生产状态 |
| target_response | 完整路径且实际执行任务目标时的响应，否则null |
| requested_endpoint_response | 完整请求路径的最后原目标；可为卸载回零，与加载任务目标分开 |
| maximum_loading_stroke | 最大加载位移的接受态，不是自动最大力 |
| last_accepted | 最后接受状态，失败可保留真实二分步；没有状态为null |
| failure | 原控制器code/reason（equilibrium phase），或包装异常的观测stage/class/code/reason |
| identity/options | result/model/task身份、来源路径与模式；旧schema默认值明确标注来源 |
| independent_reference | 同result/model/all-N/2N bookkeeping及声明源字节是否匹配；不重新审计HP/NPZ存档 |
| views | 已保存图像链接、原SHA和匹配工况；不新绘图或授予物理资格 |

R为半模型输入反力；下半工件力保留signed total/material/regularization、holding和镜像语义。2|Fy|是两侧法向幅值和，不是装配净力；q_out是加权端口位移，不是钳尖间隙。J/Hu是保存的全局标量，node-window clearance保持原栅格诊断范围。无工件响应为null，不填伪造零力。数组SHA只引用声明，不表示本轮读取核查数组。生产者原资格flags保持原值，独立参考匹配单独报告；接触/压力/夹持/全列/HF5资格不由此升级。

## 本轮可审查输出

| 保存结果 | 紧凑响应 |
|---|---|
| 2mm完整24态 | [response](../{exports['right2col']['file']}) |
| 4mm完整24态 | [response](../{exports['right4col']['file']}) |
| 无工件4态 | [response](../{exports['no_workpiece']['file']}) |
| 失败9态前缀 | [response](../{exports['failed_prefix']['file']}) |

4mm任务目标在加载index13、d=1.2mm；请求终点在卸载index23、d=0mm。失败前缀末态0.86875mm，原invalid_J保留，target_response和endpoint均null。2/4mm参考及已有4幅图链接匹配；无工件/失败前缀不借用资格。

[执行回执](../{relative}/run_001/execution_receipt.json)、[启动回执](../{relative}/functional_launch.json)、[阶段卡](../{relative}/functional_protocol.json)、[当前进度](../{relative}/closure_progress.json)、[源码与独审索引](../{relative}/author/INDEX.md)。

下一步以独立的新资源窗口，通过本入口完成一次小型真实正向任务，再据实际结果接同任务比较和小批量。当前HF5整体仍未完成；压力/接触定义、匹配网格、圆体自身任务、自由工件和摩擦按物理证据逐项推进。
'''
    (root / 'docs/NATIVE_EVALUATION_INTERFACE.md').write_text(guide, encoding='utf-8')
    fronts = ['README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md', 'docs/PROJECT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md']
    preserved = {}
    for name in fronts:
        path = root / name
        raw = path.read_bytes()
        prefix = '../docs/' if name.startswith('hf_repo/') else 'docs/' if name == 'README.md' else ''
        text = f'''## 当前：薄原生评价接口已通过纯功能验证

HF保持独立正向评价、不含优化器；4mm固定方体完整24态、48新HP及已有变形/力视图仍是最近的实际力学证据。新增一次evaluate_native入口、保存JSON摘要及任意cwd CLI，{receipt['tests_passed']}项功能测试和4份保存响应导出通过；25核心文件原字节保持，真实科学调用为0。本轮模拟集成不表示已从新入口执行真实任务，HF5整体尚未完成。

响应区分任务目标、请求终点和最后接受态；参考与图链接核对同结果/模型/全部状态身份。下一步独立新窗口执行小型真实API任务，再推进同任务比较与小批量；压力/接触判据和匹配网格等仍待验证。[接口用法与本轮效果]({prefix}NATIVE_EVALUATION_INTERFACE.md)。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；旧执行卡不重跑。

---

以下原字节保留为前一阶段历史；当前接口状态以上方及接口报告为准。

'''
        path.write_bytes(text.encode('utf-8') + raw)
        preserved[name] = dict(before_sha256=sha256(raw).hexdigest(), before_bytes=len(raw),
            old_suffix_byte_exact=path.read_bytes().endswith(raw), after_sha256=sha256(path.read_bytes()).hexdigest())
    physical = root / 'docs/PHYSICAL_FUNCTION_PROGRESS.md'
    old = physical.read_bytes()
    text = old.decode('utf-8').replace('统一一次评价入口；新模型不继承旧资格', '新入口真实任务尚待执行；新模型不继承旧资格')
    text = text.replace('单任务后端和保存证据可用，LF/N4研究层保留', '薄一次API/CLI及保存摘要已实现；21项JSON/模拟集成通过，4份摘要可审，LF/N4研究层保留')
    text = text.replace('薄评价接口、同任务小批量、紧凑响应/失败/来源和重复性合同', '新API真实平衡路径、同任务小批量和完整HF5重复性合同')
    text += '\n[薄评价接口用法与实际验证范围](NATIVE_EVALUATION_INTERFACE.md)。\n'
    physical.write_text(text, encoding='utf-8')
    preserved['docs/PHYSICAL_FUNCTION_PROGRESS.md'] = dict(before_sha256=sha256(old).hexdigest(),
        update='Current capability cells and interface link; historical science files untouched',
        after_sha256=sha256(physical.read_bytes()).hexdigest())
    (stage / 'documentation_receipt.json').write_text(json.dumps(dict(status='updated_after_functional_pass',
        documents=preserved, new_scientific_calls=0), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status='interface_docs_updated', tests=receipt['tests_passed'], exports=4)))


if __name__ == '__main__':
    main()
