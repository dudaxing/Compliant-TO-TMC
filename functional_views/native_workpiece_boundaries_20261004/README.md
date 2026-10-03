# 实际Q1边界最近点：保存数据可视化

这是粗方 `[0,.1,0]mm` 三个实际接受态的纯数据查看器。它直接读 `boundary_geometry_001` 的已保存无符号距离、外边节点和最近点，不重做边提取或测距，不调用 F/T/solve/HP。

全部结构只展示实际×1。双方 y=40 对称切口已从保存边集中排除。底/左最近点分别连接显示；left 边集最近点可落在下角，图中必须将它与侧向normal间隙区别。旧 node-window 两曲线单列，不能称为最近表面距离。下方线段只连接实际保存态，未生成插值状态。

无符号边界距离不是signed penetration；未检测全包容，正距离或无交叉不证明无重叠、接触、夹紧或压力资格。

从任意克隆的仓库根运行，下列是普通接口示例。该阶段实际只运行一次，写入独占的 `render_001`。读取其他目录同份缓存时，`--result` 明确指定该目录；查看器按完整相对后缀和原SHA映射6数据文件及2源码，不打开旧机器绝对路径。

```powershell
python functional_views/native_workpiece_boundaries_20261004/plot_native_boundary_geometry.py --input lf_data_preparation/native_workpiece_001/boundary_geometry_001/measurements/boundary_measurements.json --result lf_data_preparation/native_workpiece_001/coarse_square_cycle_001/result --output new-boundary-view
```

新view阶段outer120秒/采样8GiB，首错停止、无同阶段重试或改图；执行前冻结查看器/本说明/已保存测量及5source/6payload。输出一张PNG、实际数值CSV、源脚本副本和metadata。原始单次launch位于 `boundary_geometry_001/saved_view_launch.json`，实际结果单独写RESULTS.md；本说明及图源码冻结后不改。
