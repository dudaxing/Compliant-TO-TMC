# 最近功能选择：两设计的小批入口，或同设计匹配网格

本轮仅只读本项目已有普通 JSON/源码及文件 SHA；0 NPZ 数值、HF/LF 导入、构模、求解、HP、绘图、制卡及正式写入。上一真实 API 阶段已由根关闭；这里不增加新资格。

现成库确有两个不同的 gripper LF 设计，可用于**同物理任务、各自原生网格**的小批功能示范。不是把 coarse 设计的细网格复本当成第二设计：来源分别是 sweep/kin10/uniform 与 refine/kin1/random，声明的 native solid cell 数1086与4358，且各转换保持原 native masks。此处只核 JSON 来源/声明，未重新读取数组。

| 别名 | 普通几何路径（仓库根下） | 原 JSON SHA256 | 原生网格 |
|---|---|---|---|
| gripper_canonical | lf_data_preparation/v2_adapter_001/converted/gripper_canonical/geometry.json | 8d831fd3f1a034a3cd1948415c3f9758a2c6b94507973b7dc8c409266fec78e6 | h1mm，80×40 cells |
| gripper_native_fine | lf_data_preparation/v2_adapter_001/converted/gripper_native_fine/geometry.json | dbab7567c98e18174d198318f025184b3545c3681c060fa77d9435122bb0f32c | h0.5mm，160×80 cells |

两者 case_family 均为 gripper，域80×40mm、厚20mm、lower-half extent 相同；四组 `region_tags` 字典完全相同：support x0/y0–8、实体 uy 对称 y40/x0–60、输入 x0/y38–40沿+x、输出 x80/y28–30沿+y，采用同一参考弧长归一化 trapezoid 权重政策。

已写的 `native_model_001/tasks/gripper_canonical.json`（SHA67d21a63898b2f31962f3e930bc2cb17e36b2813671dfa413c85c7834e6c9b63）与 `gripper_native_fine.json`（SHA3638394a88ab8def0324c1e1fc58c7c6d63963296cc5d47c696aefbdac8fd78b）逐键 JSON 比对只有 task_id、geometry 不同，其余19键全部一致。共同物理合同为 E1MPa/nu.3/plane_strain、gamma=alpha1e-6/Lr80mm、平均输入目标.025mm、free output、无输入辅助弹簧/无工件、solid-incident 支承、背景全顶 x0–80 uy0、undeformed、native policy。原任务标签为 construction_test_only；它们是现成可核查的物理起点，不等于新的 HF5 研究任务已批准或已执行。因每份 task 明确绑定几何，不能把同一 task 文件直接给另一设计；应显式保留两个 geometry 身份与共享物理条件。

`inverter_canonical` 虽是另一设计，却有-x的输出端口 x80/y38–40及更长实体对称线；不应混进上述 gripper 同任务比较。right-margin2/4、gamma-half、工件覆盖文件沿用相同机制设计，也不能充当第二个独立 LF 设计。

最近功能价值是补一个很薄的小批 manifest/index：明确两 geometry/task/output 路径和共享物理条件，每例一次现有 evaluate_native，集中给出 status/失败原因、任务目标与终点、R/q/J/残量/资源、真实 result/source 身份和各自图链接；不做优化器、性能排名或跨例资格借用。API 已能接这两个 native grid、明确 task/path/initial_guess、任意 cwd 与 --repo、保存 partial/error/compact response；CLI仍只有一个 geometry/task/output（evaluate_native.py:13–28），源码中没有小批入口。

小批尚缺：显式列表与共享物理条件核对、每例新输出/一次调用与总/单例资源合同、汇总失败/来源及按 case 归属的可视化/参考链接。独立 HP/视图当前新包装绑定 coarse gripper 与 .001 小任务；不能把该 PASS 直接授予 fine 或 .025 新任务。可复用原数学，但须按新例实际 model/state/source/实际N绑定，fresh2NHP，逐例依据结果推进。无需另造材料核或重建 LF/N4。

这两个设计同时改变设计和 native 网格，因此比较只能称各 native 模型的同物理任务响应；不能称同设计网格收敛或纯设计性能优劣。若最近重点是巩固当前固定side18夹持结论，应改选**同一已有机制、同一4mm域余量/工件/材料/行程的显式匹配网格**。现 `native_map` 只读取已声明 native 网格，`lf_v2` 保持源 native cells，`analysis_domain` 只加右侧 void columns，无同设计细化适配器。需要一个明确标为 HF-derived 的整数嵌套细化几何，保留原4masks物理分区/支承端口/背景/工件/Lr80及LF provenance，并重新映射DOFs/方向/权重；现 gripper_native_fine 是另一LF设计，不能代替这项依赖。

建议根下一步优先选“两例小批薄入口”以提高对外可用性；若目标转为可转移夹持力，则先落实上述同设计网格依赖。这里不冻结新执行卡、不预设结果、资源或资格。
