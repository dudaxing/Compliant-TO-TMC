# 固定工件与连续加载—卸载：2026-10-04

整体目标是从普通几何、材料、边界和任务文件得到独立 HF 正向力学结果，逐步用于真实机构夹持和候选比较。用户已委托 Agent 探索对称圆/正方形工件、尺寸/位置和较大输入行程。本目录记录第一次带固定半工件的普通文件循环，保存完整开发、失败与数值证据。

正式 Git 根是 `Compliant-TO-TMC`，唯一开发分支 `main`，origin 为 `https://github.com/dudaxing/Compliant-TO-TMC.git`。本目录名表示历史数据准备来源；HF 运行不导入 LF，不要求旧 LF 工作目录、优化器或 MATLAB。新机器先按仓库 `docs/RESUME_DEVELOPMENT.md` 恢复独立 Python 环境，再读 `docs/NUMPY_FORCE_PROGRESS_20261002.md#native-workpiece-cycle-20261004`。清单 SHA 只证明文件身份，不扩大数值资格。

## 实现与物理约定

任务/模型 1.1 增加显式 `workpiece` 和 `path`。`fixed_rigid` 将实际栅格工件的唯一节点两个位移分量固定；不以巨大 E 代替约束，不更改原材料/实体/端口。工件内部仍为 undeformed dummy 场，工件受力来自邻域弱式全局力的约束节点投影。原 1.0 无工件任务保留兼容。

初选正方形 side16mm 或圆 r8mm，中心 (70,40)mm，仅计算关于 y=40 对称的下半。粗方 h=1mm；细方/细圆 h=.5mm。三包构造全通过，原21个非边界数组 dtype/shape/bytes 相同，均有27个保存数组。只有粗方实际求解；细方/细圆没有平衡或高精度资格。粗细原设计不同，不做网格收敛解释。

加载—卸载保留有序目标及前态，不排序、不在卸载前重置位移/力/切线。平均输入通过原 KKT 控制，输入节点可有不同位移。工件的 signed `(Fx,Fy)`、保持约束反力、材料/Hu/总力、镜像整装配净矢量 `(2Fx,0)` 与双侧竖向量级 `2|Fy|` 分开报告；后者不是压力或无条件成立的夹持力。

## 实际结果与证据关系

| 阶段 | 已保存结果 | 资格及限制 |
|---|---|---|
| `construction_summary.json` / `models/` / `tasks/` | 粗方、细方、细圆纯构造通过 | 0F/T/solve/HP；构造不授受力资格 |
| `tests_v1_*` / `tiny_cycle_diagnostic_001/` | 原返零失败及完整 partial | 原预算内 time_limit，永久保留失败 |
| `tiny_range_diagnostic_001/` / `v2_validation/` / `v3_validation/` | 首拒绝原语、完整力及切线失败定位 | 原 DD/range 门保持，所有失败和来源不改 |
| `v4_validation/` | 截获态完整F/T及2新HP/96门通过；30 focused tests 通过；同 tiny 循环约1.01秒通过 | 截获态参考与 tiny 功能测试分开；不授任意输入或AD/JIT资格 |
| `coarse_square_cycle_001/result/` | [0,.1,0]mm、3接受态、API263.45秒 | 22F starts/19 completions、11T、1solve；3个原规则允许的范围拒绝trial，无失败target或二分 |
| `coarse_square_cycle_001/reference_precondition_001.json` | 原全F完成前置条件不满足，明确未启动/0HP关闭 | 不把未启动说成数值通过或数值失败 |
| `coarse_square_cycle_001/reference_002/` | 3态、6新HP80/120、58010 checks、真实exit0/pass，约60.11秒 | 只修订已声明计数谓词；原force/Jv/CSC/KKT/mean/fixed/J/balance门保持；拒绝trial未获资格 |

粗方峰值输入 R=.020941490699N、输出 +y=.114466446177mm、minJ=.947487891；半工件总力 `(-3.0237102546e-5,+2.3930273461e-5)N`。卸载末 R≈-1.19e-27N、输出≈1.76e-27mm，没有裁零。最大全局总力归一化误差1.03749e-15，原门1e-11。参考覆盖全部3200单元/6642DOF及一个声明方向，不是 HP 穷举全部切线列。

实际×1仍张开，底/左节点窗口约1.896/2.039mm，不是真实表面距离。微小介质力不能证明已夹持；没有接触压力、自由刚体平衡、完整大变形、H2/H3、HF5或本轮公开数值重放资格。三次粗方返零范围拒绝没有保存原语，具体根因尚未确诊。

[真实结构与力](../../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_physical.png)、[signed响应与分力](../../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_response.png)、[三帧实际×1动画](../../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_actual.gif)、[CSV](../../functional_views/native_workpiece_cycle_20261004/render_001/numeric_states.csv)；[旧失败与新 tiny 返零](../../functional_views/native_zero_cycle_20261004/evidence/cycle_diagnostic.png)。×20只供观察细微变形，显示重叠不是接触。

## 普通接口与接续

下列示例从仓库根运行，用现有 task1.1 显式读取有序路径，写入一个全新目录；它说明功能入口，**本轮没有再次执行**。历史 execute/audit helper 绑定旧 HEAD/冻结来源，不能将重新运行它们当作普通 CLI 或复用其已关闭阶段。

```powershell
python hf_repo/scripts/solve_native_mean.py --geometry lf_data_preparation/v2_adapter_001/converted/gripper_canonical/geometry.json --task lf_data_preparation/native_workpiece_001/tasks/gripper_coarse_square.json --output new-coarse-square-cycle --time-limit 600
```

若 task1.1 声明 `path`，CLI 自动采用其 `targets_mm`；显式 `--targets` 必须与任务一致。改峰值必须建立新任务同时更新 `input.target_mm` 和 `path`，不修改本目录冻结任务。缺省最小增量为首个非零目标/16；本轮 .1mm 循环为 .00625mm，其他设置不改。

下一步先从保存态提取真实 Q1 栅格外边界，排除 y=40 对称切口，计算距离/最近位置/交叉，0新力学调用；随后同一粗方初探 `[0,.1,.25,.5,.25,.1,0]mm`，依据实际几何、力、J和成本再决定1/2/3mm与圆形/细网格。当前这些新行程未执行。保持完整失败记录、原数值门、每个新阶段明确来源/资源以及首错停止规则；正常作者实现后再冻结新阶段，不用延长旧窗口或静默修验收条件。
