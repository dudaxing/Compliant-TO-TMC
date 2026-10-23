# 高输入力控准备的恢复边界

本目录是准备材料，尚无新高输入force结果或科学包。首先阅读[准备说明](PREPARATION.md)、[候选卡](L-CTIPFHIGH1_CARD.md)、[来源绑定](SOURCE_BINDING.json)、[比较门](COMPARISON_GATES.json)及[人工页](inspection.html)。

本机拟用原`D:/hpr1_001/parent_001`最小父树：原完整13目标result及model/source_geometry描述／缓存、仅selected accepted012状态；probe参考用`D:/hpr1_001/run_001/science`普通result和accepted000／002 split。旧父整个13态的科学档不需要，也不声称该最小树拥有它们。P1参考选accepted002，不是中间accepted001。

已有PROBE1[原封证据包](../lf_circle_tip_probe_001/execution_evidence.zip)及[原成员清单](../lf_circle_tip_probe_001/EVIDENCE_MANIFEST.json)包含其当时最小父源和新probe科学档；本次没有解压、复制或核它们的payload。普通旧probe完整result仍链接既有[原件](../lf_circle_tip_probe_001/run_001/science/result.json)，本次不另复制大文件；source_context仅保存必要普通描述与旧失败摘录，未改原文件内容或旧状态。

SHA与stat分别标注：本轮对普通JSON／源码实际核字节，NPZ／字段／旧ZIP身份均只从原普通记录引用并stat。准备PASS不等于旧科学payload、四mask、selected split或P0 fresh已经重新验证。以后执行必须通过原准入；旧controller源码差异保留，两kernel硬门与fresh首检不变。

其他机器若需恢复科学包／迁移路径，应在新准备／执行范围显式列出解压／复制／读计数和资源，核原包身份后保内部相对树；当前候选卡只覆盖本机已存在树，不暗含这些额外读取。封存记录中的绝对D路径是历史身份，不应改写旧档以掩盖路径迁移。

当前生产入口`hf_repo/src/hf_eval/native_guided_force.py`，原固定／probe入口保持，当前57份.py身份见author/PRODUCTION_IDENTITY.json；main基线293c542557c0abe59e1321713e9c3e251eeca465。origin固定`https://github.com/dudaxing/Compliant-TO-TMC.git`，后续开发在main。未来卡获批后冻结的是当时发布的main，而非强制回退本基线。

本轮发布恢复核对只验证同机`D:/hf-restore-20260930`与main的变化文件字节／索引／清单，不是异机数值复算或环境证明。控制图是新绘的纯示意，不是新结果；旧动画／PNG不重开，未来科学路径／显示须另行批准。
