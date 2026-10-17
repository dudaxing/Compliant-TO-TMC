# 首次卸载：最小公共合同的只读方案

基线 `c78658322587499e901e654516aed62b45aa022d`。本子任务只读现有Python源和少量测试源，写外部说明。尚未取得本阶段实现、安装、测试或真实夹持器卸载授权；没有导入HF、运行测试、读取科学/CSV/媒体、修改正式文件或制作候选实现。源SHA、精确行号和读取范围见同目录 `READONLY_DESIGN.json`。

## 结论

现有 `extend_path=True` 加显式新任务已经足够明确，不需要新增布尔参数、API、CLI选项或第三种path kind。建议唯一功能源码修改为 `hf_repo/src/hf_eval/native_resume.py`：在现有来源为load_only的分支内，加入严格限定的 `load_only → ordered_cycle` 首次下降合同。控制器、力核、切线、组装、原门、任务构模、响应数值和两CLI均可保持原字节。

## 现有事实

| 源与行号 | 当前行为及意义 |
|---|---|
| native_resume.py:46、58—76 | `_extension_targets`要求load_only来源的新任务仍为load_only且严格递增；因此当前转换明确抛`invalid_task_extension`。原前缀和归一后的完整任务按canonical hash比较。 |
| native_resume.py:77—112 | 共用的成功终末原目标、来源任务签名、原子段完整覆盖、parent anchor及global/local映射检查已经存在，可直接复用。不能添加`parent.task_target_executed=True`要求，因为现有成功加载子段该字段为False。 |
| native_resume.py:162—175 | `saved_load_only`只依赖extend_path和父/result/model的旧load_only类型，不要求新project也是load_only；转换通过扩展验证后，已有reader入口可以运输原态。 |
| native_resume.py:182—220 | 已核geometry/material/region/counts/settings/options、力/切线源码及保存split/hash/fixed条件；只读lift和fluctuation，不读旧力/切线/矩阵。有效边界task hash的合法更新已有处理。 |
| native_project.py:73—84 | 仅支持load_only和ordered_cycle；ordered_cycle已允许完整加载前缀后下降，要求非负、无相邻重复、max等于input峰值。没有`load_unload` kind。 |
| native_mean.py:249—254 | 新任务的ordered_cycle模式可直接获得原保存state、R和绝对parameter；load_only-only布尔许可不会传给ordered_cycle。 |
| split_displacement.py:99—114、275、358 | 已支持非零ordered_cycle warm start，首次fresh F/T不平衡则停止且不校正原锚；首态leg为resume_origin，下降态为unloading。 |
| native_evaluate.py:52—66、103—107 | 既有extend_path显式要求新任务和保存源，并转发到同一defaults/reader/solver；无需改签名或另设入口。 |
| scripts/evaluate_native.py:17、33；scripts/solve_native_mean.py:22、38—44、62 | 两CLI已有`--extend-path`、显式`--task`及完整转发链；无需新增参数或改变缺省行为。 |

## 建议限定的转换

设成功父load_only任务的完整路径为T，末态/原峰值为P，选中行为最后一个接受的原目标。显式新任务只能：

1. 保留T的完整canonical前缀，path.kind改为ordered_cycle，**只追加一个**有限、非布尔、非负且严格小于P的下降值q。
2. `input.target_mm`继续等于P。不能按load_only追加加载的规则更新成q，不能改变原峰值。
3. 四个说明字段task_id/purpose/parameter_origin/description沿原load_only来源许可，可明确更新。其余geometry、材料、工件、端口、约束、输出弹簧和任务字段精确保持。
4. 做完整任务canonical比较时，仅恢复旧kind和旧targets，并按既有四说明字段规则归一；不得泛化为忽略整个path、input或任意新字段。
5. 共用原来源/终末态/子段映射/settings/力核等检查，不复制一套reader或控制器。默认`extend_path=False`和既有同kind扩展规则保持。

