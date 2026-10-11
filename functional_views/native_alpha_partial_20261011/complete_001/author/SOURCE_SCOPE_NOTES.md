# M-AVIEW1 显示候选：源码准备说明

本候选只把 M-ALPHA1 已接受的 14 个原点／加载保存态转为可人工检查的实际变形和工件节点力图，并与原 α=1e-6 的同 14 个原目标作对照。α=5e-7 的原结果仍是 `failed/time_limit`：加载峰值到达，第一次卸载没有接受态，整个路径未完成。显示成功不改变这个事实，也不授予稳定性、压力、有效夹持或 HF-5 资格。

## 源码及复用关系

- 新候选 `saved_alpha_partial_views.py` 是独立 helper，未来置于 `functional_views/native_alpha_partial_20261011/complete_001`。它只通过 `runpy` 调用一次原 `functional_views/right_margin4_20261007/complete_001/saved_right_margin_views.py`，保留原 viewer 字节和纯读取模块合同。
- 原 viewer 支持失败路径的已接受部分；没有 `success` 前提。原 α 对照脚本 `lf_data_preparation/native_interface_001/regularization_sensitivity_001/compare_alpha_views.py` 强制成功 15 态，不能用于本次。新候选只采用其 14 项普通记录匹配与六面板曲线思路。
- 原 viewer 的纯 `hf_eval` 模块为 `__init__`、`native_region_geometry`、`boundary_geometry`、`workpiece_nodal`。原 helper `measure_native_workpiece_regions.py` 及 viewer 合计形成六份源文件的读取闭包；新候选不导入力、切线、模型构造或求解模块。
- 当前 parent main 为 9e2e37c。未来执行必须得到对新准备发布提交的直接人类授权；不能把当前 parent 当作未来授权源提交。

## 未来读取与显示范围

α 候选路径固定为 `lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half`。原 viewer 实际完整解码 29 个 NPZ／279 个字段实例：模型 27，14 个 state 各 2，14 个 forces 各 16。不能把其中的使用子集当成实际解码范围。未来每态各调用一次原几何和工件节点观察器，共 14+14 次；不新增模型、F、T、平衡求解或 HP，不使用原卸载 trial 作为第 15 帧。

原基准只读已有 result JSON、原嵌套周期 viewer summary JSON 与 states CSV，按原目标序号、leg、位移和 state SHA 匹配。原基准的 24 态与参考资格不移植给新 α。新对照 CSV／JSON 保留 14 项原量和 196 个 candidate-minus-baseline 标量差值；这些差值仅在未来明确授权窗口中计算，本次源码准备不生成数值。

未来产物为原三张 PNG、14 帧 GIF、原几何／节点／derived 记录及 9842 个工件节点 CSV 数据行（703×14），再增加一张 α 对照 PNG 和两张 GIF 原像素快照，总计六 PNG／一 GIF。两张快照分别对应 frame 6、原 loading 0.85 mm 和 frame 13、原 loading 1.20 mm；先核原目标／state SHA 身份和成功生成的 GIF 帧数，再复制已解码的原画布像素，保留三分量 glyph、比例与标题，不重新观察或重画该帧。

14 项对照量保留原定义：输入反力、加权输出位移、下半工件 total/material/Hu 有符号 Fy、原两侧法向幅值和、尖端位置、三个有限边界无符号距离、solid 最小 J、free-medium 最小 J 和 free-medium 最大 Hu 绝对分量。原缓存工件字典完整复制保留有符号 Fx/Fy、保持反力、镜像合力／幅值及其各自含义。全域极值、free-medium 区域极值、场图中的均值／Frobenius 范数不可混称；工件节点弱作用不能称为压力，有限边界距离不能替换为射线间距或穿透判定。

## 未来接口与资源合同

CLI：`--repo <正式仓库> --protocol <本阶段 protocol.json>`。读取 protocol 的 `viewer_source`、`candidate_directory`、`view_directory`、`baseline_result`、`baseline_summary`、`baseline_csv`、`targets_mm`、`bindings`、`sampled_RSS_bytes` 和 `phases['view']['helper_seconds']`。`author/authorization.json` 与 `author/direct_human_reply.json` 必须绑定 M-AVIEW1、实际未来 HEAD、protocol／人类原文 SHA 和非空回复上下文；脚本不生成授权。

未来既存 `author/M_AVIEW1_source_publication_receipt.json` 的原 SHA 与授权收据绑定，并要求状态为已发布／增量恢复通过、提交为实际执行 HEAD、准备卡为 M-AVIEW1、准备时 authorized/executed 均为 false。该证明只能在本轮真实发布以后产生和归档；当前不制造证明。原 M-ALPHA1 执行发布证明仅用于绑定保存数据来源，与此未来包装源证明分别保留。

root 提议新 helper 180 秒／outer 240 秒／采样 8 GiB；原 viewer 只取得扣除此前检查时间的剩余额度，完整 helper 包含对照、两快照和字节核验，无延期或重试。新收据为 `alpha_partial_view_receipt.json`；原 `view.json` 仍保存原 viewer 的自身动作与产物字节，新收据覆盖新显示／对照产物并明确原执行保持 not_pass。采样与协作停止不是硬 OS 限制，`mechanical_hooks_monitored=false` 保留原含义。

本次只写外部源码并作 AST／普通元数据静审；没有执行候选、导入 HF、解码 NPZ、调用观察器、积分、绘图、造新授权、写正式仓库或改旧科学资格。卸载续算能力及成本另见同目录 `UNLOAD_COST_AUDIT.md`，本候选不改变路径表示或恢复求解。


准备期最小修订：依据独立物理静审，在最终输出哈希之后及最终回执写入之后各检查一次剩余预算，之后才打印完成。原viewer、观察次数及所有物理门保持；超时外层仍为not_pass，已写的局部回执不能替代终态。原作者收据按字节另存 source_author_receipt_initial.json。
