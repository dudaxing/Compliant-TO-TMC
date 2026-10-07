<!-- front proposal 2026-10-07; dynamic results require final actual records -->

## 从任意目录继续 main 开发

项目目标是把 LF/N4 的几何与研究任务交给独立 HF 正向评估器，获得有限变形、力、TMC 作用和加载—卸载的可解释结果，再推进优化接口。当前是固定方体中心 `(71,40)` mm、边长 `18` mm、对称下半体 `[62,80]×[31,40]` mm、24 目标 `0→1.2→0` mm 的探索。右面贴到分析域边界；原 x71/side16 是对照，两个后续失败工况保留原终态。

当前可接续事实：{{CURRENT_VERIFIED_RESULT}}

{{ACTUAL_VISUAL_LINKS}}

可选 `initial_guess="port_projection"` 已通过 15 项小模型测试，保留默认初猜行为、真实 KKT LU 和原 Newton／J 门。新大模型的状态、HP 资格与图仅按上方最终记录判断。先读 [本轮报告](WORKPIECE_ENLARGEMENT_20261007.md) 和 [当前状态](CURRENT_STATUS.md)，核对峰值加载与共同加载位移的实际图和力。

下面的 PowerShell 命令从所选新目录恢复文件，路径不要求与原电脑一致：

```powershell
$repoRoot = Join-Path (Get-Location).Path 'Compliant-TO-TMC'
git clone --branch main https://github.com/dudaxing/Compliant-TO-TMC.git $repoRoot
git -C $repoRoot switch main
python (Join-Path $repoRoot 'tools/handoff.py') verify
```

证据大资产按实际移交清单恢复：`python (Join-Path $repoRoot 'tools/handoff.py') fetch-evidence`，随后同入口 `verify --full`。文件校验用于核对来源；另机数值实验使用新任务与新输出目录，原已关闭卡作为历史保留。

当前源码包要求 Python 3.13。新建环境并使用仓库锁定依赖；无需复制原机器虚拟环境：

```powershell
py -3.13 -m venv (Join-Path $repoRoot '.venv-hf')
$hfPython = Join-Path $repoRoot '.venv-hf/Scripts/python.exe'
& $hfPython -m pip install --require-hashes -r (Join-Path $repoRoot 'hf_repo/requirements.lock')
& $hfPython -m pip install -r (Join-Path $repoRoot 'hf_repo/requirements-dev.txt')
& $hfPython -m pip install --no-deps --no-build-isolation -e (Join-Path $repoRoot 'hf_repo')
```

开发只在 `main`，origin 保持上述仓库。下一项功能按本轮真实力／间隙／变形确定：接触与压力定义、匹配网格和 gamma、圆体或自由工件、HF5/LF-N4 接口。`q_out` 是 `(80,28/29/30)` mm 的加权竖向输出端口；钳尖间隙另测。输入 `R_input`、单侧工件 `Fy`、双侧 `2 abs(Fy)` 和全体净力各自报告，避免混读。

---

## 历史记录

以下保留此前完整文字与命令；其“当前”“下一步”对应当时阶段。现在的结论和开发顺序以上方及本轮报告为准。

