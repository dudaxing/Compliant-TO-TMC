# M-ALPHA1 实际执行闭合与增量交付计划

此文件只准备普通文档／字节交付方法。当前已有本卡真实直接批准，源码基线为 `64a19f7d990d294d09f16145eae946e0edfa1580`，唯一 launch 正在执行。root 报告原点态已接受；终态、其余状态、图件和敏感性结论尚未知。本文不假定成功，不运行闭合、发布、候选或新监控工具。

## 不变的来源合同

继承实际准备发布／恢复证明 `MSTAB1_preparation_001/publication_receipt.json`，其 SHA 为 `60f125e01524728632020d10c3541b8e7a200ff3a55e0b2a39a83940b86ab83a`；正式归档为 `author/M_ALPHA1_source_publication_receipt.json`。原 manifest 为 18651 条／9296517834 字节、science 0.5.0，SHA `0c511c4a40d1a50bb6b58615d3e4c1f9f123d40fb532c234841e2957c71a3fb4`。本轮执行发布不重扫旧约 9 GB，不改原57 bindings、task／protocol／card、worker／compare／launcher、既有输出或基准资格。

准备 protocol 的 `authorized=false/executed=false` 是不可改写的准备历史；本次实际批准另由 `author/authorization.json` 与原字节 `author/direct_human_reply.json` 记录，并绑定协议、源码提交和 source publication proof。前端新正文应明确实际批准、唯一启动和真实终态，完整保留上次正文，不能通过修改旧准备文件伪造当前状态。

## 等实际退出后再闭合

只在 root 取得真实进程退出与 outer 完整终态后读取稳定文件，不在写入中的 run/log 上冻结 SHA。终态审阅使用真实 outer/helper 回执、stdout、progress、batch/API response/result、源绑定和实际存在的图表。实际调用、资源、接受数及停止原因由原回执承载；包装审核只读已有普通记录和原字节，不重算力、门、积分、求解或绘图。

| 实际情况 | 闭合文档要求 |
| --- | --- |
| 原 production／保存／viewer／匹配均完成且原门通过 | 引用真实回执与原图／GIF／CSV／JSON，注明15原目标与额外接受态；解释同任务 alpha 敏感性，不授予稳定／压力／有效夹持／新HP／HF5 |
| 原控制器正常返回部分态，批次失败或未完成 | 保留原缓存 writer 实际保存的部分文件，记录最后真实状态、停止原因、原门和成本；只展示真实存在的图表，不冒称15目标或完整显示已完成 |
| 资源／异常退出，缓存 writer 未达到，或 helper receipt 缺失／未完成 | 按真实 outer／日志／progress说明证据缺口；不补造 result、NPZ、门、计数或图，不把内存里的未保存缓存当可恢复输出 |
| 生产成功但 viewer／比较失败 | 分开记录成功的生产与未完成的显示，保留已有真实产物及错误；不重画、重启 child、修复重跑或借旧图冒作候选图 |

闭卡后没有自动重跑、延期、force 或补科学计算。下一步只依据真实结果提出最近取舍；新的数值范围另审，不预订后续资源卡。终态 NOT_PASS 也应完整提交保存证据；交付审核 PASS 表示文档／字节完整性，不能替代数值执行 PASS。

## 最小闭合工具结构

实际终态产生后再定稿三份薄 metadata 工具，复用已审过的 generic 增量方法，不加监控／清理框架：

1. `close_execution_docs.py` 仅读真实终态审阅与作者文稿，写 `RESULTS.md`、`NEXT_STEP_REVIEW.md`，更新三份当前入口：`docs/CURRENT_STATUS.md`、`docs/RESUME_DEVELOPMENT.md`、本 stage `README.md`；三份原64a19f7正文连续、完整保留一次。记录实际文稿／审阅 SHA、原文 byte区间、图件可用性及零新增科学动作。
2. `configure_execution_delivery.py` 冻结实际存在的新 run／outer／log／auth／reply／sourceproof／审阅／RESULTS 与工具源码，声明确切增量。新的执行审阅、文档回执及配置使用独立名称，例如 `execution_documentation_receipt.json`、`execution_delivery_config.json`、`execution_final_delivery_static_review.json`；不要覆盖准备阶段已有的同名 final／documentation／config／peer 文件。
3. `deliver_execution.py finalize/verify` 仅更新增量 manifest 和读字节核对，不在工具内 commit／push。它接受真实终态 PASS 或 NOT_PASS，只要求窗口已经真实关闭、批准来源匹配、实际记录一致、原57 pins保持和文档没有升级科学资格。

唯一允许改写的原文件是两份 docs 和本 stage README（README不属于protocol pin）；其余 delta 都是实际新文件。原准备报告、准备manifest／protocol、57 pins和历史科学结果不改。现有 `stop_requested.txt` 若实际生成，作为真实停止证据保存，不用它阻断 NOT_PASS 归档，也不将它移除以制造通过。

## 最终独立审阅与发布恢复

source／closure／交付工具经过静读及AST审阅后，root才能运行普通闭合工具。三入口实际写入、审阅归档、配置冻结后，独立 reviewer 一次读取真实文件、source proof、授权／reply、实际终态、原57 pins、三份历史正文、当前相对链接及所有现存delta字节。最终报告明确其唯一未来文件是报告自身；配置只声明它的路径、不含其SHA，报告也不自hash。root显式核最终审核状态和冻结 config SHA，然后归档报告、精确stage delta并 finalize。

提交必须是原64a19f7的唯一子提交、分支main、origin保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。推送后只核增量真实字节与原manifest条目逐条继承：源／恢复同提交、远程main同提交、两个checkout clean、manifest原字节同、science 0.5.0与原科学baseline保持。发布证明同时保存真实数值终态（可为NOT_PASS）与交付恢复状态，不能因推送成功改写计算结果。

当前实际动作：只写此计划与来源SHA记录；没有执行工具、导入候选、解码NPZ、运行API／F／T／solver／viewer／HP、生成新图或修改正式仓库。交付工具实现与所有实际结果审阅待真实终态产生后进行。
