# L-BPREP1 批量 LF 输入准备结果：PASS

2026-10-16（Asia/Seoul），基线 main `8772efc36f682788c0f829f690403f3405706e4d`。唯一执行终态 `addc32 exit0`（初始79c310／session41815），没有外部重试、修复重跑、延期、force、回滚或删除。

## 目标、动机与实际功能

整体目标是由 HF 独立读取 LF 普通几何，在一致任务下计算并交付非线性力学响应，供外部研究层使用。已有三个设计的保存态对照；本轮解决单例准备与已有 batch 求解入口之间缺少来源清单桥接的问题，不重复完整加载路径。

新增并安装两个入口与一份有限测试：`hf_repo/src/hf_eval/lf_native_batch_inputs.py`、`hf_repo/scripts/prepare_native_lf_batch_inputs.py`、`hf_repo/tests/test_lf_native_batch_inputs.py`。原默认文件零修改，原单例转换、task 校验、native batch 元数据门、力核、切线、控制器与科学十五门保持。

来源 schema `hf-native-lf-source-manifest-1.0`，统一任务／右补／options；输出既有 `hf-native-batch-manifest-1.0`，并记录每例来源、geometry/task身份、准备epoch、future output及partial/not_run。路径以显式repo解析，数字案例目录不依赖label。函数顺序准备各例一次，首次准备前核清单与来源pin；失败保实际partial并停止。

API 为 `prepare_native_lf_batch_inputs(source_manifest_path, output_directory, *, repo_root=None)`；CLI 参数为 `--repo --manifest --output`。以后在 HF 专用环境中可从仓库内取得真实根，选择全新输出目录；这只是使用示例，本卡不再执行：

```powershell
$hfBatchRepo = (git rev-parse --show-toplevel)
python "$hfBatchRepo/hf_repo/scripts/prepare_native_lf_batch_inputs.py" --repo "$hfBatchRepo" --manifest "lf_data_preparation/native_interface_001/lf_batch_input_preparation_001/source_manifest.json" --output "local_runs/lf_batch_inputs_new"
```

## 实际结果与效果

| 项目 | fine | wave |
| --- | --- | --- |
| 来源 | 仓库内普通LF v2包 | 仓库内普通LF v2包 |
| 准备状态 | success | success |
| native实体单元数 | 4358 | 4349 |
| native网格 | 80×160，h0.5mm | 80×160，h0.5mm |
| 明确右补 | 4mm／8列 | 4mm／8列 |
| 分析网格 | 80×168，84×40mm | 80×168，84×40mm |
| task原目标数 | 25 | 25 |
| 新力学求解／HP | 0／0 | 0／0 |

两例四场逐格核对：原LF bool→native uint8完全相同（design_domain映射design），derived原160列保持，新增8列仅passive_void=1，其余三场为0。新native及derived geometry_id均与旧声明相同。任务除geometry两个身份外，连同原25目标、材料、固定工件、边界、alpha／gamma及描述文本逐值保持。新descriptor内历史路径与绑定task字节SHA可变化，均绑定本次实际SHA；不要求跨目录raw SHA相等。

六个有限mock测试一次运行、6/6通过（0.681秒）；真实CLI从无关cwd一次运行，两包各准备一次。现有batch `_preflight` 纯元数据核对通过；未来evaluations与evaluation_index目录未创建。完整grid相同是新准备入口的明确合同，原batch能力不改。未读取Downloads ZIP、旧geometry NPZ、科学gzip或旧媒体。

[新来源清单](source_manifest.json) · [准备状态表](run_001/index.json) · [原batch清单](run_001/batch_manifest.json) · [精确检查](run_001/checks.json) · [人工检查页与未变形图](run_001/REVIEW.md) · [测试日志](tests_stdout.log)

## 显示、资源与来源记录

唯一PNG展示实际新derived masks、毫米坐标、端口／支撑／对称声明、y31–40mm固定方体半域及右补区域。箭头只表示声明方向，不是实际力。唯一一次像素检查通过；原图2400×870，工具显示缩至2048×742，无重绘。[像素记录](author/pixel_QA.json)。

helper 12.045562500秒／180秒；outer 14.296650900秒／240秒。树采样峰195538944B／1GiB，helper自身峰82927616B。真正复用冻结SUP2，CPU-CLEAN1同实例终止／成员覆盖／句柄释放合同通过，CPU telemetry关闭；采样不是OS硬限。[outer收据](preparation_launch.json) · [原实例日志](preparation_instances.ndjson) · [helper收据](run_001/execution_receipt.json)。

CLI记录6次NPZ读打开、4次numpy.load；helper记录20次NPZ读打开（含新输出封存／输入SHA读取）、6次numpy.load。文件打开和byte-buffer数组解码分开记录，不能当成26份不同文件。实际21份新产物在原helper窗口封存，原输入和绑定源码保持，三份安装字节等同冻结候选。既有依赖可能导入／注册JAX；0新力学调用的依据是冻结源码与实际准备路径，不冒称全局动态机械hook证明。

[原批准卡](L-BPREP1_CARD.md) · [卡静审](author/CARD_REVIEW.md) · [候选静审](author/SOURCE_REVIEW.md) · [冻结末核](author/FREEZE_REVIEW.md) · [实际结果审阅](author/ACTUAL_REVIEW.md)

## 当前边界及下一步

本次PASS只覆盖输入准备和batch声明兼容。没有重新构模、F／T／HP、平衡求解或真正batch评价；不继承旧机械／独参资格。压力、有效夹持、释放、稳定性、全路径独参、标签、排名、HF5均不升级，整个HF项目尚未完成。下一步依据[功能缺口记录](NEXT_STEPS.md)规划一次有限的真实batch消费，不重开本卡窗口。
