# L-CTIPACOMP1：既有双 α 全周期对照

直接用户授权实施并执行；基线 main `08d07caf6cbb1e6ebe1af6f35c8dc1b8c9d0d669`。

## 目标与原因

独立 HF 的目标是读取 LF 设计并可靠分析大变形、第三介质作用及加载／卸载。本步复用两份已完成汇总，检视将 α 从5e−7降为2.5e−7对相同20个原目标的影响，为下一项功能与物理探索提供依据。

## 授权范围

- 仅读两份固定 SHA 的 `unified_response.json`；两原人工页仅核大小并链接，间接提供已有变形动画和完整历史。不另读原 summary、task、convergence、CSV、NPZ、科学 gzip、参考结果或旧媒体。
- 按 convergence 原目标索引、display_branch、精确 d 配对20目标；40份原值、13项既有标量、260项新α减旧α描述差。两份原文嵌入保留37观察字段、全部raw及已嵌入诊断／异常／计数／来源；不按 d 或 stateSHA 跨任务去重。
- 仅 α 及 task_id／purpose／parameter_origin／description 可不同；其余任务绑定不兼容必须明确记录，不静默归一化。旧23项／新13项原 within-alpha 对照原样保留，新的跨α差仅13项。
- 新增 comparison JSON、人工页及两PNG：反力／q_out／三力Fy／距离，与介质／右侧J/Hu及分别33／23原始行的诊断。保留数值精度、符号、原分支和来源。旧14段与新4段的工作量不可作为纯α性能结论。
- helper180秒、outer240秒、采样RSS1GiB，OMP／MKL／OpenBLAS／NumExpr各最多16线程。唯一启动、首个终端错误停止，保留实际partial；无外部重试、修复重跑、延期、force、删除或回滚。两新PNG由root各检查一次，无重绘。
- 不新增构模、F／T、HP、平衡求解、测试、默认HF修改／安装或API关联。原物理定义与生产验收门保持；不授α独立、压力、有效夹持、释放、稳定性、全路径参考、网格／域独立或HF5资格。相同初始SHA不转移HP资格。
- 包含候选独立静审、实际记录与图检、main普通提交推送、同机异目录localGit恢复及回执归档。完整逐Newton历史仅通过原人工页访问，本轮不另读。

原计划：[APATH1 NEXT](../lf_circle_tip_alpha_path_001/NEXT_STEPS.md)。
