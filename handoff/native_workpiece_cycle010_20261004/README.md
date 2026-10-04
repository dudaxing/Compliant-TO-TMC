# Cycle010 开发与异目录接续材料

从[主报告](../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/RESULTS.md)开始，它记录整体目标、此步选择依据、实际12态、原失败、修订内容、代码入口、物理效果、资源与下一步。当前入口为[CURRENT_STATUS](../../docs/CURRENT_STATUS.md)，完整旧记录原字节保留；整体项目尚未完成。

本次源码与数值位于主干中的以下目录：

- `lf_data_preparation/native_workpiece_001/coarse_square_cycle_010`：独立一次生产成功；原参考在HP之前首错关闭；捕获T44/F77和拒绝trial。
- `lf_data_preparation/native_workpiece_001/coarse_square_cycle010_ref_002`：计数合同及12项元数据测试；参考达到16HP/7完整状态后超时关闭。
- `lf_data_preparation/native_workpiece_001/coarse_square_cycle010_ref_003`：新600/660秒独立参考，对全部12态重新完成24HP，不拼接旧前缀。
- `functional_views/native_workpiece_cycle010_20261004`：12次保存几何、12次全节点力观察与实际变形/力/字段图，观察和绘图无新力学或HP。

`authoring/`按四个原作者目录保存候选、原先有误的预备版本、最小迁移、静审和实际只读复核；`authoring_copies.json`给出83件逐字节复制的身份。它们是开发过程来源。正式运行绑定以各自protocol/source_freeze/input_inventory和实际launch为准，晚到审阅不冒充早先运行已冻结的材料。后续交付审查放在本目录，不追写已冻结科学目录。

`document_preservation.json`证明七个当前入口的旧07134ea6正文逐字节保留，只加最新前缀。后续`public_restore_science_receipt.json`记录公开科学提交的异目录文件核对；最终交付提交及核对回执保存在该次仓库外作者目录，避免把清单自身循环纳入哈希。

另一台机器克隆main到任意目录后，在真实Git根读取报告，并用已有Python执行`python -B tools/handoff.py verify --output <新的仓库外JSON>`。当前manifest覆盖本轮受管源码、任务、保存态、参考、失败、图和审阅资料；历史外部大资产按`handoff/evidence_assets.json`恢复。文件验证不运行HF/HP，也不代表完整历史资产恢复或异机数值再验收。

旧作者生成器和实际argv带有来源机的绝对路径，用于追溯，不能在另一目录原样重跑关闭卡。功能入口在`hf_repo/src/hf_eval/`和`hf_repo/scripts/`；新的任务须另建未存在的运行目录、明确任务/源码/资源/门，再按本报告的下一步继续。main与origin保持`https://github.com/dudaxing/Compliant-TO-TMC.git`。
