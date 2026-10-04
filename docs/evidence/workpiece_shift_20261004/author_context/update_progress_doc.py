from pathlib import Path
root=Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
doc=root/"docs/WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md"
text=doc.read_text(encoding="utf-8")
text=text.replace("生产完成后才冻结新接受态参考，fresh HP80/120遍历全部真实接受索引，原力/PORT-Jv/CSC/KKT/工件投影门不变；任何失败即关闭，不以旧前缀、缩短目标或同卡修复重试补成通过。", "独立右移002已经真实生产pass：原11目标全部完成、17实际接受态、F137/131与T74/74，6个原predictor invalid_J回滚二分，未有新的range capture。helper1413.35052430/outer1414.68240900秒，helper/tree RSS480681984/463564800字节。零位R=1.94010479e-29N、q_out=-3.19950890e-29mm。其独立一次900/960秒、8GiB参考也pass：34fresh HP80/120、328767检查，helper618.89146170/outer620.53278580秒，RSS422268928/426196992字节；原力/PORT-Jv/CSC/KKT/工件投影门不变，全部实际索引逐一对照。未借001前缀、缩短目标或同卡修复重试补成通过。")
text=text.replace("软化对照尚未冻结或执行。若位置结果支持，将 E1→.5、gamma/alpha 1e-6→2e-6；", "软化001已独立构造pass并唯一启动生产1800/1860秒、8GiB；全部原11目标、零起点、物理位置、端口和数学门保持。构造helper6.43475420/outer7.68056930秒，RSS129286144/134078464字节，0F/T/求解/HP；新模型对合格位置002只变lam/mu/gamma/Et4字段，其余23原字节。现在采用 E1→.5、gamma/alpha 1e-6→2e-6；")
text=text.replace("本轮所有正式阶段仍须以终态回执和文件SHA为准。", "本轮所有正式阶段以终态回执和文件SHA为准。软化生产尚在进行，不能预设贴合改善或完整通过；后续参考仍按它真实全部N态另冻预算并做2N新HP。")
doc.write_text(text,encoding="utf-8")
print("Current actual position/reference pass and active soft scope recorded")
