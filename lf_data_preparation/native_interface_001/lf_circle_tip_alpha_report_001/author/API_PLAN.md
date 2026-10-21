# L-CTIPAREPORT1：最小保存研究报告入口建议

2026-10-21 Asia/Seoul；仅只读准备。没有实现模块、执行候选、调用API、重算差值、绘图、测试或Git。当前无新执行授权，本说明不预写成功结果。

## 真实入口与复用判断

`hf_repo/src/hf_eval/native_response.py:summarize_saved_native_result(result_file, *, repo_root=None, reference_file=None, view_manifest=None)`是单mean result摘要，必读model JSON，不能直接接收两comparison schema。其`_reference`另读参考/源码；`_views`另读view/summary，并用read_bytes逐PNG/GIF哈希，超出本卡范围。

`hf_repo/scripts/summarize_native_mean.py`仅为上述函数CLI。安装命令`hf-eval`来自pyproject的`hf_eval.__main__:main`；后者顶层导入`.evaluation`，只有inspect/evaluate/tmc-cshape。因此不调用/复制该摘要，不修改默认HF入口、包或安装。只参考显式路径、write-once及简短错误消息的习惯。

已核ACOMP/AFORCE现行compare源码：它们会重新作任务差/配对/260或3390减法，AFORCE还作fsum和显示比例；不能作为本卡loader调用。复用其已保存字段与语义，不复用计算执行函数。

## 一个纯stdlib模块：函数与CLI共用

建议研究stage内一个`saved_study_report.py`，提供可导入`load_saved_study_report`及`main(argv=None)`。不import HF、NumPy、Matplotlib或默认生产API；无新通用框架。外部研究层显式导入该模块，CLI用脚本绝对路径与显式`--repo`，不依赖当前目录或硬编码本机盘符。

建议函数合同（非实现）：`load_saved_study_report(cycle_report_file, peak_node_report_file, *, repo_root, bindings, assets)`。文件相对路径以repo_root解析；bindings与assets来自调用者已解析控制协议，不再另开manifest。每输入只一次read_bytes，同一buffer核原bytes/SHA并parse；12个已固定artifact各stat一次。CLI只调用该函数一次，以同一次返回生成轻report.json及REVIEW.md；不再为函数演示额外调用。

返回对象建议四个分区，均为同一次已读对象或其引用：

- `cycles`：baseline/new分别引用ACOMP.sources[source].original完整原周期。
- `scalar_comparison`：完整原ACOMP dict，可访问40原值、20pairs、260差、原任务/诊断/异常/计数及资格。
- `peak_node_comparison`：完整原AFORCE dict，可访问565pairs／3390差、原节点/坐标/mask/边、原group/whole/holding/矩、对账与资格。
- `report`：轻索引，含两输入path/bytes/SHA、原counts/compatibility、原task中的物理定义、两峰精确关联、各分区对象路径、12个既有图页path/bytes、作用力及资格范围。

不deepcopy或改写任何原对象；cycles和scalar_comparison共享同一内存对象。CLI仅serialize report，不serialize整个返回值，也不重复3390或260表。完整周期目标覆盖与选定态独立参考覆盖分开列；成功只表示保存来源关联完成，不表示新的机械或HP通过。

## 固定两报告与关联合同

共同前缀`lf_data_preparation/native_interface_001/`：

1. `lf_circle_tip_alpha_comparison_001/run_001/comparison.json`，schema `lf-circle-tip-cross-alpha-comparison-1.0`、card L-CTIPACOMP1。
2. `lf_circle_tip_alpha_force_001/run_001/comparison.json`，schema `lf-circle-tip-cross-alpha-node-force-1.0`、card L-CTIPAFORCE1。

root已外部固定两输入共3219013B及其schema；本次没有另打开两报告或原cycle/node/history文件。后续仅源schema/card/status/固定形状与来源身份检查，不重核科学门或差值算式。不另读PATH/APATH、原node、task、summary、convergence、HP、source_history或完整Newton文件。

按原角色baseline=alpha5e-7、new=alpha2.5e-7关联。在ACOMP的唯一global12/display_branch loading/d1.06项，经baseline/new_raw_index取原raw_values.row，再与AFORCE.source.state及selected_state对照：alpha、global12、原leg loading、d、完整state SHA及原源身份必须精确相合。旧accepted1、新accepted12分别保留；不能强行统一index、按坐标近似或仅凭d/同零SHA关联。原origin/loading/unloading角色保持。

两峰SHA分别为`dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6`、`e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`。只复制已有counts／用len核schema形状；不重新求和、减法、极值、归一化、筛节点或生成物理指标。身份不合、来源或链接缺失明确报错停止，不降级选别的文件。

## 恰8PNG与4页：只stat/link

均在上述共同前缀及各run_001下：

|目录|两PNG|一页|
|---|---|---|
|lf_circle_tip_path_001|response.png、quality.png|REVIEW.md|
|lf_circle_tip_alpha_path_001|response.png、quality.png|REVIEW.md|
|lf_circle_tip_alpha_comparison_001|response.png、quality.png|REVIEW.md|
|lf_circle_tip_alpha_force_001|force_vectors.png、force_components.png|REVIEW.md|

每个固定path核原bytes并链接，不读取/哈希页面内容或媒体。四页间接提供原14/4段实际变形入口，不另stat GIF；无解码、复制、抽帧、拼接、新PNG或旧图新像素审查。保原可见性限制：节点图是固定下半工件弱力、非完整机构，箭头为力显示比例，密集/极小量以原值为准。

## 实施前边界

当前仅API计划，无实现/执行。后续具体卡须固定两输入、12artifact、源码与协议，再获明确整卡授权后有限静审、唯一运行、实际记录和普通发布。拟沿180/240秒、1GiB、四库16和原SUP2；首终端错停，无外部重试/修复重跑/延期/force。控制协议/源码/资源wrapper读取另列，不冒充业务输入。

保原selected-state/方向参考，不迁移为全周期；报告不升级压力、有效夹持、自由释放、稳定性、alpha独立、网格/域收敛或HF5资格。旧14/新4段的计数保各自来源，不称纯alpha性能；到零仍只表示输入回程完成。
