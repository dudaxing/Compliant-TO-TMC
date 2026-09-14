"""Generate the review narrative from the completed, verified HF3 record."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
out, repo = root/'hf3_results', root/'hf_repo'
read = lambda p: json.loads(Path(p).read_text())
a = read(out/'acceptance_summary.json')
assert a['status'] == 'pass'
b = read(out/'bridge_001/summary.json')
gate = read(out/'full_path_gate.json')
paths = a['full_paths']
fmt = lambda x: f'{float(x):.6g}'
lines = []
for family, label in [('inverter','反向器'),('gripper','夹持器')]:
    m = paths[family]
    lines.append(f"| {label} | 40/40 | {m['q_out']:.9f} | {m['R_input']:.9f} | {m['path_minimum_J']:.9f} | {m['maximum_HP_relative_residual']:.3e} |")
bridge_rows = []
for family,label in [('inverter','反向器'),('gripper','夹持器')]:
    c = b['cases'][family]
    trend = c['first_layer_trend']
    bias = c['linear_reference']['A_vs_B_model_bias']['comparisons']
    bridge_rows.append(f"| {label} | {trend['output_gain']['last_error']:.3e} | {trend['input_stiffness']['last_error']:.3e} | {trend['solid_displacement_gain']['last_error']:.3e} | {bias['output_gain']['relative_error']*100:.6f}% | {bias['input_stiffness']['relative_error']*100:.6f}% |")
component_rows = []
for family,label in [('inverter','反向器'),('gripper','夹持器')]:
    x = gate['model_interpretation'][family]['component_virtual_work_fraction_at_K0_solution']
    component_rows.append(f"| {label} | {100*x['solid_material']:.6f}% | {100*x['medium_material']:.6f}% | {100*x['HuHu']:.6f}% |")
resources = a['resources']
budget_rows = [f"| {k} | {v:.3f} |" for k,v in resources['category_seconds'].items()]
report = f'''# HF-3 执行与验收报告

2026-09-14。**本轮授权的 HF-3 指定数值验收已完成**：项目适配、平均位移控制、近零算术排查、两层小位移桥接、两条 40 目标路径和独立安装重放均有对应证据。几何研究资格仍为 `pending`，功能性为 `not_evaluated`；本报告不宣布接触精度、真实材料精度或候选性能通过。

## 1. 整体目标、阶段位置与本轮要做的事

整体目标是一个独立正向力学评估器：只有 HF 仓库、独立环境与普通几何文件，也能在明确版本的物理任务下返回带单位、符号、版本、状态与逐步证据的响应。LF 和几何生成只属于数据来源。最终必须分别判断数据可读性、几何资格、求解完成度、物理模型精度与功能表现。

HF-0 核查资料和边界，HF-1 建立独立几何/实体线性接口，HF-2 验证指定 TMC 数值基准并完成强压缩算术修正。本轮把内核接入两例真实机构；先排除映射和近零精度问题，再解释模型偏差，最后才运行完整路径。这样做的原因是：一个 C-shape 基准通过，不能自动证明真实机构的支承、端口、单位及平均位移工况正确。

用户已授权按此前计划继续执行，并要求完整记录目标、工作、理由及效果。本轮未另行扩大到 HF-4 接触或小批量候选排名。前置条件见[执行计划](HF3_EXECUTION_PLAN.md)和[完整路径放行记录](../hf3_results/full_path_gate.json)。原提案的未执行/待授权措辞仅保留为历史。

## 2. 做了什么，为什么做，效果如何

| 工作 | 代码与理由 | 已观察到的效果 |
|---|---|---|
| 项目模型适配 | [project.py](../hf_repo/src/hf_eval/project.py)：将原掩膜映射到全域 TMC，显式区分实体支承与背景边界 | 原 395 数据文件字节不变；80×40 单元、3321 节点、6642 DOF；端口方向/三节点权重保留 |
| 平均位移求解 | [displacement.py](../hf_repo/src/hf_eval/displacement.py)：求解功共轭乘子，使用实际非对称 Jacobian | 解析符号、非刚性端口、秩一弹簧、Armijo、二分回滚、超时和重复性测试通过 |
| 近零材料算术 | [tmc_kernel.py](../hf_repo/src/hf_eval/tmc_kernel.py)：从位移梯度直接形成增量 Piola/log1p，避免微小应变相消 | 固定状态最大求值误差从约 5.97e-8 降至 2.98e-13；材料/网格/正则/积分不变 |
| 完整项目 API | [project_evaluation.py](../hf_repo/src/hf_eval/project_evaluation.py)、[evaluation.py](../hf_repo/src/hf_eval/evaluation.py) | 同一 evaluate/CLI 根据 task schema 分派；每状态原子写盘，失败目标指标为 null，保留最后接受态及拒绝轨迹 |
| 两层桥接 | [run_hf3_bridge.py](../hf_repo/scripts/run_hf3_bridge.py)：非线性→自身 K0；K0→实体 3×3/2×2/HF1 | 39 项桥接检查通过，三响应误差随输入缩小约同比缩小；初始模型偏差小且未反转方向 |
| 独立数值复核 | [hf3_precision_reference.py](../hf_repo/scripts/hf3_precision_reference.py)、[audit_hf3_states.py](../hf_repo/scripts/audit_hf3_states.py) | 从实际 binary64 原语重新提升到 Decimal；6 个桥接态和 80 个完整路径态全部通过，8 态完成 50/80 位交叉核验 |
| 可搬迁安装 | [run_hf3_isolated.py](../hf_repo/scripts/run_hf3_isolated.py) | 新 wheel、新环境、异地 cwd、阻断原工作区/LF；39 项验收通过，HF1/HF3 A–B–A 物理数组逐位一致 |

完整接口、方程与测试函数对照见 [HF3_IMPLEMENTATION.md](../hf_repo/docs/HF3_IMPLEMENTATION.md)；跨阶段索引见[目标总览](PROJECT_STATUS.md)及[需求对照](REQUIREMENTS_TRACEABILITY.md)。

## 3. 冻结物理任务与力的含义

两例采用原生 1 mm 网格、80×40 mm 下半模型、厚度 20 mm、平面应变，诊断材料 E=1 MPa、nu=0.3。第三介质 gamma=1e-6，alpha=1e-6，Lr=80 mm，kr=alpha Lr²(kappa_s+4mu_s/3)，正则项不再乘 gamma。两例均无工件、无输入辅助弹簧，输出弹簧 k_out=0。

输入均沿 +x；反向器输出正方向为 −x，夹持器下夹爪输出正方向为 +y。端口平均权重为 0.25/0.5/0.25。只约束平均输入位移，不把端口节点刚性绑定。实体支承/实体对称只选择实体附着节点，完整 y=40 mm 背景 uy 条件独立列出，固定 DOF 合并后只计一次支反力。[约束图](../hf3_results/plots_001/regions_and_background_constraints.png)可与 `regions` 中的节点/DOF 集合直接对照。

方程为 `r=fint+k*bout*(boutᵀu)−bin*R=0`、`g=binᵀu−d=0`。R 是驱动器**作用于当前半模型**的输入广义力；反力/能量均不隐含翻倍。夹持器这里是无工件运动，配置的输出弹簧力为零不等于测得零夹持力。材料能量仅指材料能量，完整非保守 HuHu 不能改称保守总势能。

## 4. 排查与修正，保留了哪些失败

0.2.1 在两例真实几何的固定 K0 预测状态上，d=1e-4 和 1e-5 mm 的力求值误差超出冻结的 1e-9×SF 预算，最小幅值约 5–6e-8。这里尚未求解非线性平衡，问题是近零表达式的算术消去。见[旧取证](../hf3_results/near_zero_v021_001/summary.json)、[修正决定](HF3_NEAR_ZERO_DECISION.md)。

0.3.0 在每积分点 max|grad(u)|≤0.01 时使用增量等价式、log1p 和稳定的小应变材料能量；分支外保留原强压缩表达。全部 HuHu 残差及其实际 Jacobian 保留，不截断实际 J，不改任何物理参数救活结果。[最终同状态复验](../hf3_results/near_zero_v3_final_001/summary.json)最大误差 2.98e-13；近零材料力/能量/导数测试、原 16 个小参考的 976 项检查及原三强态的 192 项检查均通过。早期修正输出与最终内核哈希分别保留，不混用版本证明。

一次新失败注入测试原先用不合适的切线制造回溯失败，但它可能在前一迭代改善残差，导致预期 3 个试探实际为 6 个。修正为显式拒绝所有试探的非法 J 注入；生产方程及阈值未改变。原[regression_a.xml](../hf3_results/regression_a.xml)的 289 通过/1 失败/1 跳过保留，随后 308 通过，再加入最终文件写入失败保护及三项测试，最终为 **311 通过、1 跳过**。跳过项是本机不能创建实际符号链接（Windows 权限 1314），不是力学检查跳过。

另有一次监控器使用无 psutil 的解释器，尚未启动力学子进程即失败。原异常、4.1104776 秒工具耗时与更换到既有 HF 解释器的处理均进入账本；早于补记的原回执不追溯覆盖。最终 I/O 失败处理保证已有状态和诊断仍可返回，目标指标为 null，已提交检查点保持原样。

## 5. 两层桥接与模型偏差解释

两例分别从零运行 1e-3、1e-4、1e-5 mm。以下前三列为最小幅值对自身 K0 的相对误差；后两列是 K0 对实体 3×3 参考的模型差异。

| 几何 | q_out/d 误差 | R/d 误差 | 实体 u/d 误差 | 初始输出增益偏差 | 初始输入刚度偏差 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(bridge_rows)}

三响应从最大到最小输入的误差均约降低 100 倍，满足冻结的末点≤1e-4 与趋势≥5。实体 3×3/2×2 刚度≤1e-11、响应≤1e-9 的核验通过。完整三幅值见[CSV](../hf3_results/bridge_001/small_displacement_bridge.csv)、[误差图](../hf3_results/bridge_001/small_displacement_bridge.png)及[39 项原始检查](../hf3_results/bridge_001/summary.json)。

在各自保存的 K0 单位位移上，以 `uᵀK_component u / R` 分解初始虚功：

| 几何 | 实体材料 | 第三介质材料 | HuHu |
|---|---:|---:|---:|
{chr(10).join(component_rows)}

结果支持“当前初始任务未被背景材料或正则项主导”，而不是有限路径或物理接触误差上界。夹持器另一次 K0 诊断仅释放 x=61..80 mm 的 20 个背景 uy DOF，实体条件不变；输入刚度差约 0.017079%，输出增益差约 0.007922%。未扩展为另一条非线性参数路径。[分量与边界图](../hf3_results/plots_001/initial_model_components_and_bias.png)保留原数组及来源哈希。

## 6. 两条完整路径与独立验收

前置桥接、独立 HP 和安装门槛通过后，按[放行记录](../hf3_results/full_path_gate.json)各执行一次 0→1 mm、40 个原目标。两例均无二分补步，失败尝试分别为 {paths['inverter']['failed_attempts']} / {paths['gripper']['failed_attempts']}；拒绝试探分别为 {paths['inverter']['rejected_trials']} / {paths['gripper']['rejected_trials']}。

| 几何 | 原目标完成 | 终态 q_out [mm] | 终态 R_input [N] | 全路径最小 J | 全路径最大 HP 自由残差/SF |
|---|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

生产停止要求自由力残差≤1e-9×SF，独立验收≤1e-8×SF；SF 从实际内力、输入力、广义弹簧力及 `1e-8*E*t*max(|d|,1e-6)` 下限构成。HP 将实际 primitive/u/R/bin/bout/k 原值提升，重算 F/J/载荷乘积/端口均值和共同 SF。不是把已经舍入的 F/J/q 提升后充当独立参考。

全部 80 个路径态及 6 个桥接态通过：HP 自由平衡、全/自由生产内力求值预算、平均约束、固定位移、全 J 正性、合力平衡及归档支反力平衡。完整路径最大生产内力求值误差/SF 为 {fmt(a['high_precision']['full_path_maxima']['full_relative_error_decimal'])}，最大 HP 合力相对误差为 {fmt(a['high_precision']['full_path_maxima']['relative_force_balance_decimal'])}。8 个末态/桥接态的 50/80 位全内力差/SF 最大 {a['high_precision']['max_cross_force_difference']:.3e}，低于 1e-30。

HP 分两次各 40 态完成完整路径复核，首次 `incomplete` 的[进度快照](../hf3_results/full_path_hp_batch1_snapshot.json)仍保留；第二次按完全相同的绑定哈希恢复，只处理剩余状态，无超时、无门槛或预算修改。最终见[80 态摘要](../hf3_results/full_path_hp_001/summary.json)、[6 态摘要](../hf3_results/bridge_hp_001/summary.json)及各逐态 Decimal 文件。生产 `result.json` 的 `independent_precision=not_evaluated` 保留其生产时事实，外部审计摘要负责给出独立结论，不回写伪造历史状态。

反向器[结果](../hf3_results/inverter_path_001/result.json)、夹持器[结果](../hf3_results/gripper_path_001/result.json)均可定位 model.npz、path.npz、steps/index.json 与逐状态 NPZ/JSON。图仅从这些数组生成，变形比例为 1；J 图按实体/介质分色条，取各单元九积分点最小 J，不能将色块解释为接触压力。

## 7. 独立性、版本与资源

当前运行源码聚合 SHA-256：`{a['source_sha256']}`。独立 wheel SHA-256：`{a['wheel_sha256']}`。Git 提交与发布 ZIP 哈希由最终[发布清单](../deliverables/HF3_release_manifest.json)记录；[源文件冻结清单](../hf3_results/production_source_freeze.json)可逐文件核对。

独立安装使用新临时目录和环境，wheel 字节与当前所有生产 .py 文件一致，以 Python `-I`、异地 cwd 和文件/导入审计阻断原工作区、LF/MATLAB来源路径。HF1 与真实几何小位移 HF3 的 A–B–A 全部物理字段逐位相同，并与开发路径在冻结容差内一致；CLI x64 初始化亦实际运行。安装的核心依赖 RECORD 哈希已检查。离线 uv 缓存按 lock 的精确版本安装，此次未重新验证第三方原始 wheel 压缩包哈希；该边界见[独立安装记录](../hf3_results/detached/summary.json)。

| 受监控作业类别 | 累计秒 |
|---|---:|
{chr(10).join(budget_rows)}

累计 **{resources['total_seconds']:.3f}/2400 秒**；最大采样进程树 RSS **{resources['maximum_sampled_tree_rss_bytes']/1024**2:.1f} MiB**，低于 4 GiB 软上限。内存是采样观察而非操作系统硬隔离。wheel 构建及依赖安装另计 {resources['installation_seconds']:.3f} 秒；文档、文件复制与打包为普通文件处理，不混算为有限元求解耗时。所有受监控失败均记账，原记录见[资源账本](../hf3_results/resource_jobs)。

## 8. 为什么这些结果有用，以及接下来做什么

本轮将“能运行非线性基准”推进到“能独立读取原始真实几何，在明确平均位移工况下可重复地求解，并对每个状态进行独立数值验收”。近零失效已经定位和修复，真实几何桥接也把实现极限与背景模型偏差分开了。原几何、HF1/HF2发布包、0.2.1 wheel及旧失败证据保持不变。

仍需解决物理可信度：当前仅为指定离散模型、诊断材料和自由输出任务；未验证真实材料、接触、稳定性、网格/第三介质/正则/步长敏感性，也未给几何资格或功能阈值。因此本次不生成性能排名或夹持力结论。

下一步应先准备并冻结 HF-4 的独立法向接触基准、间隙与接触合力定义、验收容差，再确定圆柱位置/尺寸/材料/边界及后续参数敏感性方案。正式进入接触计算属于下一阶段；本轮没有执行 HF-4。项目总览和需求对照表继续作为审查入口，而不是用成功日志替代科学判断。
'''
report = report.replace('plots_001/', 'plots_002/')
report = report.replace('Git 提交与发布 ZIP 哈希由最终[发布清单](../deliverables/HF3_release_manifest.json)记录；', 'Git 提交与每文件哈希见[包内内容清单](../HF3_CONTENT_MANIFEST.json)，ZIP 本身哈希见外部[发布清单](../deliverables/HF3_release_manifest.json)；')
report = report.replace('## 5. 两层桥接与模型偏差解释', '首轮绘图因 Matplotlib 的坐标轴 set 接口不接受 linthresh 参数中断；改为独立 set_yscale 调用后在新 plots_002 目录重绘。plots_001 已生成图及失败日志保留，该修正只影响可视化，不重求解或改写数值证据。\n\n## 5. 两层桥接与模型偏差解释')
(root/'docs/HF3_REPORT.md').write_text(report,encoding='utf-8')

validation = f'''# HF-3 验收记录（0.3.0）

2026-09-14。指定 HF3 数值验收通过：311 自动测试通过、1 Windows 实际符号链接权限项跳过；原小参考 976 项及强压缩 192 项通过；两例三幅值 39 项桥接通过；两条 40 目标平均位移路径完成，6+80 个状态独立高精度验收通过，8 态 50/80 位交叉核验通过；独立安装 39 项通过。

这说明指定离散模型的项目映射、求解、数值精度与独立重放得到验证。几何研究资格 pending，功能性未评估；无工件的夹持器自由运动不验证接触或夹持力。旧 HF2 全路径仍绑定旧版本，0.3.0 未另行重跑完整 C-shape。

完整叙述、修正原因、失败记录、物理参数、图和资源见[阶段报告](../../docs/HF3_REPORT.md)。当前生产源聚合哈希 `{a['source_sha256']}`，wheel 哈希 `{a['wheel_sha256']}`。

本仓库的紧凑证据快照在 [validation/hf3/records](../validation/hf3/records)。完整发布包另含 `hf3_results` 逐态模型/位移/反力/J/材料能量/Decimal参考与原始日志，可搬迁的395文件几何包，以及未经改写的上一版HF2修正发布包。

## 运行普通文件接口

从本仓库目录运行（result目录须不存在）：

```powershell
.venv\\Scripts\\python -m hf_eval evaluate ../geometry_dataset/canonical/inverter/geometry.json --task configs/hf3/inverter_pilot_v1.json --solver configs/hf3/full_path_solver_v1.json --output new-inverter-result
```

夹持器使用对应几何及 `gripper_pilot_v1.json`，solver相同。solver JSON从本轮实际调用逐项导出，不回改计算前冻结的 validation_spec。Python接口仍为 `hf_eval.evaluate(geometry, task_config, solver_config, output_directory)`；在调用JAX前显式设置CPU/x64。CLI负责这项配置。

验收证据不会因一次新运行成功而自动继承；新输入、物理配置或源码需要相应重新验收。完整80态HP分批的初始 incomplete 快照和全部失败日志保留。
'''
(repo/'docs/HF3_VALIDATION.md').write_text(validation,encoding='utf-8')

entry = '''# HF-3 交付证据导航

先读 [总体目标与阶段状态](docs/PROJECT_STATUS.md)，再读 [HF3报告](docs/HF3_REPORT.md)及 [需求—代码—证据对照](docs/REQUIREMENTS_TRACEABILITY.md)。

- `hf_repo/`：独立Git源码快照、精确依赖锁、0.3.0已验收wheel、普通任务/求解JSON、测试与验证脚本。
- `geometry_dataset/`：原395文件，未修改权威几何掩膜或单位/端口含义。
- `hf3_results/`：失败及修正、六个小位移桥接态、两个40目标路径、86态独立HP、图、独立安装和资源。
- `HF3_CONTENT_MANIFEST.json`：包内每个文件SHA-256、源码哈希、Git提交及wheel身份。
- `deliverables/HF2_repaired_evaluator_and_evidence.zip`：上一阶段原包逐字保留，供追溯其特定版本数值证据；不是HF3运行依赖。

数学实现验收不等于物理真值。资格仍pending、功能性未评估、HF4接触未执行。生产文件保留当时的独立精度未评估标识；最终独立结论来自外部审计与总验收摘要。
'''
(root/'HF3_EVIDENCE_README.md').write_text(entry,encoding='utf-8')
print('HF3 report, portable validation and evidence navigation written')
