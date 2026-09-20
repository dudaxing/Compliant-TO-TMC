# 在新电脑或任意新目录接续开发

本指南覆盖 **稳定 0.5.0 / HF4-B** 与主分支 **HF4-C0/C1 实验扩展**。先读[开发上下文](DEVELOPMENT_CONTEXT.md)、[C1 最终报告](HF4_C1_FINAL_REPORT.md)、[C1 证据入口](../hf4_c1_results/README.md)和[最终摘要](../hf4_c1_results/summary_v2/summary.json)，再准备环境。[旧项目状态](PROJECT_STATUS.md)保留 0.5.0 时的事实。C0 受限参照与 C1 冻结配对任务已通过各自门禁；HF4-C 一般接触与项目整体仍未完成。TMC 净合力对账不构成其局部单边接触验收，文件搬迁和安装检查也不构成新的力学验收。

## 1. 克隆与校验

仓库名称、盘符、父目录均可自行选择；不要创建原机的 `D:\Coding`、用户 Downloads 或 Zotero 目录来满足旧路径。

```text
git clone https://github.com/dudaxing/Compliant-TO-TMC.git my-hf-work
cd my-hf-work
python tools/handoff.py verify
```

本文除明确说明外，命令均从克隆根目录执行。`python` 应指向 Python 3.13；Windows 可先用 `py -3.13` 代替。保留仓库中的相对结构：`hf_repo/` 是独立求解器，`geometry_dataset/` 是普通几何数据，`docs/` 是项目文档，阶段结果各在自己的目录。

主分支包含全部说明文档、395 个几何数据文件、各阶段摘要和图，以及当前 HF4 所需的完整证据。较大的早期原始记录通过本仓库 GitHub Release 的证据附件提供。需要追查早期原始状态或按原流程复验时运行：

```text
python tools/handoff.py fetch-evidence
python tools/handoff.py verify --full
```

`fetch-evidence` 按移交清单下载、校验并恢复证据；不要把任意同名 ZIP 当作对应发布附件。先用 `python tools/handoff.py --help` 查看本次移交工具的接口。依赖包并未随仓库或证据附件完整分发，安装还需要可用的 Python 包源或自备、已校验的缓存。

历史文档链接遵循完整工作区相对结构；未下载大证据时，部分深入到原始数组或日志的链接可能尚无本地文件。阶段报告和当前状态可先阅读，不能因附件未下载就把历史“已验收”改记为“未运行”。

## 2. 建立新的独立 Python 环境

当前包要求 `>=3.13,<3.14`，历史验收使用 CPython **3.13.6 / Windows CPU**。不要沿用 LF 虚拟环境，也不要复制原机 `.venv*` 目录。以下为 PowerShell 示例：

```powershell
py -3.13 -m venv .venv-handoff
$hfPython = (Resolve-Path .venv-handoff/Scripts/python.exe).Path
& $hfPython -m pip install --require-hashes -r hf_repo/requirements.lock
& $hfPython -m pip install -r hf_repo/requirements-dev.txt
& $hfPython -m pip install --no-deps --no-build-isolation -e hf_repo
```

Linux/macOS 的对应安装命令为：

```sh
python3.13 -m venv .venv-handoff
.venv-handoff/bin/python -m pip install --require-hashes -r hf_repo/requirements.lock
.venv-handoff/bin/python -m pip install -r hf_repo/requirements-dev.txt
.venv-handoff/bin/python -m pip install --no-deps --no-build-isolation -e hf_repo
```

`requirements.lock` 固定运行依赖及其下载哈希；`requirements-dev.txt` 固定 pytest、构建和资源监控工具。历史交付说明里将开发工具概括为 lock 依赖的一句话应按这里理解。安装开发工具后，`--no-build-isolation` 使用已安装的固定构建后端。此流程不依赖 uv、原机包缓存或 MATLAB。

