# 在新电脑或任意新目录接续开发

本指南对应移交时的 **0.5.0 / HF4-B 已完成**状态。先读[开发上下文](DEVELOPMENT_CONTEXT.md)及[当前状态](PROJECT_STATUS.md)，再准备环境。此次 GitHub 移交保存代码、资料、历史结果及接续入口；文件搬迁与安装检查本身不构成新的力学验收。

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
python tools/handoff.py verify
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

wheel 可能需要先由 `fetch-evidence` 恢复。严格“断开源码”验证还必须新建工作区以外的环境、复制普通输入、安装普通 wheel，并从外部目录运行独立脚本；editable 安装不能用于声称源码已经断开。

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

如需在新机重做 HF4-B，先确定本次时间、内存和停止预算，串行执行，并选没有使用过的输出目录。以下是一条原第四组合的完整路径及其独立审计；这里选 `review_runs/g1_m1_001`，已存在时应换一个新名字：

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

先核对[开发上下文](DEVELOPMENT_CONTEXT.md)、[HF4 修正报告](HF4_REPAIR_REPORT.md)、[实现说明](../hf_repo/docs/HF4_SPLIT_IMPLEMENTATION.md)和[需求对照](REQUIREMENTS_TRACEABILITY.md)。当前没有需要续算的 HF4-B 失败路径。

下一项工作是**审阅并冻结 HF4-C 非均匀二维接触验证计划**：独立参考、物理输入、可比较的观测量、非零 HuHu 检查、网格/介质/正则化误差分离、预算和停止条件都应先确定。每次工作继续记录总体目标、要做与已做、理由、效果、局限及代码/证据链接。保留已有失败和修正因果链，不把均匀基准通过外推成真实机构功能或一般接触精度结论。
