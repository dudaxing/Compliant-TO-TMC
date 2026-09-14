# HF-2 执行前复审

2026-09-13。用户授权根据 HF-1 执行情况再次审阅，审阅后继续执行。复审结论为可以进入 HF-2，物理路线保留，五处定义补全后已冻结。完整执行结果另见阶段报告；本文件记录计算前决策。

| HF-1 实际证据或缺口 | HF-2 处理 |
|---|---|
| 独立 wheel、新环境和第三工作目录验收通过 | 沿用独立打包及断开依赖验收；MATLAB仍只在仓库外生成普通数字参考 |
| 四数组/物理坐标/来源守恒已核验 | 两例 geometry_dataset 全部冻结；本阶段另用手工基准，不改候选几何 |
| HF-1 是去空区Q1、2×2 Gauss、小应变与平均位移约束 | 新全域TMC入口保留实体及第三介质的全部节点，使用九点Lobatto和载荷倍率控制 |
| 力和能量的半模型含义已明确 | C-shape是完整模型，source_numeric单位、厚度因子1，不套用HF-1的20mm或自动倍乘 |
| 数值成功与正式资格分开；两例仍pending | 本阶段回答指定源码复制精度，未设置的研究/制造参数继续留在后续阶段 |
| 88项测试通过，A–B–A逐位一致 | 旧测试保留回归，新核增加实际残差Jacobian、跨语言对账与路径失败/回滚验证 |
| HF-1未实测峰值内存 | 本阶段按进程树采样RSS/Windows WorkingSet，记录采样峰值和4GiB软停止；不宣称OS沙箱或捕获瞬时峰值 |

原计划必要补充已写入 [HF2_PLAN.md](HF2_PLAN.md) 第0节，以及 `hf_repo/validation/hf2/validation_spec.json`：固定局部原点、kr参考长度、小网格域/倍率/场/方向；统一范数；明确Armijo公式和检查计数；分别定义位移/加载点/反力/实体与TM能量/J误差尺度；60分钟共享预算优先于分项上限。

固定差分样本的独立算术预检，覆盖两个尺寸、三个场、两方向、五步长、两侧和九积分点，最低 J=0.51235724，满足原定 J≥0.4。预检未调用新TMC内核，未修改样本，也未根据求解结果调宽容差。

实现采用 NumPy + JAX局部float64实际残差Jacobian + SciPy一般稀疏LU，CPU执行。使用JAX/jaxlib0.11.0作为固定对账版本，在新的 `.venv-hf2` 重新安装/核验。官方[安装说明](https://docs.jax.dev/en/latest/installation.html)支持Windows CPU wheel；[jacfwd](https://docs.jax.dev/en/latest/_autosummary/jax.jacfwd.html)与[vmap](https://docs.jax.dev/en/latest/_autosummary/jax.vmap.html)用于局部导数和批处理。使用前显式启用float64和CPU，未将HF-0系统环境探针替代本次HF环境验收。

实施中审查另外纠正了真实接口问题：复数位移不能先强转实数；Newton次数须为整数；超时和失败试探也计入总装配尝试墙钟；每步保存回调后再次检查时间预算。它们不改变物理配置或验证阈值。

阶段边界：一个指定C-shape配置，MATLAB与Python各一次完整尝试，逐目标留证；参考失败、未到λ=1或超差时按实际状态报告。不会因为单元测试通过而将完整路径或接触精度标为已验证。HF-2结束后暂停，另提HF-3最近计划。
