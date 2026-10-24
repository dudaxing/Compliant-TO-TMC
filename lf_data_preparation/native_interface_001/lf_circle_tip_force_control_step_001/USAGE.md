# 正式非零q力控续载：实际用法

2026-10-24。**L-CTIPFSTEP1实际PASS且科学窗口已关闭。** 现有入口已在正式r9从非零q末态完成一个新增载荷；默认固定工件力控及其他入口保持，58生产源码不改。

```python
# 已完成调用的原参数记录，不得向已存在output重跑。
from hf_eval.native_guided_force_resume import extend_native_guided_force
result = extend_native_guided_force(
    saved_force_result="D:/hfh1_001/run_001/force/result.json",
    full_extended_body_load_targets_half_N=[0.0002399800950672949, 0.0002561572865437846, 0.000260201584412907],
    output_directory="D:/hfst1_001/run_001/force",
    time_limit_seconds=1800,
)
```

完整绝对P前缀保留，只计算[P1,P2]。保持mean1.06及原物理，继承q1/P1/signedR1/原split，独立求q2=0.03123384806234602 mm/R2=0.1954005432102683 N。没有q参数/答案/裁剪界；rootP0尺度原值保留，段P1单独记录。本正增段实际SP=P，原根主导小模型证据另保。

结果schema1.1，accepted0是global1/segment0 fresh，accepted1是global2/segment1新P2；full_extended_path_executed_by_child=False。下一次扩展应从这个新成功result末态出发，提供完整[P0,P1,P2,P3]，只执行[P2,P3]；P3和新窗口尚未核定/授权，不能直接编辑本次冻结包装/协议或复用已关闭窗口。

load必须严格递增的有符号绝对半模型N列表，保精确旧前缀；q保持原未变形参考下绝对mm，R是独立机构mean反力。只clock可重新配置；物理/非clock/Nmin继承。输出须全新且在直接父及fixed父树之外。同字节fixed_parent_result仅供明确恢复后的路径迁移，不借此换模型。当前接口支持成功力控末态单调续载，不从failed/partial/非末原目标自动恢复或做力卸载/自由转动。

实际源直接树`D:/hfst1_001/run_001/force`可供后续新卡；本交付顶层force_result.json是普通审查副本，旁边没有accepted缓存，不能直接当完整续载树。跨机按[RECOVERY](RECOVERY.md)恢复原字节目录与fixed模型/geometry后再核定新任务，不编辑源JSON/descriptor/SHA。

原free/mean/J/finite/global/rigid和独立body门、源核身份、fresh checks1及q/P/R/split硬身份保持。新P2无给q/HP参考，误差null；原P1工程比较仅历史。较小J/Hu及unsigned距离继续报告，P、material/Hu、单侧Fy和R分别使用，不能从本次数值通过升级压力、纯接触抗拔、极限或稳定性资格。完整数据和图见[RESULTS](RESULTS.md)。
