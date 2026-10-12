# MEXTEND1 外部源候选说明 v2

本候选未安装／授权／执行；没有HF或候选import、API、NumPy计算、pytest collect/run、NPZ/gzip/CSV/media读取或图。baseline main c4d81620。6份既有生产文件外部修改＋1份新测试，实际old/newSHA／行数／AST及11精确selector见candidate_author_receipt.json。没有launcher/protocol，正式runtime与冻结证据不改。

## 入口与两模式

solve_native_mean/evaluate_native新增opt-in extend_path=False；两CLI有--extend-path。False保持原same-task/fullparent/interior/suffix所有门，False时不转发新kwargs，以维持旧CLI/mock默认合同。True须显式新task与saved result/index，零起点／缺task／非bool为typed invalid_input；CLI解释为显式task选择。

新task只有path.targets改变：完整旧targets作为canonical前缀＋严格非空append，其余完整task（包括task_id/description）canonical身份相同；生产直接复用hf_eval.data.canonical_hash。旧task_SHA与新的extended_task_SHA独立记录，不修改旧task或以新SHA冒充旧SHA。root拟实际task来自proposed_task.json，正确source-only canonical receipt为v2（new94671c…，old a343fbb…）；候选不使用早期draft错误身份，也未调用HF算法来准备文件。

源必须status success/path_completed/target_reached，选中末accepted为旧完整task末原目标且非零。若parent.targets仅本地suffix，逐项核continuation完整task/requested suffix／原globalindices、source anchor SHA／signedR、local/global映射与所有原目标覆盖。默认strict gate没有被删或放宽；append不能通过修改一条terminal检查实现。

## 原状态与新身份

共用原reader：source/model/selected descriptor、geometry/material/DOF/port/boundary、两个force/tangent source及settings（新clock除外）保持。在扩展专属_extension_targets中先核旧region_metadata.effective_boundary.task_sha256等于旧model.task_sha256，之后才将expected region的新task stamp改为project实际hash；其它regions必须相等。默认False分支没有新增stamp门。原state descriptor、NPZ lift/fluctuation2fields的dtype/shape/bytes/statehash／zeroLift／fixedSplit完整块原文保持；不读旧force/tangent/matrix。warm state/R/p原样，KNone/freshF/T依原controller，未改数学、组装或导数。

extension metadata：continuation_mode、source/extended任务hash和完整targets、appendedtargets、全parent_continuation、selected accepted/global index。parent_status/failure保持立即来源；当前来源是成功child，祖先MALPHA failed/time_limit保存在parent_continuation。original/new full path并未从零由本段执行，资格False；新段maximum_loading_stroke只是1.15锚点，response scope明示不是原1.20峰值。原公共_reference/_views/_state/writer的门与body不变，只有扩展scope文字／false flags分支新增。

## 有限测试源码（未运行）

11实例：1个真实16单元50DOF整合，构造after-peak failed父、strict成功child、证明默认strict拒绝新task，再显式extend；5 ordinary metadata拒绝（physics/nonprefix/nonterminal/childmapping/task_stamp）、3 typed API input mocks、2CLI mocks。真实测试的4次tiny建模包含一次严格新task拒绝构建，不是4个大模型，也没有新原夹持器／HP；实际F/T/时间未知，须由未来已批准执行记录给出。

真实测试监测第一次fresh力／切线和源state两字段唯一decode，原lift/fluctuation与signedR字节保持。生产入口期间拒绝旧forces/tangents/matrix原bytes／decode；fixture前后raw bytes snapshots仅用于tiny保存包保持，不是production reader。geometry authority NPZ经现有builder可通过BytesIO装载，测试只拦具体旧缓存路径，允许原geometry加载。缓存save零额外F/T由现有实现及保存计数检查。

11精确selectors只由源码参数字面值整理，未collect。future旧25有限兼容集应复用，不称为已通过。候选6生产文件若将来默认安装，必须另行审批／来源迁移与旧证据上下文核对；当前仅外部overlay，没有改变任何既有source pin。

source receipt SHA256：`2a274b5123c250c0c3e9cecd2f89fc9a759479bb080b1e8a021dd1518bcab843`。

## v1→v2来源修正及viewer核查

v1原作者receipt／notes已分别以candidate_author_receipt_v1.json／SOURCE_AUTHOR_NOTES_v1.md逐字节保留。v2只改native_resume._extension_targets的旧task stamp一致性与test metadata helper／task_stamp负例；实际旧source task两stamp相同，修正是准备期来源完整性完善，不是已执行数值修复或重试。原生产残差／约束／平衡／Armijo／bisect门及force/tangent/controller均不变。新11实例＋原25有限兼容实例为未来36目标；全部未collect／run／安装。

原viewer无result.scope／continuation名称白名单，可沿原descriptor／model／accepted合同处理扩展段，不改viewer或改名绕过验收。固定square、(80,30)参考节点、原纯来源与逐态缓存门保留。其PEAK accepted是本段最大d，拟段1.15→1.10只代表1.15段锚点，不能称祖先1.20峰值；production_path_completed是child段，完整原／新task资格另保持false。可选HP reference仍须本次result全态身份，旧两态ref不可移用。详情见VIEWER_SCOPE_COMPATIBILITY_REVIEW.md／viewer_scope_compatibility_review.json（静读，不等于未来view PASS）。
