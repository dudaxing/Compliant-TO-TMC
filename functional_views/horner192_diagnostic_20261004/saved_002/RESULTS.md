# 保存诊断视图002实际结果

唯一渲染实际exit0/pass，外层2.4662198000005446秒、采样树峰132169728 B，377项绑定前后同。2880×1710 PNG经root和独立agent实际审图，标题、指数和单元数完整可读。没有新的力、切线、HP、consumer、全局组装、求解或几何计算。

上排为原F16终端保存的局部8DOF力范数：材料max=2.08301e-29 N，Hu正则max=9.85246e-31 N，总max=2.0831e-29 N。共同N色阶的1e-30只是显示下限，CSV保持原值。下排显示35个能量NaN单元以及旧36IP/26cell、新48IP/35cell的首次primitive失效位置；这是参考坐标，不是新变形或接触图。完整力仍失败，原始有限字段未获HP或平衡资格。

原001渲染也exit0完成（2.7446923999814317秒、134868992 B、366绑定同），实际审图发现标题/colorbar遮挡后保留原图。002仅修改五处排版，没有覆盖001或重跑其执行卡。两版3200行CSV逐字相同，SHA256 `fd31b7358854ea2e95b2287393b65fcbe91b89b7a1462d5745cfaccdd8f90504`；源/图SHA因排版改变而不同，元数据中的物理字段相同。

- [实际诊断图](render_001/horner192_raw_diagnostic.png)
- [全3200单元原值CSV](render_001/raw_element_diagnostic.csv)
- [元数据与字段身份](render_001/view_metadata.json)
- [唯一执行回执](render_launch.json)
- [实际独立审图](actual_view_review.json)

旧0.5mm峰值的真实×1结构和力及卸载失败时序见[循环003保存物理图](../../native_workpiece_cycle003_20261004/failure_saved_001/render_001/cycle003_failure.png)。该图的2个接受态尚无fresh HP资格，不能用本诊断补授资格。