q可以等于旧加载前缀中出现过的更小位移值；这是卸载回到相同位移的正常路径。不能增加“全序列数值唯一”要求。原ordered_cycle仅禁止相邻重复，已满足本合同。

既有三种关系的职责保持明确：load_only→load_only仍是原追加加载/新峰值；ordered_cycle→ordered_cycle仍按旧规则只追加targets；只有load_only→ordered_cycle进入新单下降分支。反向转换及其他kind继续拒绝。

## 来源、完成状态与公共摘要

保留 `continuation_mode='explicit_task_extension'`，让现有响应继续执行完整路径资格为False的处理。建议在同一续算元数据中新增小型 `task_transition` 子字段，明确旧kind、新kind及保留的峰值P；来源任务SHA、完整旧/新targets、appended targets、parent_continuation、global/local索引和锚点证明沿现有字段保存，不另造主mode。

新结果的path_kind为ordered_cycle。`path_completed`、`continuation.segment_completed`和既有`unload_endpoint_reached`描述本次下降子段；`task_target_executed`、`full_original_path_completed`、`full_extended_path_completed`继续为False。`loading_peak_reached`可因为原峰值锚在本段重新复核而为True，不能表述成重新执行了加载前缀。

native_mean.py:307只为load_only显式扩展写`new_peak_reached`和`extended_segment_completed`。首次卸载不应为了迁就旧阶段wrapper而要求这些字段；使用原本通用的`continuation.segment_completed`即可。没有新加载峰值，不需要扩大native_mean实现。

native_response.py:218—224已会将resume_origin纳入segment maximum，给出下降端点，并因task_target_executed=False保持target_response=None；:258—268原样转发continuation并保留full flags为False。首次卸载时segment maximum恰为父峰值锚。已有scope句“Segment maximum; not the source task loading peak”应按原范围文本理解，**不是数值不等断言**。按root取舍保持该文件字节，在task_transition和阶段记录中明确“峰值位于锚点，但未重新执行原加载”，不扩大响应源码范围。

## 文件变更范围

| 文件 | 本阶段职责 |
|---|---|
| native_resume.py | **唯一必改功能源**：限定转换验证、任务归一及task_transition来源记录；保持其余共用检查与原错误类型。 |
| native_mean.py / split_displacement.py | 保持原算术、路由、fresh-anchor与回退；不增加卸载算法。 |
| native_project.py | 保持已有合法ordered_cycle schema及峰值校验。 |
| native_evaluate.py / 两CLI | 保持现有extend_path签名与转发，不增加新选项。 |
| native_response.py | 保持数值、mode分支和原scope文本；解释性澄清放本阶段记录。 |
| 新有限测试与阶段说明 | 获批后另编写，只证明新转换和旧合同兼容；不新增证据框架或大模型重复。 |
| 后续真实卸载wrapper | 另卡适配其新ordered_cycle/endpoints/完成标志与实际N；不能沿用加载wrapper的load_only和new_peak断言。此只读任务不实现它。 |

后续ordered_cycle继续卸载可复用已有同kind扩展；注意该旧分支只允许追加targets，**不允许继续修改四说明字段**。本次不应顺手放宽其规则。

## 有限验证和安装建议，尚未执行

复用现有16单元/50DOF小模型及少量现有保存态/扩展测试做法。关键正例是一条短链：零起点load_only成功→显式转换并单次下降→按旧ordered_cycle扩展再次下降；核新task保前缀/峰值、fresh anchor原SHA/R、global/local映射、原settings/options、父包不变和子段资格。必要反例聚焦改峰值/物理/前缀、非下降或多个追加值、错误来源/未平衡锚，以及未显式extend。不要重做夹持器路径或增加HP来证明接口。

若后续获批，先在外部写单文件候选并完成静审，再由一次受控helper安装一份native_resume.py，运行唯一有限小模型兼容集合。首错保实际安装字节和部分结果，不自动回滚或修复重跑。真实夹持器的首次卸载另按后续授权执行；这里不选择下降目标或资源窗口，也不授真实卸载权限。
