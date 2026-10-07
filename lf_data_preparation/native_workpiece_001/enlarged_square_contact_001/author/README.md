# 加大方形工件的接触与力探索

目标是使夹持器末端更容易接近工件，观察 TMC 的变形分析与工件受力。当前文件仅为作者候选：尚未运行准备、力、切线、求解或高精度参考。

新任务采用固定正方形，中心 `(71,40) mm`、边长 `18 mm`，半模型内覆盖 `[62,80]×[31,40] mm`。相对旧中心 x70、边长16的工件，中心右移1 mm、边长增大2 mm；相对已通过的 x71/边长16对照，中心相同、底面下降1 mm、右面到达 x80。初始末端位于 `(80,30) mm`，与工件底面沿同一原始竖线相隔1 mm；这是未变形几何说明，不能提前解释为接触或新平衡状态。

工件右面到达分析域右边界，没有右侧包围介质，因此是显式的边界接触探索。原 LF 结构、1 mm网格、端口与支撑、材料 `E=1 MPa, ν=0.3`、`γ=α=10⁻⁶`、`Lr=80 mm`、厚度20 mm保持原样。此次先固定软硬度，以辨别尺寸与位置的作用。没有增加右边界固定条件。

纯保存数组选择得到162个工件单元、190个节点、380个工件自由度、19个与顶部 y 对称重合的约束；合并448个固定自由度、6194个自由自由度。27个模型字段中21个内部材料、几何、端口与算子字段必须逐字节不变，6个工件与约束字段随尺寸变化。尺寸变化使用坐标与连接表重新选择，不能沿用统一索引平移。

从零执行24个有序目标：

```text
0, .25, .5, .65, .75, .8, .85, .9, .95, 1, 1.05, 1.1, 1.15, 1.2,
1.15, 1.1, 1, .9, .8, .75, .65, .5, .25, 0 mm
```

这是独立的1.2 mm加载—卸载任务。原 Newton、回退、最多4层二分、最小增量 `.00625 mm`、正 J 和参考容差不变；细化接近阶段的原始目标允许每个目标按原规则推进，不能预言完整周期一定通过。静态审阅发现原 `execute_shift_pose.py` 的结果元数据断言仍硬编码1.8 mm；新包装仅将该断言末项改为本任务的1.2 mm，原求解、数学、hook、缓存和轨迹完全不变。root明确采用这项新物理任务所需的元数据适配；当前包装采用新SHA，不宣称仍为原96bf字节。原SHA256 `96bf1b48eebe22b1132f6736b17de2f4269d656442c8308c2822caa0ec0387ae`保存在 `producer_original_96bf.py`，协议绑定作历史证据，未进入运行时70个来源。当前唯一获准的切线 v5 及其有界证明不变；旧010的68个历史源码胶囊保留，当前来源为原68个角色中切线显式转换、加2个包装，共70个。任何旧卡都未修改。

已通过的 x71/E1 和 x71/E0.5完整路径与参考，只用于身份、选择和成本依据。旧 x72/边长16运行仅完成8个状态、在原规则下未完成路径，保留为关闭的失败上下文，不借用其前缀或模型资格。

准备一次120秒、外层150秒、采样8 GiB；生产一次3000秒、外层3060秒、采样8 GiB。生产资源依据完整 x71/E1约1413秒、软化对照约1193秒及新24个目标的余量。每相只运行一次；正式首错关闭，无修复重试、延期、force或前缀替代。准备只构造并导出模型；生产仅 NumPy 力、组装、切线与原平衡求解。完整生产若通过，再以实际全部 N 个接受状态另定参考卡，执行新鲜2N次80/120位 HP，随后保存变形、有限工件边距离、力和实际状态动画。

报告力时须区分输入反力、固定下半工件的 `(Fx,Fy)` 和材料/Hu分量。`2|Fy|`仅是对称两侧法向力大小之和，完整装配净 y 力为0；弱形式节点力不能作为点接触压力，介质压缩下的接近也不能直接宣布硬接触夹持成功。

审阅候选后，仓库任意目录中可由 root 使用现有解释器执行：

```powershell
python author/build_pose_card.py --repo . --mode prepare
python lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/launch_pose.py prepare --protocol lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/preparation_protocol.json
# 只有准备实际通过后，冻结生产：
python lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/author/build_pose_card.py --repo . --mode production
python lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/launch_pose.py production --protocol lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/production_protocol.json
```

首行的 `author` 为本外部候选目录，不是事先存在的正式目录；安装前不得运行后续入口。基线 main 为 `b31003303960231c5cc6bf95c9fd6fe751f85da8`，推送 origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。作者脚本不推送、不运行上述入口，也不修改正式仓库。
