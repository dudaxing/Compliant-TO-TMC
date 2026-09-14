# HF-2 小算例独立核验

冻结的 16/16 算例、976 项检查和 160 个中心差分点全部通过。验收阈值来自
`hf_repo/validation/hf2/validation_spec.json`，未因结果调整。12 个单元覆盖两种
长宽、三个非仿射场与两种材料因子；四个小网格采用第一场及预定交替材料序列。

| 核验量 | 全部算例最大相对误差 | 冻结容差 |
|---|---:|---:|
| MATLAB 局部总残差 | 5.895e-16 | 1e-9 |
| MATLAB 局部总切线 | 4.643e-16 | 1e-9 |
| MATLAB 局部材料残差 / 切线 | 5.974e-16 / 5.366e-16 | 1e-9 |
| MATLAB 局部正则化残差 / 切线 | 1.515e-15 / 5.541e-16 | 1e-9 |
| MATLAB 全局总残差 / 切线 | 6.361e-16 / 4.643e-16 | 1e-9 |
| MATLAB 全局正则化残差 | 5.749e-15 | 1e-9 |
| MATLAB J 全场 | 1.124e-16 | 1e-11 |
| MATLAB 第二 Piola 应力 | 5.323e-16 | 1e-9 |
| MATLAB 加权材料能量 | 7.498e-15 | 1e-9 |

向量采用 Euclidean 范数，矩阵和张量采用全部分量 Frobenius 范数；每项实际
分母与物理尺度均写在 summary.json 中。正则化分量来自独立的零材料调用，
没有从很大的实体力中相减提取。全局比较包含生产稀疏装配、独立逐元素稠密
累加和 MATLAB 显式置换后的数值。形函数梯度/Hessian、Lobatto 积分矩、Q1
Laplacian、刚体运动、仿射应力/能量及零态与 HF-1 线弹性切线均通过。

全部正负扰动最小 J = 0.51235724022880136，高于预定 0.4；32 条固定方向
曲线中，最差的最佳相对误差为 1.1645e-10，低于 1e-6。步长从 1e-2 减至
1e-3 的误差下降因子为 100.0003–100.0545，超过预定 20。所有五个步长均保留。
例如 element_a_field0_tm 的切线非对称比为 0.0704055751，核验采用未对称化切线。

完整验证作业墙钟 15.516 s，采样进程树峰值 387,837,952 B；专门 parity pytest
19 项通过，墙钟 6.838 s、采样峰值 301,608,960 B。两次均由统一 budget runner
记录在 resource_jobs，300 s 上限内。脚本内第一响应时间含可能的编译与计算，
未冒充纯编译时间；RSS 是采样工作集而非操作系统硬限制。

原始结果目录：`small_validation_001/`，包括 summary.json、numeric_outputs.npz、
directional_errors.csv/.npz、directional_error_curves.png 与 timing_receipt.json。
图已经直接视觉检查，16 面板标题、图例、双对数轴和全部曲线可读。pytest 证据：
`resource_jobs/small_parity_pytest_001_1965fa6e.log`。

随后为核对完整路径的独立后处理，增加了同一 16 个小状态下的直接 Piola
表达残差、J 和材料能量测试；16/16 通过，单独墙钟 3.271 s、采样峰值
116,625,408 B，receipt 为 `resource_jobs/piola_postprocessor_small_001_c27b96a4.json`。
parity 测试文件现含 35 项；根任务已将其纳入完整回归。此后补存的
directional_errors.npz 仅逐列转换已有 160 行 CSV，没有重新计算差分。

结论仅限冻结的 source_numeric 实现/源码一致性，不证明独立接触精度或网格收敛，
不替代完整 C-shape 的逐目标核验，也未对 HF-1 几何开展非线性评估。
