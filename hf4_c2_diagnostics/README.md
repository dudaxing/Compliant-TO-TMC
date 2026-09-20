# HF4-C2 诊断证据包

本目录承接 HF4-C1 的局部负弱式节点反力问题。整体目标是建立独立于 LF 的、可由保存状态重新核验的 HF 力学评估器。本轮解释读数量、核对离散公式，并在冻结条件下检验背景边界与网格敏感性；不将这些观察升级为一般单边接触或 HF5 验收。

**当前状态：partial。** 三次 FE 保存 59 态，58 态通过；1810 项独立检查中 1809 项通过。两条边界路径完整通过；细网格 d=0.5 mm 总内力求值误差超过原门，路径不通过，有效前缀止于 d=0.4375 mm，覆盖 6/7 原目标。新 FE 已停止。先读[最终报告](../docs/HF4_C2_FINAL_REPORT.md)和[下一步稳定运动学修复计划](../docs/HF4_C2_KINEMATICS_REPAIR_PLAN.md)。

## 阅读顺序

1. [排查计划](../docs/HF4_C2_DIAGNOSTIC_PLAN.md)：问题、候选原因、先诊断后求解的顺序。
2. [公式审查](../docs/HF4_C2_FORMULATION_REVIEW.md)：材料弱式力、直接边积分、离散体项与界面项、HuHu 抵消恒等及适用边界。
3. `fields_001/plan.json`、`fields_001/summary.json`：四个 C1 已保存末态的独立 80/120 位重装、虚功和分项诊断。原 Gauss 积分不足的观察原样保留。
4. `analytic_edge_001/plan.json`、`analytic_edge_001/summary.json`：保存 Q1 场顶边材料法向牵引的解析积分。它补充积分分辨率证据，不替换原弱式反力或原验收。
5. `boundary_review/` 与 [预先判读规则](../docs/HF4_C2_INTERPRETATION_RULES.md)：单因素设计、域宽与加载混杂、自由底边做功及可推断范围。
6. [实际执行协议 v3](../hf_repo/configs/contact_c2_v3.json)、`saved_field_admission_r3.json`、`pre_execution_review_v3.json`：33 个实现文件、166 个证据输入和三模型独立重建的执行前检查。
7. `experiments/`：按扩大背景域、释放外底边、细化网格的次序执行；每条路径须通过独立审计才允许下一条。
8. `summary_001/`：三条新路径加两条 C1 基线；失败末态不参与正式比较，原目标不插值。
9. `fields_experiments_001/`、`analytic_experiments_001/`：仅两条已完整通过的新边界路径；外底边自由确实产生小幅远端材料名义拉应力，不能推广原四态全压缩结论。
10. `mesh_force_failure_diagnosis.json`、`force_precision_001/`：固定失败态的空间分布和算术归因。生产总力位级复现；主差来自 F 形成中的求和舍入；正确舍入 F 的反事实只用于诊断，不构成修复或准入。
11. `force_precision_visual_001/` 与 `independent_final_review.json`：固定失败态的算术归因图及最终独立数据复核。复核一致性通过，力学状态仍为 partial。
12. `contact_c2_presentation_001/`：共同 d=0.375 mm 三网格有效前缀与外底边自由远端符号图。`summary_manifest_amendment_001/` 保留并补正旧汇总清单的错误自哈希；其余七个科学输出匹配，后续汇总改用 `summarize_contact_c2_r2.py`。

## 为什么保留三个协议版本

v1 和 v2 均没有执行新的 FE。v1 之后补齐直接审计的实现/来源清单校验，并明确“弱式节点反力”语义；v2 之后修复串行继续门：审计文件写出 pass 后，若进程超时、异常或绑定文件变化，必须停止。v3 才是实际执行协议。三个版本的物理参数、算例、顺序、容差与预算完全相同。

修改分别见 `preflight_source_amendment.json` 和 `preflight_guard_amendment.json`。`pre_execution_review.json` 是 v2 的来源/模型范围复核，不能替代 v3 执行检查。前期 62/94 项预检及最终 103 项测试的原始日志、JUnit 和凭据均保留；这些测试不计为新的平衡路径。

## 数据和复读约定

每条路径保存原始双数组位移、模型、原始接受记录及完整控制器历史。接受记录和控制器使用无损 JSON gzip；压缩只改变存储，不删除迭代记录。独立审计逐状态保存详细 JSON，由小型 `audit.json` 绑定。外部 solve/audit 日志和回执记录退出码、超时、耗时与哈希。

必须保留 `hf_repo/`、`hf4_c1_results/`、`hf4_c2_diagnostics/` 和 `docs/` 的相对目录关系。来源中记录的原始绝对路径仅作历史定位；可复读绑定使用相对路径。旧 `.whl` 不含 C2 新增源码，应使用仓库源码和已有依赖锁。重新求解不得覆盖本目录中任何历史 run、审计、计划或摘要。

重新审计使用 `hf_repo/scripts/audit_contact_c2.py --run <run> --output <new-name.json> --protocol <repo>/configs/contact_c2_v3.json`。该程序在 run 内创建与新输出名对应的详细状态目录；搬迁验证必须在独立复制树中进行，不能向冻结原树写入新的详细目录。同一主机异目录复读只验证搬迁与证据链，不证明跨平台数值可重复性。

如需重新生成科学汇总，在新的空输出位置调用 `python hf_repo/scripts/summarize_contact_c2_r2.py --root . --protocol hf_repo/configs/contact_c2_v3.json --output <new-summary-directory>`。它保留失败前缀语义，仅修复输出清单创建顺序。历史 `summary_001` 原清单的自身条目无效，应结合上述补充清单读取，不能忽略问题或改写原文件。

负节点反力、正负抵消和失败状态都保留。初始实体横向跨度不是实际接触区域；直接材料牵引不是含正则项的完整广义边界力；固定参考试函数下的离散虚功不是压力重建；三网格比较不是连续收敛证明。