运行依赖为 NumPy 2.4.6、SciPy 1.17.1、Matplotlib 3.10.9、JAX/jaxlib 0.11.0，其他传递依赖以 lock 为准。若某平台缺少所需发行文件，先记录平台和安装错误；不要静默升级版本后沿用原验收标签。Linux/macOS 的命令写法可移植，不代表这些平台已经完成项目验收。

开发安装使用 `-e hf_repo`，源代码修改会影响后续执行。若要验证普通安装，可把最后一步改成不带 `-e` 的源码安装，或安装经哈希确认的 0.5.0 wheel：

```powershell
& $hfPython -m pip install --no-deps hf_repo/dist/independent_hf_evaluator-0.5.0-py3-none-any.whl
```

该 0.5.0 wheel 已在主分支，不需要 `fetch-evidence` 恢复；稳定标签 `hf-history-0.5.0` 和 wheel 均保持原样。**它不含新增的 C0/C1 研究模块。** 运行实验扩展应使用上述 `-e hf_repo` 源码安装和 `hf_repo/scripts/` 中的新脚本，不能把旧 wheel 称为新扩展的已安装发行包。严格“断开源码”验证还必须新建工作区以外的环境、复制普通输入、安装普通 wheel，并从外部目录运行独立脚本；editable 安装不能用于声称源码已经断开。

## 3. 固定运行设置，保存新机记录

直接使用 Python API 时，必须在首次 JAX 初始化前选 CPU 和 float64。PowerShell：

```powershell
$env:JAX_ENABLE_X64 = 'true'
$env:JAX_PLATFORMS = 'cpu'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:MPLBACKEND = 'Agg'
$env:PYTHONIOENCODING = 'utf-8'
& $hfPython tools/handoff.py inspect --output review_runs/environment.json
& $hfPython tools/handoff.py verify
```

POSIX shell 使用 `export JAX_ENABLE_X64=true JAX_PLATFORMS=cpu OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg PYTHONIOENCODING=utf-8`，后续将 `$hfPython` 换成 `.venv-handoff/bin/python`。`inspect` 保存新机环境及输入检查结果；不要用新环境记录替换历史安装回执。

普通几何独立读取示例：

```powershell
& $hfPython -m hf_eval inspect geometry_dataset/canonical/inverter/geometry.json
& $hfPython -m hf_eval inspect geometry_dataset/canonical/gripper/geometry.json
```

读取成功只证明数据可读和相应文件契约成立。真实几何研究资格、功能表现和接触精度仍按各阶段报告分别判断。

## 4. 开发回归与可选数值复验

先保留新环境记录，再运行开发测试；输出使用新的命名。下面假设 `review_runs/regression_001.xml` 尚不存在：

```powershell
Push-Location hf_repo
& $hfPython -m pytest -q --junitxml=../review_runs/regression_001.xml
Pop-Location
```

移交基线历史测试为一次 **592 通过、1 跳过**，另一次 **12 通过**，合计 604 个唯一通过项。新机完整执行是新的测试记录，实际通过/跳过数量应以本次输出为准。原跳过为 Windows 符号链接权限；不同平台可能不再跳过。历史 xunit2/record_property 警告及实际保留的属性已在修正报告说明。

如需在新机严格重做原 HF4-B，应先在独立目录检出 `hf-history-0.5.0`，按该目录建立环境；当前主分支还包含本轮新增源码，其源文件清单不同于旧冻结。先确定本次时间、内存和停止预算，串行执行，并选没有使用过的输出目录。以下命令从该稳定标签目录执行，是原第四组合的完整路径及其独立审计；这里选 `review_runs/g1_m1_001`，已存在时应换一个新名字：

```powershell
& $hfPython hf_repo/scripts/run_hf4_split_normal.py --spec hf_repo/configs/hf4/validation_spec.json --gamma-index 1 --mesh-index 1 --output review_runs/g1_m1_001
& $hfPython hf_repo/scripts/audit_hf4_split_normal.py --spec hf_repo/configs/hf4/validation_spec.json --run review_runs/g1_m1_001 --output review_runs/g1_m1_001_audit --source-freeze hf4_repair_results/source_release_001/source_freeze.json
```

