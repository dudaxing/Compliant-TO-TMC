# γ 单因素：保存态视图候选

本目录仅为外部作者候选，尚未制卡、观察或渲染。新stage为 `functional_views/workpiece_gamma_20261007/complete_001`。

原 `saved_shift_views.py`（16d2c029…）与 `launch_view.py`（f3a96681…）原字节复用。薄wrapper在同进程运行原viewer一次，随后仅读取该次`states.csv/derived.json`，输出共有坐标的匹配Fy、间隙µm、Fy-gap、J/Hu曲线与ΔR/ΔFy/ΔJ/ΔHu及CSV。没有第二次geometry/nodeforce观察，没有F/T/model/solver/HP。GIF保留每个实际索引，不增加插值帧；节点2510与两个工况的相同原生网格相容。

默认complete制卡必须先有两工况完整生产以及各自对应实际N态的新鲜2N机械参考通过。label为`gamma1e6`（原projection）与`gamma5em7`（新gammahalf）。新生产若正式失败，可显式partial模式保存实际前缀：原工况仍有原同路径参考，新工况不传reference，标题及报告注明失败前缀、无新物理资格。生产成功但参考尚未通过时，complete模式不能制卡。

目标对照先用各task的`targets_mm[original_target_index] == d`筛出原目标，再匹配相同leg、original_target_index和实际d。额外二分态不混入目标图/CSV，仍完整保留在原视图/GIF中；其索引与普通未匹配原目标分别列出。不补点、不猜测Fy减半。Fy是下半固定工件所受总力；R是半模型输入反力；gap是钳尖到有限底边的无符号距离，与qout、压力和精确硬接触不同。共有色标及力箭头由原viewer计算；匹配曲线的两工况共用坐标。

整个原viewer＋cached绘图合并一次view phase，helper180秒、outer210秒、采样RSS8 GiB；每个实际态geometry/nodeforce各一次，首错即停，无重试/延期/force。原`view.json`保留原生成方式；新增`phase_view.json`记录合并窗口、原观察次数与cached输出。制卡只绑定数据SHA，不复制昂贵状态、切线或历史caps。

root/peer审阅完成且实际终态到齐之后，未来才可执行：

```powershell
& <HF-Python> -B <作者目录>/build_gamma_view_card.py --repo <仓库根目录> --mode complete
& <HF-Python> -B <仓库根目录>/functional_views/workpiece_gamma_20261007/complete_001/launch_view.py view --protocol <仓库根目录>/functional_views/workpiece_gamma_20261007/complete_001/protocol.json
```

作者阶段只做AST/compile、JSON/原字节身份静查，0候选导入/模型/力学/HP/geometry/API/渲染。压力与夹持判据、网格和右側余量敏感性资格没有因此增加。
