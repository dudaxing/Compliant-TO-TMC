# 本生产结果的后续参考与图已完成

2026-10-08：本目录原生产保持PASS；V1的HP0读取失败卡保留为CLOSED NOT_PASS。独立新阶段 B-REF2 两例各实际4态／8次新HP均PASS；B-VIEW2保存图、四帧动画及各自新增qualified响应PASS。原生产result/response/index、原失败输出与冻结科学源不变。

当前后续效果见[参考结果](../batch_reference_v2_001/RESULTS.md)、[图与响应](../batch_saved_view_v2_001/RESULTS.md)及[物理功能矩阵](../../../docs/PHYSICAL_FUNCTION_PROGRESS.md)。下面完整原文保留其历史日期与当时状态；不把旧失败重写为通过。

<details>
<summary>Historical records; full original bytes preserved.</summary>

## 当前：真实两例生产通过，新的参考包装读取失败

UTC 2026-10-07T20:32:01.470309+00:00：canonical 新参考卡已一次终止，exit1，新增节点数检查读取不存在的 `coords` 字段；真实23字段中的名称是 `coordinates`。失败前新HP=0、参考接受态=0、检查11项，helper约1.498秒/outer约1.880秒。fine参考与新图未执行。两例0.025 mm生产、28核心源与原54份输出字节不变，原生产资格仍通过。

本张参考卡已关闭，不修复后重试；准备独立V2最小包装、逐项字段/状态/属性核对和新卡，再单独确认执行。两设计不同，不作网格收敛或排名；HF5整体尚未完成。[当前诊断](reference_failure_diagnosis.json)；[实际阶段报告](RESULTS.md)。以下为历史记录，当前以上方及真实终态回执为准。

---

# 两例真实 batch：生产阶段完成

UTC 2026-10-07T20:12:52.065634+00:00：一次生产已实际终止，exit0；不是观察超时，也不再有本卡计算。独立saved-only闭卡核对通过。独立HP和新图仍待下一阶段，HF5与排名未完成。

整体目标是读取LF/N4普通几何，在明确一致的独立HF任务下给外部研究层提供非线性响应和接触相关观察；HF不包含优化器，不调用dmftd。本步验证同任务批量分析功能，不生成正式标签。

已做：使用发布版本aa072的28项HF执行源，冻结source/input/包装/审阅共52项绑定；原两例task及geometry保留，只有身份与各自设计/网格不同，19共同物理键不变。新批量API从无关cwd、显式repo顺序执行两例各一次，构模、求解、缓存写出、formatter和responsewriter各一次。源码、complete/full/tangent、四点0/.005/.010/.025 mm、min_increment6.25e-5及原门保持。为什么：让mock通过的薄入口确实产生两套可对照的真实结果和index，同时保留LF研究层。

实际效果：每例4原目标态、无额外二分态，14F/14完成、9T/9完成、1solve；8项once delegate逐例1次，callback4次，cached writer新增F/T为0。原J>0、production residual1e-9、native constraint bound、globalbalance1e-6及fixed8e-11 mm门通过；23 model fields/完整JSON与54份原saved outputs身份核对一致。

| 例 | 原生网格 | 末态输入 mm | 输入反力 N | 输出端口位移 mm | min J | API整例秒 |
|---|---|---:|---:|---:|---:|---:|
| canonical | h=1 mm | 0.025 | 0.00521459203 | 0.0286037185 | 0.99658126 | 162.854812 |
| native_fine | h=0.5 mm | 0.025 | 0.00375627879 | 0.0238778244 | 0.997535854 | 783.353005 |

资源实际：helper 950.663555500秒，outer 951.878764800秒；helper采样峰RSS 2817945600 bytes，outer采样child-tree峰RSS 2722684928 bytes，均在原2400/2460秒、8GiB内。helper elapsed覆盖imports至最终hash/checkpoint；最后receipt写出由outer计时覆盖。每case一次GC清理不可达递归闭包；不声称OS RSS必然立即下降。52 bindings前后不变、无stop signal。

两例是两个不同LF设计在各自原生网格上的同任务分析。q_out是加权端口位移；任务无工件，因此没有夹持力/接触/压力资格。即使两个响应可并列查看，也不能当作同设计网格收敛或正式排名。原response/index producer/reference/view资格保持未验证，HP_all_columns/contact/clamp/pressure/HF5/ranking不扩。

可审查：[执行卡](EXECUTION_CARD.md)、production_protocol.json、production_launch.json、run_001/execution_receipt.json、run_001/accepted_progress.jsonl、run_001/batch/index.json及production_closure_review.json。closure_author保存stdlib核对与文档recipe。progress_snapshot_001.json/live_observation_001.json只保留历史运行时刻，不再表示进程存活。

下一步：实际N均4；分别新卡fresh8HP80/120覆盖所有接受态/全单元DOF和既有PORT方向切线，预算coarse240/270秒、fine900/960秒各采样8GiB（旧同N成本只用于预算，不继承HP资格）。然后新saved-view卡生成每例4真实帧PNG/GIF、x1与明确40x补充、力/位移/J/平衡曲线，并保存自有qualified_response。当前这些尚未执行。

</details>