生产运行成功后才可把后续审计称为完整成功路径验收；运行失败时保留失败目录及原始状态，按失败证据分析。HP 审计可检查已保存接受态，但不能把部分接受态通过改写成原目标全部完成。

上述 source freeze 只用于**未经修改的 0.5.0 生产源码**。开始修改代码时另建本次源码冻结、执行计划和结果目录；不得修改旧 freeze 来使新代码与旧证据“匹配”。其余三组索引为 `(0,0)`、`(0,1)`、`(1,0)`。每组都应保存原目标、子步、失败增量、反力/间隙、独立 HP 及参考误差。修改 `--gamma-index` 或 `--mesh-index` 时同时修改输出名称，不并发占用既定数值预算。

查看历史图不需要重算。需要重绘已归档新旧 HF4 比较时，可运行：

```powershell
& $hfPython hf_repo/scripts/plot_hf4_split_comparison.py --new-root hf4_repair_results --old-root hf4_results --output review_runs/comparison_plots_001
```

该命令绘制已保存的发布证据；它不会自动用 `review_runs/g1_m1_001` 替换其中某条曲线。新的四组比较应另建完整输入组织和对应来源清单。

### 主分支新增 HF4-C0 的复核入口

以下从当前主分支根目录、使用源码环境执行，先测试和复核已保存证据，再按需要进行新计算。每个输出必须使用未存在的路径：

```powershell
& $hfPython -m pytest hf_repo/tests/test_contact_audit.py hf_repo/tests/test_contact_reference_a0.py hf_repo/tests/test_contact_reference_a0_audit.py -q
& $hfPython hf_repo/scripts/audit_contact_geometry_rational.py --output review_runs/geometry_audit_001.json
& $hfPython hf_repo/scripts/audit_contact_reference_a0.py --run research_integration_20260920/results/a0_h025_a000_r1 --output review_runs/a0_saved_state_audit_001.json
& $hfPython hf_repo/scripts/run_contact_reference_a0_isolated.py --mode solve --run review_runs/a0_h025_a000_001 --h 0.25 --amplitude 0
& $hfPython hf_repo/scripts/run_contact_reference_a0_isolated.py --mode audit --run review_runs/a0_h025_a000_001
```

冻结协议是 [contact_reference_a0_v1.json](../hf_repo/configs/contact_reference_a0_v1.json)。顺序为粗均匀独立验收、细均匀独立验收，再运行四个非均匀组合；沿用该轮明确预算，任一依赖门失败即停止后续组合。HP 审计会核对存储哈希链、每个原目标与全部插入态，以及当前源码身份。首次配置失败、6 条正式路径和 30 个接受态原件均保留，不覆盖旧输出。

本轮两网格差包含 Q1 边界插值差（离散平均 `1−a·h²/2`），不是单独的内部离散误差；`kr=0` 下 Hu 非零不证明 HuHu 正则项通过。研究来源和限制见[完整报告](HF4_C0_RESEARCH_INTEGRATION.md)。

### 当前 HF4-C1 的独立读回入口

当前选定的 10 条 C1 路径有 80 个状态（均匀 50、非均匀 30），80/120 位独立 HP 与几何门禁全部通过，选定范围共 2516 项独立检查；相关测试 173 项通过。另保留旧激活失败 run 的四态有效前缀，该 run 不通过。含前缀的历史统计为 84 态、2644 项检查，包含上述选定范围，不能重复相加。比较按[selection_v1.json](../hf4_c1_results/selection_v1.json)去重；阶段起点、原目标和插入态仍按存盘身份分别保存。

