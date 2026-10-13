# M-PREF1：两卸载保存态输入范围审查

源 main `eb92b41fd58547640d2c2a8381f98aa5012154df`。本报告仅普通 JSON／源码／AST／科学文件 stat；未运行候选、HF、HP、模型、求解、测试或绘图，未打开科学数组／header／媒体。准备审阅通过，尚未取得本卡数值授权，也未执行。

选择 `saved_extension_004/run_001/unloaded_alpha_half/result.json` 的 child2/global18/0.90 mm 与 child3/global19/0.80 mm。两态均为 unloading、原目标、非 continuation anchor；原 result 成功保存9态，完整 task25目标及最深 failed/time_limit祖先保持。

| child／global | d mm | 原 signed R N | 原 qout mm | 原 lower-body Fy N | state SHA |
| --- | --- | --- | --- | --- | --- |
| 2/18 | 0.9 | 0.193413365531 | 0.998321785104 | 0.0198430044604 | `fa1cffaa2d9911c01752d702ab7cbc91d048b2c41a2f701d555953f91c7e598f` |
| 3/19 | 0.8 | 0.152543853536 | 0.936858828374 | 0.00234515886586 | `8b834bcae162345adb6036970a91ccbb427455f84a07b2bdb0e111ee05db437a` |

最小科学输入为10份NPZ：共享 model 与 source_geometry；每态各 state／forces／tangents／total_matrix。未来9份解码，geometry仅原字节来源身份；本次所有10份只继承已闭 M-UNLOAD2 `execution_receipt.outputs` 的SHA／size，并与当前manifest逐项匹配、stat检查，不新读取或hash。完整路径、每字段 dtype／shape／SHA及来源JSON成员保存在同目录JSON。

model27字段；每态 state2、forces16、tangents3、CSC数组3，共75个不同声明字段。CSC loader另必读 `format`／`shape` 每矩阵2项；`_is_array`是可选探测，准备阶段不声称确认容器实际成员。现有 aa86逐态重开state/forces，会重复36次字段读取；总13个数组loader调用，111次声明字段读取，加CSC必需成员为115次。全部为源／描述符静态计数，不是已执行计数。

保留 B850 `run_state(18,row2)`、`run_state(19,row3)` 与 aa86 `workpiece_checks` 的原字节、15门、Decimal scatter／原PORT方向和原signed R。raw `accepted_018/019` 不改；top `index`／`child_accepted_index` 保持2/3，另记 `reference_execution_index`18/19。此范围仅两个选点，不能变为9态／25目标完整路径PASS或为兼容reader改为0/1。

与 M-EREF1比较，材料、网格、geometry、非path task字段、非clock settings、options及已安装来源相同；完整task由16前缀变25，生产clock1800→9000。数学不改，但旧load包装必须适配实际N9、无安装、`outputs`为 `{sha256,bytes}`、更深祖先；不能照抄旧N2／安装6项／SHA字符串／固定祖先层检查。原 force／tangent／默认API均不变。

新参考窗口拟900／960秒、采样8GiB；全部4HP80/120、工件核查和一张新参考误差PNG须在这一新窗口内完成。既有两态4HP outer193.35030270001153秒、一态2HP99.37017110001761秒仅是资源依据，不能保证新点耗时，也不能延用旧授权。图只读取本次两份新ordinary摘要，源胶囊平铺11依赖＋driver＋plot，各basename必须唯一。

原参考属于另一个result／状态，不能迁移。新选点参考也不升级full-child/full-original/full-extended、所有切线列、连续压力、接触／有效夹持、释放／稳定性／HF5资格；当前公共reference reader仍要求本result全部9态／18HP，此卡不修改reader或关联API。

既有输入最长路径为 205 字符；新输出最终stage名尚未提供，生成路径长度需在实际协议冻结时核。平铺依赖继续避免嵌套capsule路径。

两次普通预览脚本误取model顶层counts及不存在的reference_source_manifest，已按真实JSON定位修正；没有运行数值候选、更改原验收门或科学重试。

详细实际普通读取SHA、10NPZ继承身份、完整声明与15门：[input_scope_review.json](input_scope_review.json)。
