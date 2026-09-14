# 第三方组件与许可证说明（THIRD-PARTY NOTICES）

本文件登记本仓库直接依赖或执行的第三方代码及其许可证。它是 E002 追加的治理记录，不改变任何已封存合同或证据；本仓库自身的 LICENSE 尚未由所有者选定，`contract_registry_v13.yaml` 中 `license_governance` 记录所有者 2026-09-13 的决定：仓库保持私有，许可证选择搁置。

## 1. 在本仓库内执行的第三方源码

| 组件 | 位置 | 版本 / 提交 | 许可证 | 在本项目中的使用方式 |
| --- | --- | --- | --- | --- |
| AuTO（UW-ERSL） | `third_party/AuTO`（git submodule） | commit `ba3c0c5dfc9acb7daff802aaf0bb41105296ad98` | GNU GPL v3.0（见 `third_party/AuTO/LICENSE`） | M0 以只读钩子原样运行其 `compliantMechanism` 反向器算例生成参照数据（仅此用途仍需子模块）。上游文件未被修改（`env/auto_upstream.patch` 为空）。 |
| AuTO `models/utilfuncs.py` 的逐字节副本（E005，2026-09-13） | `third_party/AuTO_frozen/models/utilfuncs.py`，许可证 `third_party/AuTO_frozen/LICENSE`，来源记录 `PROVENANCE.md` | 同一上游提交 `ba3c0c5`；SHA-256 `0aa90e8479e545ffab7e5022ac30433fbd64e2207b4fe57634444ff2e36b69c2` | GNU GPL v3.0（全文随附） | M3 起 `src/dmftd/mma_adapter.py` 在进程内加载并执行其中的 MMA 实现；自 E005 起以此副本为主、子模块为等价备选，两者都经哈希校验。**该文件随本仓库分发。** |

`dmftd` 在运行时导入并执行 AuTO 的 GPL-3.0 代码（MMA 优化器），且自 E005 起该文件随仓库一起分发；把本仓库作为组合作品对外分发时需要与 GPL-3.0 兼容的许可证。所有者在选定本仓库许可证前的两条路径不变：整仓选择 GPL-3.0，或在公开发布前用独立实现替换对 `utilfuncs.py` 的运行时依赖（这会改变 M3 封存的逐步对账数值）。本文件不构成法律意见。

**所有者决定（2026-09-13）**：本仓库保持私有，不计划公开发布，因此 GPL-3.0 的分发条款目前不被触发，仓库 LICENSE 的选择搁置；若将来决定公开或随论文发布代码，须先回到上述两条路径之一。该决定登记在 `contract_registry_v13.yaml` 的 `license_governance`。

`reference/auto_inverter_40x20/` 下的数组是运行 AuTO 程序得到的**输出数据**，其来源提交、环境与钩子记录在 `env/` 与 `milestones/M0/`。

## 2. 引用的公开算法

- 88 行与 99 行 MATLAB 拓扑优化程序的解析平面应力 Q4 刚度矩阵（Andreassen 等，2011；Sigmund，2001）：仅作为 M1 solid 微门的对照公式在 `tests/test_m1_solid_gate.py`（以及归档于标签 `e003-archive-v1` 的 M1 solid 门脚本）中重新实现，未复制原程序。
- 移动渐近线法 MMA（Svanberg，1987）：通过上表的 AuTO 实现调用，本仓库未自行实现。

## 3. 冻结的 Python 依赖（`env/auto-wsl-py311-freeze.txt`）

| 包 | 版本 | 许可证 |
| --- | --- | --- |
| numpy | 1.26.4 | BSD-3-Clause |
| scipy | 1.12.0 | BSD-3-Clause |
| jax / jaxlib | 0.4.30 | Apache-2.0 |
| ml_dtypes | 0.5.4 | Apache-2.0 |
| opt_einsum | 3.4.0 | MIT |
| matplotlib | 3.8.4 | Matplotlib License（PSF 风格） |
| contourpy | 1.3.3 | BSD-3-Clause |
| cycler | 0.12.1 | BSD-3-Clause |
| fonttools | 4.64.0 | MIT |
| kiwisolver | 1.5.1 | BSD-3-Clause |
| pillow | 12.3.0 | MIT-CMU |
| pyparsing | 3.3.2 | MIT |
| python-dateutil | 2.9.0.post0 | Apache-2.0 / BSD-3-Clause 双许可 |
| six | 1.17.0 | MIT |
| packaging | 26.3 | Apache-2.0 / BSD-2-Clause 双许可 |
| h5py | 3.11.0 | BSD-3-Clause |
| PyYAML | 6.0.2 | MIT |
| pytest | 8.2.2 | MIT |
| pluggy | 1.6.0 | MIT |
| iniconfig | 2.3.0 | MIT |
| pip | 25.2 | MIT |

CPython 3.11.13 依据 PSF License 分发。离线包中的 `runtime-linux-x86_64.tar.xz` 只是上述发行包的冻结拷贝，不改变各自许可证。

## 4. 字体

关闭图使用 Windows 自带的 Microsoft YaHei（`msyh.ttc`）渲染中文；该字体不随本仓库分发，仅在生成图片的机器上被引用。
