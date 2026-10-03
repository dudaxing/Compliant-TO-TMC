# 在新电脑或任意新目录接续开发

2026-10-04当前：**matmul320候选7fff已按原字节合入；新粗方固定半工件[0,.5,0]mm三点探索正式失败并关闭，峰值达到但卸载未完成。** 2接受态[0,.5]、R_input=.106253248N、自由+y输出=.575755712mm、minJ=.735764774。600s内部预算后实际exit1，66F/50完成、27T/26完成、1solve、0新HP。16全步范围拒绝后half收敛，随后T25范围失败回滚、二分.25遇时间门；全部来源和原27数组不变。不能称新循环或两态独立参考通过。见[整体目标、选择依据、全过程与实际结果](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_003/RESULTS.md)、[×1结构/力及失败时序图](../functional_views/native_workpiece_cycle003_20261004/failure_saved_001/render_001/cycle003_failure.png)。

新独立保存F16诊断一次复现原异常：首坏为已选辅助能量Horner乘积的(lo,hi)回缩项，非旧矩阵乘法、非overflow；36点物理词落到2^-400下界以下。只1F开始/0完成、0T/HP/solve，diagnostic_captured不是数学资格。下一最小候选改Horner共同尺度与乘加顺序，保留原14阶系数/CI域/P/门；尚未实现，先新F16完整F/T与fresh HP核验，再新连续路径和1mm探索。不增预算重开旧失败，不裁零或借旧F36解释后期未捕获T25。

