# x71 固定方体的独立软化候选

这是未执行作者稿。新控制目录为 `shift_square_soft_001`。固定下半方体仍为中心(71,40) mm、边长16 mm，实际区域[63,79]×[32,40] mm；原1 mm网格、端口、支承、背景约束、全部11目标 `[0,.5,1,1.5,1.75,1.8,1.75,1.5,1,.5,0]` mm保留，从零独立求解。

实体参考 E 从1变为0.5 MPa，gamma与alpha均从1e-6变为2e-6，nu=.3与Lr=80 mm不变。这会降低实体Lamé常数，同时保持第三介质Lamé和全局kr原字节；不能描述为所有材料同步变软。Et参考标度由20变10 N/mm，沿原floor公式推导，不改原容差、算术支持门、Armijo或二分合同。辅助能量仍不计算，不从本任务推导压力、夹持或全切线列资格。

## 执行前提与来源

`build_pose_card.py --mode prepare`只在**pose002生产及其完整独立参考均真实pass**后安装新作者资料并冻结准备卡。preparer再次核同result、所有接受索引的同state身份、fresh80/120共2N、summary/lifecycle/launch/contract/protocol。文件尚不存在或参考未完成时不得制卡。pose002原state不用于初值，不继承它的接受态资格。

库存 `prerequisite_pose_reference` 保存完整ROOT相对文件→SHA映射及task/model/result/summary各明确角色；这些是先决证据输入。运行来源仍为010历史68项、已独立证明的v5切线过渡及两包装，共70唯一basename；不是把pose002参考实现移入生产。原历史胶囊、失败pose001与已关闭卡不改。生产包装 `execute_shift_pose.py` 保持pose002/pose001的96bf字节，所有真实观察/计数与缓存保存不变。

准备新27字段模型：对原010恰10项变化（6overlay与lam/mu/gamma/Et）；对已合格pose002恰4项材料字段变化（lam、mu、gamma、force_scale_per_length）。其余23字段原字节，包含所有坐标、连接、端口、fixed/free、workpiece集合与kr。介质区lam/mu也独立作字节对照。先决模型与新fixture保留各自身份，不能称同一个模型。

## 新资源窗口与保存

纯构造准备一次120/150秒、8GiB；生产一次**1800/1860秒、8GiB**。settings.time_limit_seconds及helper/outer都明确更新。旧pose001峰值约778秒、首次卸载约882秒和额外二分提供强第三介质作用区成本依据；1800包括未知软化响应余量，不能保证收敛，也不是延长旧卡。实际RSS/时间仍为原协作采样合同，首次正式失败关闭，无修复重试或force。

```powershell
$repoRoot = '实际完整Git根'
$caseRoot = Join-Path $repoRoot 'lf_data_preparation/native_workpiece_001/shift_square_soft_001'
python -B '外部作者目录/build_pose_card.py' --repo $repoRoot --mode prepare
python -B "$caseRoot/launch_pose.py" prepare --protocol "$caseRoot/preparation_protocol.json"
python -B "$caseRoot/author/build_pose_card.py" --repo $repoRoot --mode production
python -B "$caseRoot/launch_pose.py" production --protocol "$caseRoot/production_protocol.json"
```

这些是未来root冻结后命令，本作者未运行。准备和生产各自独占新目录；两入口保留run_001与其父control的stop。新完整实际结果产生后，才另冻本材料任务的fresh参考与保存几何/节点力/可视化卡。参考预算与来源不由本卡自动授权；不能合并任何前序prefix来冒充本路径通过。
