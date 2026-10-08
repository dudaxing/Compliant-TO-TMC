# 固定工件真实 API：24态完整路径与可视化已完成

2026-10-08，W-API1完整加载—卸载已完成；明确批准的W-VIEW1唯一一次保存观察/绘图也成功闭卡，几何24/24、节点力24/24，3 PNG与全24帧GIF可人工检查。原力学源、输入/材料/端口/约束保持，W-VIEW1新增F/T/求解/HP均0；原窗口不续用。

峰值d=1.2 mm：尖端到底面距离0.0057303162 mm，输入反力0.4072527715 N，下半工件Fy=0.1193619515 N，两侧法向幅值和0.2387239030 N；卸载后回到初始形态，力接近零。图为真实×1与显示镜像；力箭头为工件节点弱式力。J色图为单元平均，与最小积分点J分开。

[目标、实现、依据、效果与限制](../functional_views/native_api_workpiece_20261008/complete_001/RESULTS.md) · [结构/尖端与力曲线](../functional_views/native_api_workpiece_20261008/complete_001/run_001/view/comparison.png) · [全24态动画](../functional_views/native_api_workpiece_20261008/complete_001/run_001/view/fixed_square/actual_states.gif) · [含图摘要响应](../functional_views/native_api_workpiece_20261008/complete_001/run_001/response_with_views.json)。新views=matched仅表示保存观察/图件匹配，独参仍未提供，producer flags仍false；原API生产JSON未改。

整体目标仍为独立有限变形/TMC正向评估，HF不包含优化。新producer独参、接触压力/有效夹持、匹配网格/域收敛、圆体自身任务、自由体/摩擦、正式标签/排名及HF5整体仍未完成。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

<details>
<summary>W-API1原生产闭卡记录（当时新HP/观察/渲染均0）</summary>

# 固定工件真实 CLI/API：完整加载—卸载已完成

2026-10-08，经用户明确批准，W-API1 唯一一次真实执行成功闭卡：24 原目标、24 接受态，1.2 mm 加载峰后卸载回 0 mm；CLI/batch/API/构模/求解/保存/摘要各一次，保存及摘要新增 F/T 为0。28 原 HF 源及36绑定不变。

峰值输入反力0.4072527715 N，加权输出位移1.0088461324 mm，下半工件 signed Fy=0.1193619515 N（材料0.1178513816、正则0.0015105699）；两侧法向幅值和0.2387239030 N，与 full mirrored net (-0.0048162478,0) N 分开。回零输入反力约1.208e-24 N。实际 helper2170.0202 s / outer2171.3780 s，原缓存生产门通过。

[目标、实现、理由、实际效果和限制](../lf_data_preparation/native_interface_001/workpiece_forward_001/RESULTS.md)及[新真实 response](../lf_data_preparation/native_interface_001/workpiece_forward_001/run_001/fixed_square/response.json)是本次恢复入口。新 HP/观察/渲染均0，reference/views未提供，producer flags仍false；旧固定工件48HP和旧图资格不转移。下一步优先复用保存态 viewer 展示新 API 数据，另立新范围/资源；W-API1已关闭不重跑。

整体目标仍是供外部 LF/N4 研究层使用的独立有限变形/TMC正向评估，不包含优化。接触/压力资格、匹配网格与域收敛、圆体自身任务、自由体/摩擦、正式标签及HF5整体仍未完成。main开发，origin保持 https://github.com/dudaxing/Compliant-TO-TMC.git。


</details>

<details>
<summary>65020bd及更早阶段历史原文（原字节完整保留；旧“下一步”与未执行表述只指当时）</summary>

## 当前补充：顺序两例批量接口

既有单例接口不变；新增 evaluate_native_batch 与 CLI，完整用法见[批量接口](NATIVE_BATCH_INTERFACE.md)。15项 JSON/mock 检查通过，覆盖共同物理声明、首错停止及独立身份；新两例真实0.025mm运行尚未执行。本次功能不增加数值、参考、压力、接触或HF5资格。

---

以下完整原字节保留为7e54e34阶段历史；批量当前状态以上方为准。

