# L-CTIPAREPORT1：保存研究报告读取入口与轻索引

2026-10-21（Asia/Seoul，由实际UTC+09派生）；执行 **PASS**；阶段完成 `True`。新PNG=0，媒体像素QA不适用，未读取pixel_QA或重开旧图。

准备期PLAN、preapproval卡和proposed_plan的pending/false按原字节保留，属于原历史；当前整卡已由用户明确批准，以[当前授权](author/authorization.json)、[批准卡](L-CTIPAREPORT1_CARD.md)和[SOURCE审查](author/SOURCE_REVIEW.md)为准。

整体目标：将LF独立几何与HF非线性/TMC评估结果提供给外部研究层使用。本轮把现成全周期、参数比较与峰节点数据集中到一个可导入函数/CLI，补齐结果使用功能，不重建力学摘要或比较算法。

实现入口为研究层saved_study_report.py的load_saved_study_report(cycle_report_file, peak_node_report_file, *, repo_root, bindings, assets)，同文件提供CLI。返回四键cycles/scalar_comparison/peak_node_comparison/report；前三者保持同次解析原对象/引用，CLI只写轻report和人工总览，不重复260/3390大表。默认native_response既有单result功能保持，不导入HF、NumPy、Matplotlib或力学实现。

实际读取/使用记录：function_calls `1`，普通业务JSON `2`，固定旧图页stat `12`；返回键 `['cycles', 'scalar_comparison', 'peak_node_comparison', 'report']`，原cycle引用 `{'cycles_baseline_is_original': True, 'cycles_new_is_original': True}`。两输入总计3219013 B；控制/源码读取另列，不再开原cycle/node/task/convergence/HP/history文件。

原标量报告计数 `{'sources': 2, 'baseline_original_targets': 20, 'new_original_targets': 20, 'raw_values': 40, 'matched_pairs': 20, 'metric_fields': 13, 'descriptive_differences': 260}`；原节点报告计数 `{'sources': 2, 'node_raw_rows': 1130, 'matched_node_pairs': 565, 'descriptive_node_differences': 3390, 'mask_group_original_rows': 8, 'mask_group_matched_pairs': 4, 'mask_group_component_differences': 24, 'whole_resultant_component_differences': 6}`。原20目标/两alpha40原值、260标量差与565对/3390节点差以及原4组/24差、整体6差仍由API原对象访问；本轮不重算差、fsum、极值或力矩，不筛节点、重排或归一化。

两alpha原峰关联如下；同source的37项原观察对应仅为已有报告身份核对，不新增科学/HP验收。旧accepted1、新accepted12与global12分别保留：

|source|alpha|原accepted|原global|原leg|d mm|原SHA|
|---|---|---:|---:|---|---:|---|
|baseline|5e-07|1|12|loading|1.06|`dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6`|
|new|2.5e-07|12|12|loading|1.06|`e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`|

不只按d或SHA合并角色：同d的加载/卸载不混配，origin不伪称loading，初始同SHA不跨alpha去重或迁移参考。嵌入cycle路径/SHA只是原来源声明，本轮未重读原cycle；旧14段/33raw与新4段/23raw历史分别保存，不当作纯alpha性能。

轻report保输入identity、原counts/任务/资格、峰关联、对象访问位置与12固定入口。缺资格字段保持缺失，不自动补值或把选定态参考升为全路径验证。原节点弱力不是面牵引、压力或有效夹持；到零仅为已有输入回程完成。

本卡已把独立HF既有结果交给一个可导入函数/CLI：两α周期、标量差与峰节点弱力均可访问，读取功能缺口已补齐。接下来影响物理使用的是报告量的定义及资格边界，而非再套一层摘要。现有全局Fy是固定下半工件上的有符号弱作用量，total包含material与Hu；这些分量各自变化，不能只看total接近就称α独立。它尚不是面压力，也不能仅由固定工件作用力证明能承受外载或释放。

