# 当前接续：M-EXTEND1显式末态延伸已准备，未执行（2026-10-12）

整体目标仍为普通LF几何上的独立HF有限变形/TMC前向评价，提供可恢复反力、位移和工件作用及实际变形图给外部研究层；HF不优化、不调用dmftd，MPM暂不实现。main、既定origin、science0.5.0保持。

M-ALINK1已实际PASS闭卡并发布/恢复c4d81620：新alpha5e−7的1.20/1.15两态响应关联同态4HP和原3PNG/两帧GIF。旧alpha1e−6的24态完整循环/48HP、以及新alpha14加载对照已存在。原新alpha父M-ALPHA1仍time_limit/NOT_PASS；1.20→1.15成功child不拼为原一次完整路径。

只读源码发现默认严格续算不支持追加原任务末目标：当前child local1/global14是原最后1.15，不能直接偷换为1.10。新候选显式extend_path要求独立新task，仅保留原15目标前缀后追加1.10；旧task_id/description及所有物理字段保持，新task有独立float.hex canonical身份。fresh F/T复核原split/R，parent success及failed祖先分别保留，full_original/full_extended和原producer资格保持false。

下一卡一次36精确有限测试（真实上界16单元/50DOF）→一次真实1.15→1.10 →原纯viewer3PNG/实际N帧GIF →全部PASS才安装六生产源，同字节来源核对。tests180/controller1800/view600/helper3000/outer3060秒、采样8GiB；首错停，无重试、修复重跑、延期、force或自动回滚。默认库目前未安装，未collect/测试/科学/绘图。七候选静审通过，具体包装/输入/protocol审阅随stage保存；需要本卡新直接批准。

现有两态原R=0.37865427196005513→0.3470376815403639N；下半固定工件total Fy=0.12492121630032427→0.10671287553103108N。这些是已保存值，新1.10效果未知。新图将解释位移、输入反力、material/Hu工件作用和接近距离；段最大1.15不是原加载峰1.20，1.10不是释放完成。

完整卸载/稳定性、一般LF输入、连续总压力/有效夹持、移动/摩擦与多形状、独立全部切线列和HF5仍未完成。完整目标/工作/理由/效果记录：[准备与原图](../lf_data_preparation/native_interface_001/saved_extension_001/PREPARATION_RESULTS.md)、[具体卡](../lf_data_preparation/native_interface_001/saved_extension_001/M-EXTEND1_CARD.md)、[后续取舍](../lf_data_preparation/native_interface_001/saved_extension_001/NEXT_STEP_REVIEW.md)。原全部文档记录以下按原字节保留。

---

