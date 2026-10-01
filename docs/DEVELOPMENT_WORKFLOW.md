# 后续主干开发流程

2026-09-27，依据用户“后续开发将全部在 main 主干上进行”及本轮合并/删除授权。远程唯一目标为 `https://github.com/dudaxing/Compliant-TO-TMC.git`，开发分支为 `main`。阶段冻结使用提交、标签、协议和证据清单表达，不再保留长期开发分支。

## 工作目录与更新

本机正式仓库根为 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`，源码在该根下的 `hf_repo/`。外层旧 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/hf_repo/` 及旧工作树只作历史来源保留，不在那里继续实施或推送。其他电脑克隆到任意路径后，在克隆根工作。

开始一轮工作先检查工作树、分支与 origin：

```text
git status --short
git branch --show-current
git remote get-url origin
git fetch origin
git log --oneline --left-right main...origin/main
```

工作树清洁且没有分叉时，可用 `git pull --ff-only origin main` 更新。发现他人的未提交工作或远端新提交先核对；不以 reset、clean、强推或整目录覆盖消除差异。并行审阅可划分文件所有权，最终按小批次整合到 main，避免两个工作区各自产生竞争主干。

## 科学开发的提交边界

2026-10-01用户补充的工作原则：以实现可用功能为主，每步产生可检查的数值、力或实际变形图，依据本步结果规划下一步。优先清晰的响应/组装/平衡入口，代码保持简洁易读；证据记录使用实际输入、输出、结果及必要验证，避免为低影响文件/绘图改变增加重复门禁或泛化防御包装。Profiler和运行异常诊断是辅助，不得替代物理验证或成为所有功能推进的永久前置链。用户已明确的数值门、资源与冻结边界保持，范围改变须具体说明。

1. 开始前读 [CURRENT_STATUS](CURRENT_STATUS.md)，写明本次问题、假设、改动边界、验证方法、输出与资源预算。既有路径额度不自动续期。
2. 源码和小测试直接在 main 的工作树修改。独立数值实验先冻结本次源码/输入/协议身份，使用未存在的运行目录；保留失败尝试和完整回执。
3. 只运行与改动相称的检查。真实求解、保存态 HP 审计和纯合成测试分别计数；重叠状态不重复当作物理覆盖。结果用实际命令、收集清单、退出码和输出身份支撑。
4. 更新当前入口与本次独立报告，说明目标、改动、理由、效果和局限。旧冻结文件不覆盖；解释修正另作勘误并链接原文。
5. 提交前复核来源绑定和交付清单。当前仓库清单应覆盖本次受管文件，不能用删除清单项掩盖缺失，或改旧 freeze 使新代码冒充旧实现。历史清单保留版本。
6. 合理粒度提交到 main，核对远端尖端再用普通 `git push origin main`。发布大证据使用不可变的版本化 Release 与哈希索引；上传后验证远端资产和独立恢复。禁止以强推改写科学历史。

交付清单使用仓库工具重建。先明确暂存本轮预期文件，再生成清单、暂存清单并验证：

```text
git add <本轮预期文件>
python tools/build_delivery_manifest.py --worktree .
git add handoff/repository_manifest.json
python tools/handoff.py verify
```

生成工具只读取 Git 已跟踪的路径，新文件须先暂存；恢复到工作树但未受 Git 管理的大证据不会被意外纳入轻量清单。生成后再改动任何受管文件，应重新生成并校验，不能沿用修改前的清单。

## 证据与资产

`python tools/handoff.py verify` 校验当前轻量树；`fetch-evidence --asset NAME` 与 `verify --asset NAME` 按索引恢复并验证指定证据及依赖；`verify --full` 要求全部声明资产。缺资产不能记作完整验证通过。

审计脚本可能在输入 run 创建详情，需通过 `prepare-replay` 或按完整相对结构建立独立复制树。原值、原失败、split 两个权威数组、HP 字符串及源身份永久保留；`u_display` 只用于显示。

后续资产 `hf4-c2-followup-evidence-v1` 与历史/S0 资产分开版本化。旧文档中的本机归档位置是来源记录，实际下载和成员集合以当前资产索引为准。文件无损恢复不等同于异机力学再验收。

## 分支清理与历史访问

本轮只删除最终 main 已保存其全部提交的远程开发分支。删除前核对实际尖端与 main 的祖先关系；若分支在审查后新增提交则先暂停该分支删除。保留所有稳定/证据标签与 Release，不做 Git 历史压缩。实际删除结果见[主干整合报告](MAIN_CONSOLIDATION_REPORT_20260927.md)。

已合入的归档提交继续存在于 main 历史，需要历史版本时以明确提交在独立只读检出中查看。远程删分支不授权删除本地未跟踪文件、数值数据或仍被进程使用的工作树；本地清理应另行核对和归档。
