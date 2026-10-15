# 第三LF保存交付 L-TUSE1：PASS

2026-10-15。按当前用户直接请求，一次复用默认公共摘要与研究层消费者，完成第三LF原25态、峰值13/首卸14独立参考与六份既有媒体的关联、25行原值表及带图人工检查页。默认HF源码和全部原生产/参考结果保持；新独立参考、力学求解和新绘图均为0。

## 目标、理由与实现

整体目标是独立HF读取普通LF几何，返回可比较、可恢复的有限变形/TMC响应、力和实际变形，供研究层使用。第三wave已完成输入兼容、小行程、原25目标完整循环及峰值/首卸两态独立参考。本轮把已成功的结果连成外部可读的交付，避免后续逐目录寻找原值或混淆参考范围。

直接复用hf_repo/src/hf_eval/native_response.py：一次summarize_saved_native_result和write_native_response；新light_index链接原result/model/response、全25态viewer、参考/误差与收敛普通JSON、生产与参考收据。原response先于viewer/reference生成，保留原not_provided事实，不回写。API只核普通JSON/源码及既有媒体原字节，不打开科学数组。

研究层consumer保持原投影算法和JSON字段，只把固定“五份”标题改为通用标题，并在Markdown中内嵌六份既有媒体。一次读取index/linked_response/result三个JSON，输出25行；每行保accepted/original序号、leg/d/state SHA、R/q_in/q_out/global minJ、材料/Hu/总工件作用向量。所有投影值与原result逐项相等，仅Markdown显示舍入。

准备期静审发现原evaluate_native响应有invocation、evaluation_elapsed_seconds、evaluation_elapsed_scope三个运行包装字段，默认保存摘要不返回；执行前只从比对中排除这三项，物理/来源/选项/路径/资格继续严格一致。前候选和修订记录在author/pre_review及preparation_correction.json；唯一正式启动前完成，没有失败运行或修复重跑。

## 可直接使用的交付

- [人工检查页：25行与六份既有图像](run_001/consumer/REVIEW.md)
- [原浮点值状态表](run_001/consumer/states_table.json)
- [关联API响应](run_001/linked_response.json) / [轻索引](run_001/light_index.json)
- [交付摘要](run_001/delivery_summary.json) / [helper收据](run_001/execution_receipt.json) / [outer收据](delivery_launch.json)
- [源码静审](author/SOURCE_REVIEW.md) / [实际与文档审阅](author/ACTUAL_REVIEW.md) / [六份原文保留记录](author/front_history.json)

| 接受/原目标 | 路段 | d mm | 输入R N | q_out mm | 下半材料Fy N | 下半Hu Fy N | 下半总Fy N | 匹配参考 |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | origin | 0 | 0 | 0 | 0 | 0 | 0 | 未覆盖 |
| 13 | loading | 1.2 | 0.266484675829 | 1.00776495955 | 0.0579495403137 | 0.000860980209213 | 0.058810520523 | 是 |
| 14 | unloading | 1.15 | 0.240427573175 | 1.00455007476 | 0.0403544277114 | 0.00083930174773 | 0.0411937294592 | 是 |
| 24 | unloading | 0 | 1.6802106192e-25 | -9.68134279094e-25 | -2.94860820833e-28 | -9.08681691411e-28 | -1.20354251224e-27 | 未覆盖 |

两态参考返回matched_partial、selected_reference_pass=true、matched_state_indices=[13,14]，其余23态没有被本关联参考覆盖。covers_all/accepted_reference_pass/full_path_reference_pass保持false；原三项producer flags仍false。原十五门不改、不重算，参考资格只来自已有L-TREF1的4次HP与指定PORT方向。

输入反力是半模型量；表中工件值是模型/介质ON下半固定体的有符号弱式作用，材料与Hu均保留。它不是连续压力；镜像双侧幅值和不等于完整工件净力。q_out不是间隙，表中minJ为全域保存值，不能代替实体/自由介质分区值。几何距离和分区场量仍链接原viewer定义。

## 实际效果与资源

原峰值形状、输入/输出、工件作用、有限距离、实体应变/自由介质场、25帧动画、真实Newton收敛及两态参考误差均可从同一页面检查。六媒体仍是既有文件：API对前4份原字节核SHA，helper对额外收敛/参考PNG核SHA；本轮没有解码、重绘、插值帧或新增像素检查。六个页面图像路径已逐项解析/大小核对，图像质量沿用原L-CYCLE1/L-TREF1像素记录。

唯一终端3422d4 exit0，outer/helper PASS。outer 4.910959秒，树采样峰31703040B；helper 0.9922454秒，采样峰27312128B。原helper180/outer240秒、采样1GiB满足，stop=null。公共摘要/响应写入/索引写入/消费/表/页均各一次，消费者JSON读取3次；5份输出在原窗口封存，原23普通输入和5源码绑定保持。从无关cwd通过显式repo读取；不依赖旧LF工作目录。

本轮新F/T/HP/构模/平衡求解、测试、NPZ/科学gzip读取、默认安装、绘图、媒体解码和像素检查均为0。没有外部重试、延期或force。完整路径生产已完成与全25态参考未完成分别保留；压力/有效夹持/自由体释放/稳定性/制造/HF5状态不升级。

## 结果驱动的后续安排

第三例已具备与既有消费交付相同schema的25行表，可进入三设计同定义对照准备。下一阶段优先复用已交付L-COMP1普通comparison.json与本轮表/原viewer summary，按(original_target_index,leg,d_mm)形成75条原值和25组三方。先核物理条件、端口、符号和几何/分区定义，再绘反力/工件作用及有限距离/材料场对照，链接实际变形。

保M分段来源与失败历史，M主源参考14/15/18/19与13alias分开；原LF参考13/16，第三wave参考13/14。不能统一冒认参考、插值补原路径没有的卸载点或用全域minJ代替实体J。本轮未执行三设计比较或新增排名。具体输入映射、可视化和核对步骤见[THREE_DESIGN_PLAN.md](THREE_DESIGN_PLAN.md)。
