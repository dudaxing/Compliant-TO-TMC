# M-ALINK1：现有摘要 API 的范围与 flags 静审

状态：只读源码／普通 JSON 审阅完成；未批准、未执行本卡，未调用 API。基线 main `84c67e48ba61548a1c15d2c049870678ef58f573`。未读取 NPZ、HP 压缩档案或任何图像字节；未进行新数值运算、测试、观察器调用和绘图。

## 最小功能与身份

现有 `hf_repo/src/hf_eval/native_response.py` 已能把同一续算的 result、相邻 model JSON、新两态独立参考和原视图 manifest 关联到一个新摘要，无需修改 reader。普通文件身份核对一致：child 本地索引 0／1 对应原目标 13／14、1.20／1.15 mm，state SHA 与新参考和原视图 summary 完全对应；新参考的 12 份 `.py` 来源 SHA 当前均匹配。此检查没有重审数组或 HP 结果档案，也没有生成 linked response。

`_reference`（77–118 行）读取摘要、2N HP 记录和来源字节身份，保留两态参考的原资格范围。其 `full_path_reference_pass` 使用 child 的 `completed`，所以未来匹配成功时该字段可为 True。这里的完整路径仅是两态请求后缀。229–235 行已有 continuation 后处理：`path.full_original_path_completed=False`、`independent_reference.full_original_path_reference_pass=False`，并标注 `Child accepted suffix only`。候选应复用这段行为，在索引和结果说明中解释其范围。

## 关联后预期字段（尚未执行）

| 字段 | 预期／含义 |
|---|---|
| `status`、`path.completed` | success／True，child 的两态后缀完成 |
| `path.task_target_executed`、`path.full_original_path_completed` | False／False |
| `target_response` | None；不能把运输来的原峰值当成本次完整任务目标执行 |
| `requested_endpoint_response`、`last_accepted` | child1／原14，unloading，1.15 mm |
| `maximum_loading_stroke` | child0／原13，resume_origin，1.20 mm；此处没有重新加载 |
| `accepted_reference_pass`、`full_path_reference_pass` | 若现有 API 的全部匹配条件通过则 True，范围均仅两态 child |
| `full_original_path_reference_pass` | False |
| 全列切线／contact／clamp／pressure／HF5 | False，不由关联升级 |
| `views.status` | 仅未来原图像字节 SHA 核对通过后可为 matched |

parent 仍是 failed／time_limit，原十五目标路径仍未完成；continuation 字典应原样复制。child 的 producer `independent_HP_qualified`／`equilibrium_qualified`／`HF_qualified` 均为 False，保留为生产时记录，与新关联参考分层报告。原 viewer 的 `reference_available=False` 同样是绘图时的历史记录，`_views` 不要求将其改为 True。新独立参考的通过资格不转给父十四态或全部原十五目标路径。

摘要会复制原 `call_counts`（F17 开始／16 完成，T9／9）和原 `timing_seconds`。它们属于之前 M-RESUME1 生产求解；新关联应另外记录一次 API 调用及自身资源窗口，不能把这些原数值称作本卡发生的科学调用。

## 实际读取范围和物理限制

`_views` 的 153–160 行会读取并核对原 3 PNG＋1 GIF 的文件字节 SHA，而不解码像素、运行 observer 或重绘。因此未来卡应准确写为“普通 JSON／源码与原图像字节身份关联”，而非字面上的“只读 JSON”。本次静审没有读取这些图像字节。API 不读取原 states/nodes CSV 或逐态 derived／geometry／nodal JSON；轻索引若需链接原两表，须明确为既存文件链接，而非新增观察。

R 是半模型输入反力；工件力为原有带符号弱式作用，保持反力、镜像上半作用、整物体净力与两侧法向幅值和应分清。q_out 是加权端口位移，不能当表面间隙；结果中的 node-window clearance 是原栅格窗口指标，原 viewer 的有限面 unsigned 距离是另一种几何观察。摘要的全域 J／Hu 标量不替代 viewer 的分区域场。关联不能使压力、有效夹持、网格或参数稳定性获得资格。

## 最小候选及资源

建议只调用现有公共摘要一次，写入新阶段的 linked_response／轻索引／收据；原 result、model、response、新参考与原 viewer 字节不改。保留严格来源 mismatch 规则，不修改原 reader。旧 M-LINK1 的第四张网格对比图与四表范围不应自动带入本次两态功能。

旧 M-LINK1 一次真实关联的 helper 记录为 0.2004933999851346 s／26537984 B，outer 为 0.3920396000612527 s／30978048 B（exit0、1 次）。helper 时间快照早于收据写完；它们仅说明普通关联已有短程执行先例，不是本候选实测或资源保证。

拟 helper180／outer240 s、采样8 GiB 是新的关联范围和窗口，不能续用已关闭 M-AREF1 的余时。最终候选、卡和 protocol 尚需联合静审、发布／恢复核对和直接人类批准；当前没有关联执行 PASS 或数值授权。

SHA、普通身份检查和逐项预期见同目录 `source_scope_and_flags_review.json`。
