# 工件右移／放大阶段：源码与审阅背景

本目录归档2026-10-07阶段选定的75份原始文本，611466字节，用于异机接续和代码对照。每份来源、目标、原字节数与SHA256见 [raw_sha_manifest.json](raw_sha_manifest.json)，复制校验见 [PACKAGING_RECEIPT.json](PACKAGING_RECEIPT.json)。归档新增于未绑定路径，没有覆盖正式冻结文件。

## 已完成正式数据与历史作者快照

[新 side18/x71 正式目录](../../../../lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/) 已一次完成24态 `0→1.2→0` mm，F354/330、T176/176、1solve、0HP/JIT。[15项小模型证明](../../../../lf_data_preparation/native_workpiece_001/port_projection_validation_001/) 已完成。正式生产、source70胶囊、模型、全部数组与当前 reference_author/accounting_evidence 保持原处，本目录没有复制整批数据。

归档时新参考已冻结：24实际态、48次新HP80/120、helper1500/outer1560秒、8GiB；首次正式运行正在进行。最终状态以正式 reference 的 summary/lifecycle 与 reference_launch 为准，此处不预告通过。作者记录中的“未冻结”“尚未开始”“pending”和前言token是当时时点快照，原字节保留；正式当前说明由根按最终真实结果更新。

首次入口遗漏 `--protocol`，在 launch_pose.py 读取不存在的默认 protocol.json 时退出，早于回执创建或子进程启动：当时正式阶段0次、HP0。见 [入口错误独审](reviews/reference_operator_entry_static_review.json) 与正式 [operator note](../../../../lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/reference_operator_entry_001.json)。随后显式选择冻结协议的运行才是第一次正式参考，两个事实分别保留。

## 选定材料

| 目录 | 用途与范围 |
| --- | --- |
| [reviews](reviews/) | 分配端口、实现、15测试卡、准备、原参考、计数与最终整合、文档／前言／功能解释、旧失败及入口错误独审；静审不增加数值资格 |
| [production_candidate](production_candidate/) / [projection_candidate](projection_candidate/) | 物理任务与仅改变初猜的作者说明、静态计数、源码差异；实际源码以正式胶囊为准 |
| [validation_author](validation_author/) / [tests_candidate](tests_candidate/) | 验证卡包装与4项新增功能测试的原始作者文本 |
| [original_projection_reference](original_projection_reference/) | 原audit447e8d3、builderca64360，原始baseline、差异与审查；不替代后续计数适配入口 |
| [accounting_candidate](accounting_candidate/) / [current_reference_integration](current_reference_integration/) | 实际恢复的invalid_J线搜索记账最小差异与最终整合作者记录；完整账本与证明在正式目录 |
| [documentation_candidate](documentation_candidate/) | 早期完整成功路径收集器；默认side18失败后未执行，只留历史 |
| [documentation_projection_candidate](documentation_projection_candidate/) | 实际终态JSON-only收集器、说明和底稿；应用时须核对实际参考／视图 |
| [front_documentation_candidate](front_documentation_candidate/) | 四份简短前言及作者清单，含4份原文SHA／字节身份；完整原文在正式文档与Git历史 |
| [functional_interpretation_candidate](functional_interpretation_candidate/) | 生产峰值、共同loading.5、卸载与物理解释快照；参考／新图pending指作者时点 |
| [saved_view_candidate](saved_view_candidate/) | 保存态查看器、局部贴合窗口与最小预算变化的作者说明；实际图另存正式视图目录 |

参考数学B850/aa86/B52及逐实际态HP80/120循环保持。纯保存计数适配单列 `accounting_source_transition`，不改变生产三项源码转换/source70，也不增加拒绝trial、压力／夹持或全切线列资格。旧x72与默认side18失败只作背景，没有拼接旧失败前缀资格。

## 异机接续

以 `main`、正式 CURRENT_STATUS/RESUME_DEVELOPMENT 和最终正式证据作为当前入口。原文件中的D:/C:绝对路径是历史来源字符串，不是运行依赖；此目录的Python、差异、JSON与模板作为审查材料，不自动导入或执行。正式参考入口与证据绑定使用repo相对路径。

`R_input` 是半模型输入反力；下半工件Fy、双侧 `2 abs(Fy)` 与全体净力分别报告。`q_out` 是 `(80,28/29/30)` 加权竖向端口，钳尖有限面间隙另测。共同loading.5只支持该同任务初猜读数一致；旧1.8与新1.2峰值不作因果比值。后续依据实际变形、力、间隙与成本推进接触／压力定义、匹配网格与gamma、圆体／自由工件及HF5/LF-N4接口。压力、摩擦、自由工件及有效夹持仍有独立待实现／验证范围。
