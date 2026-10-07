# 扩大工件后的保存结果可视化候选

此文件是作者说明，尚未运行 freezer、任何观察 API 或渲染。拟在两个实际完整工况通过后比较：x71/边长16/E1的17个接受状态，以及中心71/边长18/E1的新工况全部实际 N 个接受状态。新 N、总数17+N和新工况参考结果均待真实计算，不填入推测值。

正式阶段拟为 `functional_views/workpiece_enlarge_20261007/complete_001`。复用已通过 `complete_002` 的保存状态查看器，SHA256 `16d2c0295d03579a32adaf321a283ad9ae6f23579c4455f688be8720bb1984b0`逐字节不变；freezer只改运行时限：argv120→180秒、helper120→180秒、outer150→210秒，采样内存8 GiB。采用原 F3 启动器，不改力学、几何距离、力箭头、应变或绘图算法。两工况各自目标峰值不同，图示按各自的真实加载路径解释，不能将1.8 mm与1.2 mm的峰值当作同一输入条件。

root冻结前需检查两个工况实际生产和同路径参考通过；新工况必须零启动、完整达到任务目标并卸载到零，全部实际 N 个接受状态有新鲜2N次80/120位HP参考。不能使用失败前缀、缺少参考的状态或另一工况的模型资格。原freezer保留通用保存数据功能；本次具体输入是否符合完整比较，由root按实际终端证据审阅后传入。

预算依据：旧43状态比较约47.13秒；今天25状态保存观察约44秒。root取得实际17+N后依据这两项费用与180/210秒余量确认本次卡范围。此候选没有硬编码43状态上限，也没有提前承诺任意 N 能完成。保存动画逐实际接受索引显示，无插值；结构按实际×1变形，完整上半镜像只作对称观察。展示有限工件边距离、输入反力、工件下半体力与材料/Hu分量、固体/介质的J及Green应变。曲线各自有坐标刻度；场和节点力箭头按原查看器共有标尺解释。

未来使用现有解释器从正式仓库任意目录传入实际路径：

```powershell
python <external_author>/saved_view_candidate/build_shift_view_card.py --repo . --stage functional_views/workpiece_enlarge_20261007/complete_001 --case pose002=lf_data_preparation/native_workpiece_001/shift_square_pose_002/run_001/result --reference pose002=lf_data_preparation/native_workpiece_001/shift_square_pose_002/reference/summary.json --case enlarged001=lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/run_001/result --reference enlarged001=lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/reference/summary.json
python functional_views/workpiece_enlarge_20261007/complete_001/launch_view.py view
```

这些仅是未来实际通过后的参数模板，作者没有执行。每相一次、首错关闭，不重试、不延期、不force；保存观察不构造模型、不执行 F/T/solver/HP。

`cached_fit_candidate`另保存原114行纯缓存局部查看器与原140行freezer，均逐字节保留。它只读取新的完整主查看器缓存与保存F，展示原始结构 `y=30, x∈[63,80] mm` 的尖端附近边、相邻固体Green应变与工件总/材料/Hu节点弱形式力。加大工件底边范围为 `[62,80] mm`，此窗口仅是局部尖端片段，不覆盖整个底边。工件右侧没有介质包围；局部距离接近、弱形式节点力或对称两侧法向力大小之和，都不是点压力或自由工件稳定夹持的资格证明。