先读[物理协议](HF4_C1_PROTOCOL.md)、[激活修正](HF4_C1_ACTIVATION_REPAIR.md)与[精度补充说明](HF4_C1_PRECISION_AUDIT.md)。以下命令只读回已保存状态，并将新审计写到原证据目录以外的独立输出名；请先自行创建 `review_runs/` 目录，不要覆盖任何既有审计：

```powershell
& $hfPython hf_repo/scripts/audit_contact_c1.py --run hf4_c1_results/A0_h025_uniform_r2 --output review_runs/c1_a0_h025_readback_001.json --precision-amendment hf_repo/configs/contact_c1_precision_r2.json
```

`review_runs/` 是新建的本地复核目录，不属于发布原证据。也可以从任意其他 cwd 执行上述脚本，此时对脚本、run、output 和精度补充协议均使用本机实际绝对路径；无需重建历史盘符。审计会核对当前存盘状态、完整原目标、两数组继承、模型/代码哈希与相对来源链，不能只看顶层 `status`。

必须显式传入 [contact_c1_precision_r2.json](../hf_repo/configs/contact_c1_precision_r2.json)，才是本轮使用的 80/120 位交叉核对；80 位仍为读出量权威，原物理协议和全部误差门槛保持不变。省略此参数仍走原 50/80 位合同，用于复现历史近零分量精度失败，**不能将默认命令当作最新验收入口**。原失败审计及其日志继续保留。

### 可选的新 C1 路径重放

新计算使用 `run_contact_c1_r2_isolated.py --action solve`；独立审计使用另一个外壳 `audit_contact_c1_isolated.py` 并显式传精度补充。先为本轮建立独立目录、预算和选定路径清单。单路径求解外部上限 700 秒、单阶段内部上限 300 秒、单路径独立审计外部上限 1200 秒；最多 10 条选定路径，累计求解预算 7000 秒。失败尝试也记录耗时，不删除旧回执来重置预算。

粗网格 A0 的第一组示例：

```powershell
& $hfPython hf_repo/scripts/run_contact_c1_r2_isolated.py --action solve --run review_runs/c1_replay_001/A0_h025_uniform_r2 --kind A0 --h 0.25 --mode uniform
& $hfPython hf_repo/scripts/audit_contact_c1_isolated.py --run review_runs/c1_replay_001/A0_h025_uniform_r2 --precision-amendment hf_repo/configs/contact_c1_precision_r2.json
```

按同一合同分别完成 A0/TMC、`h=0.25/0.125` 的四条均匀路径，且四者完整独立审计均通过并保存 admission 决定后，才能运行 A0/Aalpha/TMC 两网格的六条扰动路径。下例仅在该四路径门已满足后执行：

```powershell
& $hfPython hf_repo/scripts/run_contact_c1_r2_isolated.py --action solve --run review_runs/c1_replay_001/A0_h025_perturbation_r2 --kind A0 --h 0.25 --mode perturbation --preload-run review_runs/c1_replay_001/A0_h025_uniform_r2
& $hfPython hf_repo/scripts/audit_contact_c1_isolated.py --run review_runs/c1_replay_001/A0_h025_perturbation_r2 --precision-amendment hf_repo/configs/contact_c1_precision_r2.json
```

A0 与 Aalpha 使用对应网格的 A0 均匀预载，TMC 使用对应 TMC 预载；Aalpha 是跨模型 warm start，继承的零幅态必须重新平衡并独立验收。局部阶段参数不总是物理总位移：闭合阶段是 0.25 mm 间隙之后的附加压缩，扰动阶段是固定 0.375 mm 预载上的零均值幅值。保持这一区别，不能直接按不同阶段的同名 `d` 比较力。

源预载必须保留匹配的 `audit.json` 和完整来源链；新审计外壳默认使用这个名称并拒绝覆盖。已有输出应换新 run 或显式使用新的 `--output-name` 保存诊断，不能改写历史结果来通过门禁。全路径、失败前缀、几何、数值及物理资格分别判断，依赖门失败即停止后续组合。

## 5. 哪些路径及脚本只表示历史