旧31d955七态14fresh HP及真实边距1.471935964mm保持自己的来源资格；保存F36/candidate7fff/consumer B52的19200局部＋9全局原门和原失败也保留，不能转给新循环。当前新图仅保存诊断、无新测距/夹持资格；1/2/3mm未执行。signed gap/交叉/包容、压力/有效夹持、自由工件、细/圆平衡、H2/H3/HF5及完整AD/JIT仍待实现或资格化。完整持续记录见[开发进度](NUMPY_FORCE_PROGRESS_20261002.md#native-workpiece-cycle003-20261004)。仅main、origin固定https://github.com/dudaxing/Compliant-TO-TMC.git；公开恢复只验文件身份。

以下为上一阶段及更早时点的保留记录；当前状态以页首与持续报告末节为准。


2026-10-04历史状态（0.1mm阶段）：**普通文件的固定半工件、平均输入驱动和连续加载—卸载已实现；粗方形工件[0,.1,0] mm实际完成，3接受态的6次新HP80/120独立参考全部通过。** 正方形side16mm、中心(70,40)mm，计算下半；3200单元／6642DOF／376有效fixed。峰值输入R=.020941490699N、自由+y输出=.114466446177mm，半工件总(Fx,Fy)=(-3.0237102546e-5,+2.3930273461e-5)N，minJ=.947487891；卸载末输入R≈-1.19e-27N、输出≈1.76e-27mm。生产263.45秒，参考60.11秒／58010检查；30项相关测试通过。见[完整目标、实现、诊断、成本和效果](NUMPY_FORCE_PROGRESS_20261002.md#native-workpiece-cycle-20261004)、[实际结构与力](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_physical.png)、[三帧真实动画](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_actual.gif)、[数值与分力](../functional_views/native_workpiece_cycle_20261004/render_001/workpiece_cycle_response.png)。

独立参考覆盖全部单元与DOF、三力、声明方向切线作用、CSC组装、平均约束及工件/支承反力；不是高精度穷举全部切线列。生产22F开始/19完成、11T完成、1solve，差额是3次返零力-only全步范围拒绝及原规则下的半步回溯，接受态通过不代表这些拒绝态已获资格。原“所有F开始必须完成”前置合同明确0HP关闭；[新保存态合同与计数对账](../lf_data_preparation/native_workpiece_001/coarse_square_cycle_001/reference_002/reference_contract.json)只修订这一已声明计数条件，全部原数学门保持。算术范围限制未完全消失；不扩大到接触、夹持压力、H2/H3、HF5、AD/JIT或全部任意输入。

Agent已按用户授权选择圆r8mm和正方形side16mm、中心(70,40)mm，粗方/细方/细圆三包构造通过；细方/细圆尚未求平衡。当前×1图仍明显张开，底/左节点窗口约1.896/2.039mm只是代理观测，非真实表面距离；微小预接触介质传力不能当有效夹持。新增纯保存态Q1外边界测量已通过14解析例及3接受态读取，双方排除y=40镜像切口、0新F/T/solve/HP；峰值底边最近无符号距离1.895882476mm、左边集1.981492877mm（最近为下角到下方实体，非侧向normal gap），卸载显示2mm，包容未检测。见[实际×1边界/最近点与独立代理曲线](../functional_views/native_workpiece_boundaries_20261004/render_001/native_boundary_geometry.png)。下一以同一粗方模型探索[0,.1,.25,.5,.25,.1,0]mm；依据实际作用和成本再扩到1/2/3mm及圆形/细网格。该大行程当前未执行。仅在main开发，origin固定为https://github.com/dudaxing/Compliant-TO-TMC.git。旧无工件细.025路径及公开重放保留各自冻结资格；本轮公开恢复仅验文件身份，不借用其数值重放资格。

以下增补保留各执行时点；当前结论和下一步以本条及报告末节为准。旧记录中的“尚未实现”和旧计划不作为当前状态。

2026-10-03最新：**普通文件的NumPy平均驱动平衡入口已接通**。粗夹持器0→.001mm实际路径、两态4次新HP80/120全量参考及两功能测试通过；输入力.0002084121N、自由+y输出.0011437157mm，独立残量1.54e-11。见[目标、实现、数值和物理解释](NUMPY_FORCE_PROGRESS_20261002.md#native-mean-20261003)、[实际形变/力/端口图](../functional_views/native_mean_20261003/native_mean_path.png)与[两帧动画](../functional_views/native_mean_20261003/native_mean_path.gif)。这是无工件小TEST，普通反向器新路径、完整行程、研究H2/H3、真实夹持与批量标签仍未完成；下一步同入口接粗反向器小步，现未执行。

main 93851df的[实际公开恢复](../handoff/native_mean_20261003/public_recovery_verify.json)通过：12 payload／77数组及图包6文件字节相同，物理/求解诊断JSON除耗时与关联hash外一致，0新HP。下一粗反向器小TEST尚未执行。

2026-10-03最新：**普通原生模型的三分量NumPy切线入口及完整CSC组装已接通**。粗夹持器3200单元／6642DOF保存checker态，两个方向经40次新HP80/120全量核对通过，2案功能测试通过；最坏归一化误差4.43e-14，原门未改。三完整矩阵保留fixed行列及HuHu非对称性，见[实现、数值、成本及物理解释](NUMPY_FORCE_PROGRESS_20261002.md#native-tangent-20261003)与[两方向的内力变化率图](../functional_views/native_tangent_20261003/native_tangent_directional_actions.png)。本步21.25秒为粗例给定态实测，未求平衡／未执行.025mm目标；下一步接普通文件的小步平均驱动平衡并显示真实形变、输入力和自由输出。工件／研究H2-H3／完整接触与批量标签仍待完成。

科学交付main ae8f29c及[实际公开恢复证明](../handoff/native_tangent_20261003/public_recovery_verify.json)已通过：异目录9结果文件／43数组精确相同，图包4文件字节相同，0新HP。接续见[粗夹持器0→.001mm平均驱动平衡的新近期计划](NUMPY_FORCE_PROGRESS_20261002.md#native-mean-next-20261003)，截至本条尚未执行该新路径。

2026-10-03最新：**新普通候选的NumPy完整力入口已接通，三例六制造态经64次新HP80/120全量核对通过，3案功能测试通过**。材料/HuHu/总力均满足原门，38400单元/全部DOF覆盖，最大归一化误差8.64e-17；保存模型、原始split状态、三力/应力/J/Hu/能量和全精度参考。见[目标、实施、物理效果和接续](NUMPY_FORCE_PROGRESS_20261002.md#native-force-20261003)、[位移/J/Hu](../functional_views/native_force_20261003/native_force_fields.png)、[三类内力](../functional_views/native_force_20261003/native_force_components.png)。本步为给定位移静态内力，未执行task的.025mm目标；下一普通模型的非对称切线/小步平均驱动平衡，工件/研究H2-H3/一般接触/批量标签仍待完成。

2026-10-03最新先看[显式原生任务／模型实现与恢复](NUMPY_FORCE_PROGRESS_20261002.md#native-model-construction-20261003)：native_project API／CLI、三份明确TEST task、23字段model.json／model.npz和源HF副本、独立核对、五案测试及两图随Git。两粗旧模型intrinsics精确相同；细.5mm保留五节点权重和169fixed。任务绑定四mask几何ID及完整descriptor语义SHA，analysis_grid.policy必须显式native；没有默认全研究政策。输入.025只是保存指令，force／solver未运行。下一步先新文件接口的NumPy静态力与参考，再安排有限路径；原冻结证据与默认内核保持。

以下按执行时点保留早期恢复说明；接续优先使用最新实施记录，不重开关闭窗口。

2026-10-03最新先看[split平均端口功能与恢复命令](NUMPY_FORCE_PROGRESS_20261002.md#split-average-20261003)：显式新入口已接NumPy实际CSC增广系统，两条六单元路径／272项新HP检查通过。模型、split状态、总／增广矩阵、参考、协议与[实际图](../functional_views/split_average_20261003/split_average_demo.png)均随Git。新平均入口尚未接入旧文件dispatcher；下一步用原HF3规范机构小行程，不能将普通实体演示当作机构、接触或批量标签验收。

2026-10-03后续先看[新h=.125 NumPy平衡结果和接续方法](NUMPY_FORCE_PROGRESS_20261002.md#numpy-h0125-path-20261003)。20条实际接受记录／19唯一状态及420项新HP检查通过，完整小输入、模型、两数组状态、总CSC矩阵、精确新参考、源码及20帧动画均随Git，不需旧机盘符或Release恢复即可读取／重绘。最新下一步为split平均端口控制，而非继续自动细化。新路径数值资格不等于一般接触或真实工件夹持资格；以前的关闭窗口仍保持历史身份。

2026-10-03接续先看[NumPy完整静态范围、微小应变修复与实际图](NUMPY_FORCE_PROGRESS_20261002.md#numpy-scope-20261003)：96状态／129方向的774＋774原门全通过，新源码、最小NPZ、结果及图随Git。重画图不需HP大数据；完整参考比较需恢复既有`hf4-c2-development-arithmetic-20260930-v1.zip`，再运行报告中的输入提取器，不能把缺参考的轻量树记作全参考恢复。原25场停止及微小应变诊断保留，不拼接资格。下一步选新的h=0.125 NumPy路径和新态独立核查；旧h=0.0625图示末态HP平衡仍not_pass。

2026-10-02新增[NumPy完整力→组装→解析切线→C1新平衡与独立审计](NUMPY_FORCE_PROGRESS_20261002.md)。新源码、三组小测试、四保存场比较、七方向切线比较、15唯一新状态和完整新HP80/120参考、图与动画均随Git，阅读和复核这些结果不需要旧机盘符或大资产恢复。C1瘦输入的 `run_numpy_c1_force.py --saved-input` 已在另一目录复算，41数组逐位相同。新路径的 `recovery_model.npz` 及源码扩展记录补齐控制/材料输入，原作者summary与后完成audit按时点分别保留。先看本次报告再接续范围；前文F系列仍保持历史结论。

当前主干状态先看 [CURRENT_STATUS](CURRENT_STATUS.md)、[物理与功能进度及可视化](PHYSICS_AND_FUNCTION_PROGRESS_20261001.md)与[主干开发流程](DEVELOPMENT_WORKFLOW.md)。截至2026-10-01，F-SELECT1已按明确批准正常关闭，70个必需事件和4个诊断事件已保留，仅既定前缀完成；[实际结果](F_SELECT1_RESULT_20261001.md)可直接阅读。完整新候选force/AD、一般接触与HF5仍未完成，旧TMC已有内力/切线/平衡能力，默认内核未切换。前次大证据交付见[开发证据移交](DEVELOPMENT_HANDOFF_20260930.md)；原S0、v3/v4、F-STREAM1 partial及[主干整合报告](MAIN_CONSOLIDATION_REPORT_20260927.md)保留历史事实，不相加重叠覆盖。

后续只在本仓库 main 开发，origin 为 `https://github.com/dudaxing/Compliant-TO-TMC.git`。本机正式根为 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`，其中 `hf_repo/` 是源码；外层旧 `Compliant-Nonlinear-TMC-O/hf_repo/` 只保留历史。其他电脑可以选任意克隆目录，不需要原盘符。

本指南覆盖稳定 0.5.0 / HF4-B 与主分支 C0/C1/C2 扩展。[旧项目状态](PROJECT_STATUS.md)、[v3 最终报告](HF4_C2_FINAL_REPORT.md)、[v4 冻结报告](HF4_C2_V4_FREEZE_REPORT.md)保留各自时点事实，不作为最新执行许可。C0 受限参照与 C1 配对任务通过各自门禁；一般接触与项目整体仍未完成。TMC 净合力对账不构成局部单边接触验收，文件恢复与安装检查也不构成新的力学验收。

## 1. 克隆与校验

仓库名称、盘符、父目录均可自行选择；不要创建原机的 `D:\Coding`、用户 Downloads 或 Zotero 目录来满足旧路径。

```text
git clone https://github.com/dudaxing/Compliant-TO-TMC.git my-hf-work
cd my-hf-work
git config core.longpaths true
git switch main
python tools/handoff.py verify
```

本文除明确说明外，命令均从克隆根目录执行。`python` 应指向 Python 3.13；Windows 可先用 `py -3.13` 代替。保留仓库中的相对结构：`hf_repo/` 是独立求解器，`geometry_dataset/` 是普通几何数据，`docs/` 是项目文档，阶段结果各在自己的目录。

S0 后主分支保留说明、395 个几何文件、完整 hf_repo、各阶段摘要和图。详细 C0/C1/C2、HF4 审计/探针及早期原始证据通过版本化 Release 资产按需恢复；原字节和失败状态不变。见 [S0 分层报告](HF4_C2_S0_STORAGE_REPORT.md)。需要全部原始证据时运行：

```text
python tools/handoff.py fetch-evidence
python tools/handoff.py verify --full
```

`fetch-evidence` 按移交清单下载、校验并恢复证据；不要把任意同名 ZIP 当作对应发布附件。先用 `python tools/handoff.py --help` 查看本次移交工具的接口。依赖包并未随仓库或证据附件完整分发，安装还需要可用的 Python 包源或自备、已校验的缓存。

新增2026-09-28至09-30完整冻结根的恢复入口见[最新移交](DEVELOPMENT_HANDOFF_20260930.md)。Windows 的 Git 长路径选项用于克隆；当前移交工具另以 native extended path 恢复/核验深层证据，不需修改系统 LongPathsEnabled。原 `.pyd` 仅作历史身份快照，不复制到新环境加载。

2026-10-01新增F-SELECT1根的31个结果/入口文件随Git，13个`aux`来源复制件由新版本化资产恢复，避免Windows Git保留名拒绝。查看图/74条选择JSON不需下载；完整来源用`python tools/handoff.py fetch-evidence --asset hf4-fselect1-prefix-select-20261001-v1.zip`，再用同资产参数`verify`核对。索引带原reader/native来源依赖；不能把缺13复制件记作完整冻结根已恢复。无需关闭`core.protectNTFS`或修改冻件。

稳定 F 保存输出与 v4 大载荷通过本轮后续证据 Release `hf4-c2-followup-evidence-v1` 接入统一索引；旧报告中的“只存于本机”描述保持其历史时点。只需要这两项时：

```text
python tools/handoff.py fetch-evidence --asset hf4-c2-stable-f-saved-production-arrays-v1.zip --asset hf4-c2-v4-mesh_h00625_v4-payloads-v1.zip
python tools/handoff.py verify --asset hf4-c2-stable-f-saved-production-arrays-v1.zip --asset hf4-c2-v4-mesh_h00625_v4-payloads-v1.zip
```

需独立复制树时，将上面的资产名传给 `prepare-replay --destination <尚不存在的目录> --asset NAME`；可重复 `--asset`。工具恢复索引声明的依赖，准备目录本身不启动 FE 或 HP 审计。本轮上传和空目录恢复结果见[整合报告](MAIN_CONSOLIDATION_REPORT_20260927.md)。

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

该 0.5.0 wheel 已在主分支，不需要 `fetch-evidence` 恢复；稳定标签 `hf-history-0.5.0` 和 wheel 均保持原样。**它不含新增的 C0/C1/C2 研究模块。** 运行实验扩展应使用上述 `-e hf_repo` 源码安装和 `hf_repo/scripts/` 中的新脚本，不能把旧 wheel 称为新扩展的已安装发行包。严格“断开源码”验证还必须新建工作区以外的环境、复制普通输入、安装普通 wheel，并从外部目录运行独立脚本；editable 安装不能用于声称源码已经断开。

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

## 4. 开发回归、保存证据复读与历史数值接口

本节从**当前主分支**读取历史 HF4/C0/C1 数据的审计、重绘与预载示例，均以前面 `python tools/handoff.py fetch-evidence` 和 `python tools/handoff.py verify --full` 成功为数据前置；轻量克隆本身不含这些原始文件。只做相关阶段时，也可按下表恢复并核验对应资产。C2 使用后面的独立 `prepare-replay` 示例。恢复数据不等于启动新 FE 的准入；下述求解命令保留历史复验接口说明，当前仍停止新 FE。

| 当前主分支的数据用途 | `fetch-evidence --asset NAME` 后以 `verify --asset NAME` 核验 |
|---|---|
| HF4 新旧结果重绘 | 分别恢复 `hf4-c2-s0-historical_repair_details-v1.zip`、`hf4-c2-s0-historical_hf4_details-v1.zip` |
| C0 保存态审计 | `hf4-c2-s0-c0_runs-v1.zip` |
| C1 保存态审计与预载数据 | `hf4-c2-s0-c1_runs-v1.zip` |

以上命令均接在 `python tools/handoff.py` 之后；每个资产分别执行一次。单元测试和普通几何读取不需要恢复这些大资产。另行检出稳定标签时，以该标签自己的历史布局和证据清单为准。

先保留新环境记录，再按改动范围选择测试；输出使用新的命名。下面是普通回归范围，假设 `review_runs/regression_001.xml` 尚不存在：

```powershell
Push-Location hf_repo
& $hfPython -m pytest -q --ignore=tests/test_windows_owned_process.py --ignore=tests/test_windows_owned_cpu.py --ignore=tests/test_windows_cleanup_contract.py --ignore=tests/test_s0_event_logging.py --junitxml=../review_runs/regression_001.xml
Pop-Location
```

上面排除的四个实验监督/日志测试依赖原执行卡身份与 deadline；它们随源码及原回执保留，不应为运行通用测试伪造已关闭卡的环境或重开旧窗口。其他新增研究测试也须根据本次计算范围、来源及预算选择。文件交付验证可独立运行 `python -m unittest discover -s tools -p "test_*.py"`，不执行 FE。

移交基线历史测试为一次 **592 通过、1 跳过**，另一次 **12 通过**，合计 604 个唯一通过项。新机完整执行是新的测试记录，实际通过/跳过数量应以本次输出为准。原跳过为 Windows 符号链接权限；不同平台可能不再跳过。历史 xunit2/record_property 警告及实际保留的属性已在修正报告说明。

如需在新机严格重做原 HF4-B，应先在独立目录检出 `hf-history-0.5.0`，按该目录建立环境；当前主分支还包含后续阶段新增源码，其源文件清单不同于旧冻结。先确定本次时间、内存和停止预算，串行执行，并选没有使用过的输出目录。以下命令从该稳定标签目录执行，是原第四组合的完整路径及其独立审计；这里选 `review_runs/g1_m1_001`，已存在时应换一个新名字：

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

### HF4-C0 保存证据复核与历史求解接口

以下从当前主分支根目录、使用源码环境执行，先测试和复核已保存证据，再按需要进行新计算。每个输出必须使用未存在的路径：

```powershell
& $hfPython -m pytest hf_repo/tests/test_contact_audit.py hf_repo/tests/test_contact_reference_a0.py hf_repo/tests/test_contact_reference_a0_audit.py -q
& $hfPython hf_repo/scripts/audit_contact_geometry_rational.py --output review_runs/geometry_audit_001.json
& $hfPython hf_repo/scripts/audit_contact_reference_a0.py --run research_integration_20260920/results/a0_h025_a000_r1 --output review_runs/a0_saved_state_audit_001.json
& $hfPython hf_repo/scripts/run_contact_reference_a0_isolated.py --mode solve --run review_runs/a0_h025_a000_001 --h 0.25 --amplitude 0
& $hfPython hf_repo/scripts/run_contact_reference_a0_isolated.py --mode audit --run review_runs/a0_h025_a000_001
```

冻结协议是 [contact_reference_a0_v1.json](../hf_repo/configs/contact_reference_a0_v1.json)。顺序为粗均匀独立验收、细均匀独立验收，再运行四个非均匀组合；沿用该轮明确预算，任一依赖门失败即停止后续组合。HP 审计会核对存储哈希链、每个原目标与全部插入态，以及当前源码身份。首次配置失败、6 条正式路径和 30 个接受态原件均保留，不覆盖旧输出。

该历史 C0 比较的两网格差包含 Q1 边界插值差（离散平均 `1−a·h²/2`），不是单独的内部离散误差；`kr=0` 下 Hu 非零不证明 HuHu 正则项通过。研究来源和限制见[完整报告](HF4_C0_RESEARCH_INTEGRATION.md)。

### HF4-C1 保存证据的独立读回入口

当前选定的 10 条 C1 路径有 80 个状态（均匀 50、非均匀 30），80/120 位独立 HP 与几何门禁全部通过，选定范围共 2516 项独立检查；相关测试 173 项通过。另保留旧激活失败 run 的四态有效前缀，该 run 不通过。含前缀的历史统计为 84 态、2644 项检查，包含上述选定范围，不能重复相加。比较按[selection_v1.json](../hf4_c1_results/selection_v1.json)去重；阶段起点、原目标和插入态仍按存盘身份分别保存。

先读[物理协议](HF4_C1_PROTOCOL.md)、[激活修正](HF4_C1_ACTIVATION_REPAIR.md)与[精度补充说明](HF4_C1_PRECISION_AUDIT.md)。以下命令只读回已保存状态，并将新审计写到原证据目录以外的独立输出名；请先自行创建 `review_runs/` 目录，不要覆盖任何既有审计：

```powershell
& $hfPython hf_repo/scripts/audit_contact_c1.py --run hf4_c1_results/A0_h025_uniform_r2 --output review_runs/c1_a0_h025_readback_001.json --precision-amendment hf_repo/configs/contact_c1_precision_r2.json
```

`review_runs/` 是新建的本地复核目录，不属于发布原证据。也可以从任意其他 cwd 执行上述脚本，此时对脚本、run、output 和精度补充协议均使用本机实际绝对路径；无需重建历史盘符。审计会核对当前存盘状态、完整原目标、两数组继承、模型/代码哈希与相对来源链，不能只看顶层 `status`。

必须显式传入 [contact_c1_precision_r2.json](../hf_repo/configs/contact_c1_precision_r2.json)，才是 C1 精度补充采用的 80/120 位交叉核对；80 位仍为读出量权威，原物理协议和全部误差门槛保持不变。省略此参数仍走原 50/80 位合同，用于复现历史近零分量精度失败，**不能将默认命令当作最新验收入口**。原失败审计及其日志继续保留。

### 历史 C1 路径重放接口（非本轮执行计划）

以下仅记录历史接口与当时预算；不表示当前获准启动新 C1 路径。该历史求解使用 `run_contact_c1_r2_isolated.py --action solve`；独立审计使用另一个外壳 `audit_contact_c1_isolated.py` 并显式传精度补充。未来若另行准入新复验，须建立独立目录、预算和选定路径清单。原合同的单路径求解外部上限 700 秒、单阶段内部上限 300 秒、单路径独立审计外部上限 1200 秒；最多 10 条选定路径，累计求解预算 7000 秒。失败尝试也记录耗时，不删除旧回执来重置预算。

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

### 冻结 HF4-C2 v3 证据的独立读回入口

**本小节仅复读历史 v3：v3 C2 仅部分通过，v3 细网格路径仍为未通过。** 后来的 v4 单独补测已通过，见[v4 报告](HF4_C2_V4_RETEST_REPORT.md)，不覆盖这里的原失败。 三次新 FE 尝试均求解至 `d=0.5 mm`，其中 padding 的 19 态/589 项检查和 outer-free 的 19 态/570 项检查完整通过。细网格路径为 `NOT_PASS`：末态 `production_vs_hp80_total_force = 1.0943792164e-11 > 1e-11`；21 态中 20 态通过，651 项检查中 650 项通过，有效前缀止于 `d=0.4375 mm`，覆盖 6/7 原目标。三次尝试合计 59 态/58 态通过，1810 项检查/1809 项通过，包含上述子范围，不能重复相加。求解到达末目标不等于独立验收通过。

在 v3 收尾时停止了后续 FE；当时固定失败保存场的主差定位到强压缩背景单元的 F 浮点求和。原生产总力位级复现；保留生产 F、只提高本构/装配精度，误差仍约 `1.09438e-11`，而精确 split F 正确舍入为 binary64 后，诊断路径的误差约 `6.28152e-16`。这一历史分段诊断本身没有部署新 kernel、验证新一致切线或完成新路径；之后的候选与 v4 另有报告，原 v3 细网格仍为 `not_pass`。保留失败末态、原审计及外部回执，不调松门槛或覆盖旧失败。执行前 103 项测试与 17 项汇总回归分别通过，不把早期 62/94 项预检重复相加。证据见[C2 最终报告](HF4_C2_FINAL_REPORT.md)、[分段精度诊断](../hf4_c2_diagnostics/force_precision_001/summary.json)与[C2 证据入口](../hf4_c2_diagnostics/README.md)。

两条已通过新边界路径另有 206 项保存场检查和 22 项解析边积分检查通过。外底边自由场只有 44/48 条顶边满足整边材料压缩条件，远端出现保存场材料名义拉应力；不能把原四态的 144/144 全压缩推广到此任务，也不能把该名义应力直接解释为已验证真实接触压力。

[独立最终复核](../hf4_c2_diagnostics/independent_final_review.json)核对 420 个来源文件、93 个存盘状态（59 新增、34 基线）、71,000 个单元和 558 次分项重算，结论为证据完整性 `pass`、力学状态 `partial`。它重用保存的 HP 本构结果，不能代替新实现的完整力与一致切线验收，也没有取消细网格唯一失败。稳定 0.5.0 标签及 wheel 不变。

另保留了历史汇总清单的自引用缺陷，见[存储清单补充](../hf4_c2_diagnostics/summary_manifest_amendment_001/amendment.json)及[独立补充复核](../hf4_c2_diagnostics/summary_manifest_review.json)；科学数值和原文件未改。后续生成使用 [summarize_contact_c2_r2.py](../hf_repo/scripts/summarize_contact_c2_r2.py)，其 2 项存储测试与 103 项预检、17 项汇总测试分别计数。 该汇总脚本、原固定场精度诊断及原最终复核仍沿用完整历史来源链，缺少两份外部源码时不能在公开副本直接重跑；已保存结果可以读取，新公开数值入口只解决保存态重审，详见下述范围说明。

本小节历史执行协议为 [contact_c2_v3.json](../hf_repo/configs/contact_c2_v3.json)。v1/v2 都未执行新 FE，保留其配置、预检和修订说明；不要将 v2 的 `pre_execution_review.json` 当作最终执行准入。v3 的三条路径依次是 `padding_2p5`、`outer_free`、`mesh_h00625`。各路径既要满足求解/独立审计全部门禁，也要有未超时且退出码为 0 的外部回执以及完整来源、详情哈希链。

**公开数值读回与完整历史来源核验是两个入口。** 搬迁实测表明，原 `audit_contact_c2.py` 的 v3 admission 哈希链要求两份按既定出版范围排除的 MATLAB 编号源码；它们没有包含在主分支或 Release。缺少原件时，该完整审计会在 HP 求值前失败，历史源码不能伪造、静默跳过或被称为已核验。新机先用新增 [audit_contact_c2_readback.py](../hf_repo/scripts/audit_contact_c2_readback.py) 对公开数值证据复读。它限定那两条路径及精确 SHA，仍逐项核对其余 164 个 admission 输入和 33 个冻结实现，以及所有数值/控制器记录；如果外部来源存在但字节不匹配，同样失败。结果使用独立 schema 和 `numerical_pass` / `numerical_not_pass`，不替代完整来源资格，也不能传入继续执行门。详情、首次失败和新读回证据见[搬迁审计补充说明](HF4_C2_PORTABILITY_ADDENDUM.md)。 本机实际验证已复读上述两条路径共 40 个状态，科学详情 JSON 和 SHA 与原件全部一致；padding 保持通过，细网格保留唯一末态失败。新增入口有 21 项针对性测试记录，比较器有 12 项对照与反例检查，均不计作新的 FE 路径或原数值门禁。

C2 审计采用 80/120 位，80 位为测量权威，协议固定原物理参数与容差。它会在输入 run 内创建 `<output-stem>_states/`（标准 `audit.json` 对应 `audit_states/`）。**即使 `--output` 指向外部目录，也会向 run 写入详情；必须先建立独立复制树，不能直接在冻结原证据上复读。** 保留复制树内 `hf_repo/`、`hf4_c1_results/`、`hf4_c2_diagnostics/` 和 `docs/` 的相对关系，C2 来源门依赖已保存 C1 证据。

以下 PowerShell 示例从轻量克隆根建立一个尚不存在的同级复读树，并自动恢复 C2 及其 C1 来源依赖，再从副本之外的 cwd 读取第一条保存路径。`$hfPython` 使用前面已配置的环境；命令只独立核对存盘状态，不启动生产 FE：

```powershell
$originalRoot = (Get-Location).Path
$readbackRoot = Join-Path (Split-Path $originalRoot -Parent) 'hf-c2-readback-001'
& $hfPython tools/handoff.py prepare-replay --destination $readbackRoot --asset hf4-c2-s0-c2_runs-v1.zip
Push-Location (Split-Path $readbackRoot -Parent)
& $hfPython (Join-Path $readbackRoot 'tools/handoff.py') verify --asset hf4-c2-s0-c2_runs-v1.zip
& $hfPython (Join-Path $readbackRoot 'hf_repo/scripts/audit_contact_c2_readback.py') --run (Join-Path $readbackRoot 'hf4_c2_diagnostics/experiments/padding_2p5') --output (Join-Path $readbackRoot 'review_runs/c2_padding_readback_001.json') --protocol (Join-Path $readbackRoot 'hf_repo/configs/contact_c2_v3.json')
Pop-Location
```

副本、输出名和逐态详情目录均不得已经存在。公开数值入口的数值通过可返回退出码 0，但顶层状态为 `numerical_pass`；细网格应继续为 `numerical_not_pass` 并返回非零，不能当作意外中断重跑。重新审计后分别检查数值状态、历史来源未复核列表、完整目标库存、每态检查及 `input_and_helper_sha256` / `detail_output_sha256`，并与原审计逐字段比较。每态科学详情应保持相同字节；顶层 schema、范围、两项未验证来源和新增读回脚本绑定属于有意差异，时间、显示根目录与新输出路径单独记录。仅相同 `status` 不足以证明完整读回。为新机记录自己的环境和外部时间预算；同一 Windows 主机上的异目录复读只证明该环境下的搬迁/来源链可用，不是跨平台数值验收。

**读回 v3 的失败不应触发自动重跑 FE，也不能通过清理回执重置预算。** 原 v3 wrapper 和直接 runner 保留历史身份；P1 已另行实现并验收，稳定 F 候选与 v4 补测也已完成其记录范围，不能继续照抄旧的“P1 尚未实现”待办。当前仍存在三个制造场失败，默认内核未切换；v4 的一次求解与一次审计额度已使用。新的路径必须另有明确协议、预算与准入，公开 v3 数值读回不能授予这些资格。

历史 v3 预算为每条求解外部上限 700 秒、三条累计 2100 秒；每条独立审计最多 1200 秒、累计 3600 秒。它们只是历史合同，不自动成为新计划预算。任何失败、超时、来源变化或不完整目标应按本次预先定义的停止条件记录，不删除旧失败。稳定 0.5.0 wheel 不含 C2，应使用主分支源码环境阅读或开发扩展。

### v4 与稳定 F 的当前读取范围

先恢复本节开头列出的两项后续资产，再核对对应逐态结果、来源清单与[独立复核对照](HF4_C2_INDEPENDENT_RECONCILIATION_20260927.md)。资产无损恢复不会执行 FE，也不会重新计算 HP；如需重新数值审计，须在独立树中明确当前脚本/协议的来源要求和外部预算。v4 已有一次审计回执，不能覆盖、删除或用换名规避其单路径守卫。

公开 v3 读回的两项 MATLAB 来源例外不自动适用于其他工具。稳定 F 历史复算还使用明确的基线 `7fea2e4`；按[验证目录说明](../hf4_c2_stable_f_validation/README.md)建立独立基线并恢复 C1/C2 资产，不能用后来更新的仓库清单伪装旧基线。冻结运行自身的来源快照优先于后来变动的活动脚本。 完整恢复当前 main 只用于读取、文件身份校验和当前回归，不自动满足历史 stable-F driver 对 S0 提交、manifest 和资产索引的锁定；重跑历史 driver 必须使用其原冻结 S0/source-snapshot，不得改锁定哈希以适配 main。本轮整合不重跑该历史 driver。

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

先按 [CURRENT_STATUS](CURRENT_STATUS.md)确认现状与本次范围。固定场分段诊断、算术候选、JIT/AD修订及F系列都已实施并保留失败，详见[连续执行报告](HF4_C2_S0_PREPARATION_RESULT_20260928.md)。F-SELECT1已完成定向提取，可直接读74条小JSON，[结果](F_SELECT1_RESULT_20261001.md)明确56条身份与旧规则差距；不再把“读取旧128样本”作为待办或重跑已关闭卡。完整EOF/CRC/JSON与内部成本归因仍未取得。

当前优先功能步骤是新候选清晰的NumPy完整力入口：先给原unit近旋转场的八自由度材料/正则/总力，与已保存HP80/120原门参考比较并画力及误差；根据实际结果再接一个C1保存态全局组装、切线和小平衡路径，见[功能进度末节](PHYSICS_AND_FUNCTION_PROGRESS_20261001.md#可视化与最近一个功能步骤)。本轮C1十五态图和GIF是历史数组重绘，新克隆可直接查看；重绘源码带`--model/--result/--audit/--output`四参数，在任意目录显式提供相对恢复来源即可，不需原绝对工作目录。没有重新求解。Profiler是运行成本辅助，不是每个功能步骤的永久前置门。

原实验 runner 保留原机 Python、运行库 pins、路径及冻结身份。异机恢复证据不等于可以直接复跑旧卡；不要修改旧脚本/manifest 以适配新盘符。先恢复相对证据树并核 SHA；重新计算、读取 native gzip 或采集 profiler 须另定新环境、身份、预算与停止合同。原材料力、正则力、总力、导数及 native 接受门保持，不切换默认内核、不自动进入 HF5。缺少出版范围内排除的外部来源时，明确未核验范围，不伪造原件。

后续真实接触资格仍需围绕明确任务核查部分接触、释放/重入、模型与网格敏感性。负弱节点项不是已验证的负接触压力，材料名义应力也不是已经验证的真实接触压力；Aalpha 仅作诊断，TMC−Aalpha 不是纯接触误差。不要同时调整 alpha/gamma 追求净力吻合，也不能以三网格观察替代收敛证明。

后续开发统一在 main，流程见 [DEVELOPMENT_WORKFLOW](DEVELOPMENT_WORKFLOW.md)。每次继续记录总体目标、要做与已做、理由、效果、局限、代码/输入/输出哈希和资源成本；保留失败和修正因果链。HF5、LF 优化、1800 例 HF 标签与最终排名仍未实施，不因本次仓库整合自动开始。
