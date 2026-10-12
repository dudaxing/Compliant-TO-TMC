# M-ALINK1 实际结果：两态参考与变形图关联通过

2026-10-12（Asia/Seoul），直接批准后唯一启动已终端 exit0／PASS，窗口关闭。新增响应、轻索引和执行回执均已保存。现有默认 reader、原力核、切线、数学门及物理定义没有修改。

## 目标、完成内容与效果

整体目标仍为独立 HF 有限变形／TMC 前向评价：读取普通 LF 几何，在明确任务下提供实际变形、反力和可解释工件作用，供外部研究层比较。HF 不优化、不调用 dmftd，MPM 暂不实现；main、既定 origin 与 science0.5.0 保持。

M-INTEGRATE1 已安装保存态续算入口；M-RESUME1 得到 alpha=5e−7 的原峰值1.20与首次回撤1.15 mm两态；M-AREF1 为同两态完成4次 HP80／120独立参考与原十五门核对。本次只补数据入口，使调用方通过一份新的 linked_response 与轻索引同时找到两态物理响应、已有参考及原3PNG／两帧GIF。原 producer response、参考、视图与图件保持原字节。

摘要开始／完成各1，响应写入1、索引写入1；两态 reference 与 views 均 matched。API实际读取5份普通JSON、核12份声明参考Python来源和原4份媒体字节，HF导入仅包与native_response。30份原绑定在唯一运行前后保持。没有新 NPZ／NPY、科学 gzip／CSV 读取、构模、F／T、HP、平衡求解、测试或绘图；零新力学依据冻结调用路径及纯摘要模块闭包，不是全库动态力学钩子监控。

## 实际资源与可审查响应

| 记录 | 实际值 |
| --- | ---: |
| helper记录耗时 | 0.8400699000048917 s |
| child完整终端wall | 1.0407080000150017 s |
| outer含前后核对 | 1.448175400000764 s |
| helper采样峰值RSS | 23388160 B |
| outer采样进程树峰值RSS | 41127936 B |

满足helper180／outer240秒、采样8GiB；RSS为采样，不是OS硬上限。首错停止规则未触发，没有重试、修复重跑、延期或force。

下表复用原真实保存数值，本次未生成新物理响应：

| 状态 | child／原目标 | 输入R (N) | q_out (mm) | 下半工件有符号total Fy (N) |
| --- | --- | ---: | ---: | ---: |
| 1.20 mm峰值锚点 | 0／13 | 0.37865427196005513 | 1.016934534302024 | 0.12492121630032427 |
| 1.15 mm首次回撤 | 1／14 | 0.3470376815403639 | 1.0153174242325562 | 0.10671287553103108 |

R是半模型输入反力；工件Fy是下半固定刚体弱式作用合力，包含材料与Hu贡献，尚不等于有效夹持力。q_out是加权端口位移，不是表面间隙。两个端点不构成完整卸载曲线。new linked_response.call_counts与timing_seconds仍描述原生产求解，不能把它们当本次调用；本次次数和资源以本目录执行回执／launcher为准。原evaluate专属invocation、evaluation_elapsed_seconds、evaluation_elapsed_scope不由纯summary复制，仍保存在未改原response并被轻索引链接；共有公有摘要字段只有reference／views按本卡关联，其余保持一致。

## 保留的范围与未实现功能

accepted_reference_pass=true、full_path_reference_pass=true只覆盖已完成的两态child短段；reference_scope为Child accepted suffix only。full_original_path_reference_pass与path.full_original_path_completed均false，target_response为null。父M-ALPHA1仍failed／time_limit、14加载态、NOT_PASS，不把父子拼为一次原15目标完整求解通过，也不转移两态参考到父前缀。原producer三资格flags均false。

旧view.reference_available=false保留绘制时历史事实，图件未显示新HP误差场。原连续材料＋Hu表面总压力、有效夹持定义及资格、完整原路径参考、稳定性、全部切线列、一般LF输入／更多工件与运动摩擦任务、HF5仍未完成。

## 原实际效果与可恢复入口

![原峰值与首次回撤实际变形](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

原图件：[结构与力](../saved_continuation_001/run_001/view/comparison.png) · [距离与有符号力](../saved_continuation_001/run_001/view/distances_forces.png) · [峰值场](../saved_continuation_001/run_001/view/peak_fields.png)。本轮没有重新读取像素或绘图。

[新关联响应](run_001/linked_response.json) · [轻索引](run_001/light_index.json) · [helper回执](run_001/execution_receipt.json) · [outer终端](link_launch.json) · [终端／范围独立核对](author/execution_terminal_scope_review.md) · [输入／输出独立核对](author/execution_input_identity_review.md) · [下一步取舍](NEXT_STEP_REVIEW.md)

新索引的artifact路径相对仓库根，支持不同目录恢复；继承continuation中的原绝对路径作为历史记录不改写，可用索引中的parent_result等相对入口定位。不可变protocol／card仍保留prepared=true、authorized=false、executed=false的准备事实；本次实际直接批准与运行分别在author/authorization、direct_human_reply及run／launch中记录。
