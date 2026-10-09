# M-CYCLE1：同结构h0.5完整加载—卸载生产卡

2026-10-09（Asia/Seoul）。状态：候选源码/输入准备，静审后待明确批准。M-PREP1已通过并关闭。本卡只执行细网格生产，独立HP与保存观察/变形图在取得实际保存态后安排。

## 目标、输入与保持的物理任务

用已验证的同设计h0.5几何，通过现有CLI→单例batch→API→原求解器，从零执行全部24原目标，取得反力、端口位移、工件弱式力及可恢复状态，为h1/h0.5网格敏感性对照提供真实细网格响应。[M-PREP1实际模型与不变量](../nested_mesh_preparation_001/RESULTS.md)已通过，原粗网格[实际生产](../workpiece_forward_001/RESULTS.md)是对照基线。

输入：[manifest](manifest.json)、[task](task.json)，引用M-PREP1的自包含派生几何。协议绑定父task/model、几何JSON/NPZ、原粗manifest、原HF源、CLI和本卡包装。task仅修改ID及非物理说明，所有物理字段与准备task严格相同，geometry绑定保持。原机制四掩码、84×40mm域、固定方形center(71,40)/side18、E1/nu.3/thickness20、gamma=alpha=1e-6/Lr80/plane strain、物理支持/对称/2mm平均端口均保持。

细网格为13,440单元、13,689节点、27,378 DOF，fixed1548/free25830。新API构模结果在首个力计算前核对实际数量；成功保存的model NPZ必须与M-PREP1模型档案SHA一致，来源几何四项身份也必须匹配。没有重新细分、平滑、LF优化或旧状态种子。

原目标依次为`[0,.25,.5,.65,.75,.8,.85,.9,.95,1,1.05,1.1,1.15,1.2,1.15,1.1,1,.9,.8,.75,.65,.5,.25,0]` mm，输入为平均位移，输出弹簧0。保持`mechanical`完整NumPy力、`chunk256`切线、`port_projection`初猜；其余controller设置均与粗网格相同，只增加本次时间额度。

## 最近唯一阶段的步骤与输出

1. 核对新协议全部绑定、新输出目录、task物理字段、模型基线与模式；一次现有CLI调用。
2. 一次原构模和求解；原接受回调保存实际progress JSONL，原控制器按已批准算法回溯和二分。
3. 原缓存writer及summary各一次，保存/摘要额外F/T必须为0。输出完整model、接受态state/force/tangent/CSC、result、response、batch index和执行回执；目录仅`nested_cycle_001/run_001/`。
4. 核对24个原目标每个恰好一个原目标态，索引、d与origin/loading/unloading分支正确，峰值及卸载终点均达到；允许保留原控制器实际插入的二分态，不要求接受态总数等于24，也不要求F/T数量等于粗网格。
5. 核对保存模型/输入身份、实际F/T开始/完成计数、原生产缓存门与原资格标志；记录全部输出身份和实际成本，终态后关闭窗口。

包装复用W-API1，原`observed()`、solve/缓存门及F/T调用计数数学保持；新增的普通JSON前置、构模数量与保存模型/原目标检查不改变HF核心。源码/输入静审不算新的数值通过，不运行额外pilot或cost probe。

## 原门与新的有界资源额度

原生产门保持：relative residual≤1e-9，平均约束使用原1e-10 tolerance及native scaled constraint bound，relative global force balance≤1e-6，fixed split和≤8e-11 mm，所有接受态积分点J>0。displacement floor1e-6、force floor factor1e-8、max checks25、Armijo1e-4、max backtracks12、max bisections4、minimum increment.00625不变。没有新独立HP资格。

申请一次新窗口：**controller14400秒、helper15000秒、outer15060秒／采样8 GiB**。原h1实际helper2170.0202秒，其中kernel/transfer2127.8602秒、sparse solve6.1365秒；细单元为四倍，若迭代工作量相同，简单乘法给出约8511秒kernel工作，只用于预算依据。细网格迭代、条件性和成本可能变化，不能把该乘法当作ETA或成功保证。M-PREP1构模17.94秒也不能预测求解成本。

沿用协作检查及采样RSS，无OS硬内存上限、无force终止；同步计算在返回后的检查点才能确认超限。controller额度留600秒给helper进口/保存/终态检查，outer再留60秒；这是有界授权，不是额外重试额度。不得使用M-PREP1剩余时间或改小物理行程来取得通过。

原控制器可恢复的拒绝试探、回溯和二分按原逻辑处理并完整记录；终端异常、资源越限、路径未完成、身份或原门失败立即NOT_PASS，保存已有进度，无修复/重跑/延期。不得强制归零近旋转力、调整gamma/Lr或放宽门。

具体命令（尚未执行）：

```text
<HF-python> -X utf8 -B lf_data_preparation/native_interface_001/nested_cycle_001/launch_cycle.py production --protocol lf_data_preparation/native_interface_001/nested_cycle_001/protocol.json
```

## 成功的含义及接续

成功表示这条细网格任务的真实生产及缓存门通过；原reference/views未提供、producer flags=false保持。新HP/JIT执行/LF/保存态observer/renderer为0。当前已有未变形网格图；本卡没有授权新的力/变形图生成，后续按实际保存态单独安排参考及显示。

拿到完整结果后，先依据其实际状态数、成本、近压缩J/力及保存字段决定自有参考和观察的最近一张卡，再比较原目标/分支下的R、Fy及材料/正则分量、qout、几何间隙、J/Hu和卸载恢复。两网格只报告敏感性，不授予压力、有效夹持、收敛或HF5整体资格。

需新的明确批准：用户已批准的M-PREP1仅覆盖构模与未变形图，窗口已关闭；本卡新增完整非线性路径及最高约4小时11分钟outer额度。具体输入、源码和静审先完成，收到本卡批准后执行一次。