|原结果角色|类型|原页/图|stat bytes|身份范围|
|---|---|---|---:|---|
|baseline_cycle|manual|[已有入口](../lf_circle_tip_path_001/run_001/REVIEW.md)|34424|stat_only_bytes|
|baseline_cycle|PNG|[已有入口](../lf_circle_tip_path_001/run_001/response.png)|286982|stat_only_bytes|
|baseline_cycle|PNG|[已有入口](../lf_circle_tip_path_001/run_001/quality.png)|310485|stat_only_bytes|
|new_cycle|manual|[已有入口](../lf_circle_tip_alpha_path_001/run_001/REVIEW.md)|22763|stat_only_bytes|
|new_cycle|PNG|[已有入口](../lf_circle_tip_alpha_path_001/run_001/response.png)|286124|stat_only_bytes|
|new_cycle|PNG|[已有入口](../lf_circle_tip_alpha_path_001/run_001/quality.png)|312590|stat_only_bytes|
|scalar_comparison|manual|[已有入口](../lf_circle_tip_alpha_comparison_001/run_001/REVIEW.md)|36867|stat_only_bytes|
|scalar_comparison|PNG|[已有入口](../lf_circle_tip_alpha_comparison_001/run_001/response.png)|319897|stat_only_bytes|
|scalar_comparison|PNG|[已有入口](../lf_circle_tip_alpha_comparison_001/run_001/quality.png)|424862|stat_only_bytes|
|peak_node_comparison|manual|[已有入口](../lf_circle_tip_alpha_force_001/run_001/REVIEW.md)|10410|stat_only_bytes|
|peak_node_comparison|PNG|[已有入口](../lf_circle_tip_alpha_force_001/run_001/force_vectors.png)|313737|stat_only_bytes|
|peak_node_comparison|PNG|[已有入口](../lf_circle_tip_alpha_force_001/run_001/force_components.png)|309498|stat_only_bytes|

上述只链接4原人工页/8PNG，未读正文、PNG/GIF字节或内容SHA，不复制、解码、拼图或新渲染。原人工页已有变形/力图入口；密集小箭头、约8–10微米距离、全量程重合线等原可见性限制保持，不另作旧图QA。

资源配置 `{'helper_seconds': 180, 'outer_seconds': 240, 'sampled_RSS_bytes': 1073741824, 'cpu_thread_limit': 16, 'cpu_thread_environment': {'OMP_NUM_THREADS': '16', 'OPENBLAS_NUM_THREADS': '16', 'MKL_NUM_THREADS': '16', 'NUMEXPR_NUM_THREADS': '16'}}`；helper实际 `0.3286781999922823` s，outer `1.879633600008674` s；峰值采样RSS `69120000` B，清理 `True`。四库16线程仅为配置；本轮纯标准库，无GPU/机械计算或新测试/默认安装。

新封存 `2` 份普通输出／`27465` B。闭卡继承helper seals并核新输出stat，不再调用读取API或重读两原comparison。helper错误 `未提供`，outer错误 `未提供`；真实partial与实际状态保持，首错停，无外部重试、修复重跑、延期、force、回滚或删除。

入口：[人工总览与实际使用说明](run_001/REVIEW.md) · [轻report](run_001/report.json) · [可导入模块/CLI](saved_study_report.py) · [outer](step_launch.json) · [helper](run_001/execution_receipt.json) · [当前授权](author/authorization.json) · [SOURCE审查](author/SOURCE_REVIEW.md) · [实际审查](author/ACTUAL_REVIEW.md) · [闭卡JSON](author/closure.json) · [后续](NEXT_STEPS.md)

后续：先明确“下半固定工件单侧有符号作用力”的操作定义、原积分厚度/单位、镜像与material/Hu含义，并在现有研究层入口给出直接字段用法；不新增reader层，不自动求解或HP。

交接：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，main继续开发。函数用显式repo_root解析相对路径；异目录恢复采用同机local-Git fetch/ff-only并单独核远端main，不称异机科学复算。不要重跑已关闭launcher。