## 当前追加：真实API、同结果参考及保存视图已完成

首次纯功能验证为下方8330原文中的21项JSON/模拟集成、4份已有结果摘要和真实科学调用0。随后本次从无关cwd、显式repo，通过evaluate_native真实完成已有无工件夹持器0→0.001mm：2态、生产4F/3T，七个真实委托各一次，保存阶段新增F/T为0。默认complete/full/tangent和25个既有核心文件不改。

新独立参考针对本次同result全部2态完成4次新HP、38640检查，原力/PORT方向切线作用/平衡门通过；新保存视图仅用缓存，×1和标明×1000、全部实际帧，0新力学调用。helper/outer实际：生产86.092118/88.071228s，参考39.578755/40.323424s，视图3.227272/3.501443s。

[实际效果、图及各阶段卡](../lf_data_preparation/native_interface_001/real_forward_001/RESULTS.md)；[同参考/视图的紧凑响应](../lf_data_preparation/native_interface_001/real_forward_001/run_001/qualified_response.json)。原response保持不覆盖，新响应accepted/full-path参考匹配单独为true；生产者原flags保持false，全列、接触/压力/夹持、HF5不升级。请求完整路径仅指此例0→1µm，工件力为null；此例不替代此前固定方体24态的物理证据。下一项仍须是明确同任务比较或匹配网格步骤，小批量和HF5重复性尚未完成。

---

以下完整原字节为8330b821首次纯功能验证与接口用法历史；其中“尚未执行真实平衡”及其下一步只描述当时，现状以上方为准。

# 原生正向评价接口

整体目标是让外部 LF/N4 研究层把普通几何和明确任务交给 HF，取得独立的有限变形/TMC 响应。HF 不包含优化器，也不导入、安装或子进程调用 dmftd。本次新增薄接口，复用已实现的 native_mean 求解器；25 个既有核心源文件保持原字节。

## 已完成的功能与本轮验证

`hf_eval.native_evaluate.evaluate_native` 依次调用一次现有 solver、一次缓存保存和一次紧凑响应生成。它不预先重复构模、不修复重试；已有输出目录会被拒绝。现有 `solve_native_mean.py` CLI 仅新增显式 `--initial-guess` 参数，默认仍为 tangent。

本轮一次纯功能窗口 helper120 s / outer150 s / 采样8 GiB：21 项通过，helper 实际 7.560 s，外层 7.913 s。四份真实保存结果已导出；短路径第五例只作测试。模拟 transport solve/write 调用为 {'solve': 7, 'cached_write': 6}，包括受控错误，它们不是力学调用。真实模型、F/T、solver、HP、几何/节点观察、NPZ 读取均为0；不运行旧科学回归套件。

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
| 2mm完整24态 | [response](../lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_right2col_response.json) |
| 4mm完整24态 | [response](../lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_right4col_response.json) |
| 无工件4态 | [response](../lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_no_workpiece_response.json) |
| 失败9态前缀 | [response](../lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_failed_prefix_response.json) |

4mm任务目标在加载index13、d=1.2mm；请求终点在卸载index23、d=0mm。失败前缀末态0.86875mm，原invalid_J保留，target_response和endpoint均null。2/4mm参考及已有4幅图链接匹配；无工件/失败前缀不借用资格。

[执行回执](../lf_data_preparation/native_interface_001/api_validation_001/run_001/execution_receipt.json)、[启动回执](../lf_data_preparation/native_interface_001/api_validation_001/functional_launch.json)、[阶段卡](../lf_data_preparation/native_interface_001/api_validation_001/functional_protocol.json)、[当前进度](../lf_data_preparation/native_interface_001/api_validation_001/closure_progress.json)、[源码与独审索引](../lf_data_preparation/native_interface_001/api_validation_001/author/INDEX.md)。

下一步以独立的新资源窗口，通过本入口完成一次小型真实正向任务，再据实际结果接同任务比较和小批量。当前HF5整体仍未完成；压力/接触定义、匹配网格、圆体自身任务、自由工件和摩擦按物理证据逐项推进。


</details>