| 对象 | 接续时的处理 |
|---|---|
| `D:/Coding/...`、`C:/Users/Lenovo/...`、原机临时目录 | 是原运行来源、日志或访问阻断记录；不要求新机存在，不应全局替换历史文件。 |
| `hf4_repair_results/prepare_detached.py` | 固定原 Windows Python、虚拟环境和 uv 离线缓存；保留作历史流程，不直接作为新机 bootstrap。 |
| `hf4_repair_results/run_remaining.py` | 固定旧 `.venv-hf2-repair/Scripts/python.exe`；使用新环境和明确的新输出入口。 |
| `hf4_repair_results/run_budgeted.py` | 读取历史已用预算，且禁止同 `_path` 分类二次启动。不要删除旧回执重置预算；新复验必须有自己的预算与监控记录。 |
| 既有 HP 审计 `bindings.json` | 键包含历史绝对路径。搬迁后不能直接 resume 旧审计输出；在新目录建立新的 bindings 和审计。 |
| `finalize_stage.py` | 会生成汇总时间戳；历史复核需在审查副本进行，不把发布根目录当临时输出区。 |
| 旧 `*_CONTENT_MANIFEST.json`、旧 ZIP | 绑定各自发布快照；移交仓库的新增文档与布局由移交清单负责。不要修改旧清单或误称其覆盖当前全部文件。 |
| MATLAB、LF 来源验证器 | 属于资料核查/开发参考；复跑需要另行准备其明确依赖，生产 HF 不导入它们。 |

保留 `.gitattributes` 的字节保持规则，避免 Git 的 CRLF 自动转换破坏源码和证据 SHA。不要把“修正路径”做成批量重写 JSON、日志、冻结文档或原始状态。

跨电脑复用文件和环境不保证跨 CPU、操作系统或编译后端逐位相同。历史 73 项独立安装检查证明其记录环境中 A–B–A 与保存权威数组一致。新机器若逐位比较不同，应记录差异并用独立 HP、原物理门槛和明确的新运行条件判断；不能修改阈值来沿用旧 PASS。

## 6. 恢复开发时的首项工作

先核对[开发上下文](DEVELOPMENT_CONTEXT.md)、[HF4-C0 研究集成报告](HF4_C0_RESEARCH_INTEGRATION.md)、[C1 最终报告](HF4_C1_FINAL_REPORT.md)和[C1 证据入口](../hf4_c1_results/README.md)。C1 的 10 条选定路径已经完成；旧激活失败 run 的有效前缀、原 50/80 位审计失败及两项修正均作为历史因果链保留，不能由后来通过的路径替换。

四个 TMC 末态的局部节点反力分项诊断已完成，见[数值记录](../hf4_c1_results/local_reaction_diagnostic.json)和[分项图](../hf4_c1_results/local_reaction_diagnostic.png)。四态共有 18 个负节点，按参考位置均在初始实体 x 跨度 [0,2] 之外；不能据此判断实际接触区。节点合力不是边界接触压力，负节点项本身不证明接触压力失效，正负抵消后的净合力吻合也不证明单边互补条件已成立。

下一项工作是**依据保存场检查边界材料牵引、正则边界贡献及虚功平衡，再冻结外区边界与网格单因素诊断**。先追踪相关单元与积分点，区分节点离散效应和边界贡献；随后每次只改变一个边界或网格因素，保持原物理输入与验收门槛，不同时调 alpha/gamma 追求净力吻合。依据这些因果证据再确定部分接触、释放或重入参考的范围、预算和停止条件。Aalpha 仅是诊断模型，TMC−Aalpha 不是纯接触误差，两网格也不构成连续体收敛证明。

本轮不关闭一般 HF4-C/D，不直接进入 HF5、LF 优化、1800 例 HF 标签计算或最终排名。每次工作继续记录总体目标、要做与已做、理由、效果、局限及代码/证据链接，保留已有失败和修正因果链。
