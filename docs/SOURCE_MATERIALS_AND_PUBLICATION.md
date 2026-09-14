# 来源资料、公开内容及历史文件身份

本仓库按用户于 2026-09-14 的要求发布当前状态与从开始至今的说明，目标是在另一台计算机上脱离原工作目录继续开发。此次整理没有运行新的力学路径，没有改变生产内核或冻结物理任务。科学版本仍为 0.5.0，原提交 `b1334bb6a83ba9a0efab7bdba7bd39722146f024`；新增的 GitHub 交接提交仅组织目录、文档、普通证据和迁移工具。

## 仓库和附件包含什么

主分支保存全部 31 份既有根 `docs/` 说明及新增接续文档、原启动任务书、七次开发 Git 历史、当前完整 HF 包/测试/锁定依赖、395 个几何数据文件、HF1 完整结果、HF4 原版和修正版的完整普通证据。HF2、HF2 修正及 HF3 的摘要、图、测试 XML、执行脚本、门禁和资源日志也在主分支。

历史大型数组及较大 HP JSON 按阶段放入 [hf-history-0.5.0 Release](https://github.com/dudaxing/Compliant-TO-TMC/releases/tag/hf-history-0.5.0)，其文件名、大小、SHA256 和恢复路径全部列于 [evidence_assets.json](../handoff/evidence_assets.json)。运行 `python tools/handoff.py fetch-evidence` 可恢复它们；若本地存在不同内容则拒绝覆盖。当前原样 HF4 修正交付 ZIP 作为独立附件下载到 `deliverables/`，不把整包解压覆盖当前导航文件。

旧 HF1/HF2/HF3 和 HF4 部分成果 ZIP 内有大量嵌套重复。本次上传其历史发布清单与全部必要普通数据/说明，不重复上传这些旧 ZIP；其旧报告中的 ZIP 链接因此属于历史记录。需要数值证据时使用新 Release 恢复命令。旧 ZIP 的原名、大小和 hash 留在 `deliverables/*release_manifest.json`，不伪造为新整理附件的 hash。

`handoff/repository_manifest.json` 校验本次主分支文件。`HF3_CONTENT_MANIFEST.json`、`HF4_CONTENT_MANIFEST.json`、`HF4_REPAIR_CONTENT_MANIFEST.json` 和 `verify_delivery.py` 分别属于旧交付快照；新的根 README/迁移文档不受旧清单定义。新机应运行 `tools/handoff.py verify`，不能把旧整包校验器的失败解释为当前几何或数值文件被修改。

## 原资料及取得方式

原文件身份保存在 [reference_inputs/manifest.json](../reference_inputs/manifest.json)。其中的 Windows 路径只是原机来源记录，不作为程序输入定位方法。

| 原资料 | 用途与公开位置 |
|---|---|
| `hf_start_brief.txt` | [原用户启动任务书](../reference_inputs/hf_start_brief.txt)，保持原字节；作为历史需求背景，末尾“先做 HF0”不是当前待执行阶段。最新任务以接续指南和状态总览为准。 |
| Frederiksen, Sigmund, Ferrari (2026), *A Matlab code for analysis and topology optimization with Third Medium Contact* | DOI [10.1007/s00158-026-04341-7](https://doi.org/10.1007/s00158-026-04341-7)；二维 Q1 基准与代码对账依据。原 PDF 不随本仓库上传。 |
| Frederiksen, Dalklint, Sigmund, Poulios (2025), *Improved third medium formulation for 3D topology optimization with contact* | DOI [10.1016/j.cma.2024.117595](https://doi.org/10.1016/j.cma.2024.117595)；模型比较/升级依据。原 PDF 不随本仓库上传。 |
| `TMC_code.zip` | [DTU TopOpt 作者发布页](https://www.topopt.mek.dtu.dk/apps-and-software/top_thirdmediumcontact)。基准对应用户提供的 ZIP hash；在线文件可能变动，重新取得时应先比 hash，不能静默替换参考版本。 |
| `Diversity-TO-Compliant-O-main (6).zip` / `lf_snapshot.zip` | 用户提供的 LF 快照。几何与来源档案已保存为独立普通数据；HF 正向开发无需重新取得整个 LF 工程。 |

HF0 已核查：上传 TMC 源码含教育用途与保留权利声明，没有另附通用开源许可。论文开放获取不自动授权原代码重新许可。因此此次公开副本不复制原 MATLAB 八个文件、它们的逐行文本副本、论文全文/页面图片、原 LF 完整源工程和原输入 ZIP/PDF。原代码源清单、hash、已生成参考数值、独立核查报告和函数/公式对照仍保留；需要重新运行 MATLAB 参考生成时，须取得匹配原 hash 的资料并确认其使用条件。

`reference_validation/matlab/source/`、历史 MATLAB `.m` 驱动、`hf0_audit/lf/snapshot/`、`hf0_audit/tmc/TMC_code/`、论文全文提取等路径在部分旧说明中仍可见。本次发布不把它们伪装为随附文件；这些路径不能成为 HF 安装、测试或运行依赖。MATLAB 生成的普通 JSON/NPZ/MAT 数值结果可以通过主分支和 Release 读取，`.mat` 结果不是源代码。

`geometry_dataset/archive/source_members/` 中没有 Python/MATLAB 等可执行源码，395 个文件均为普通数组、几何、图、来源和说明，原 NOTICE/LICENSE 作为来源说明保留。`lf_data_preparation/` 中的自编一次性导出工具放在 HF 包之外；仅供历史追溯，不属于 HF 必需测试或运行入口。

此次不为项目或第三方材料增设新的开源许可证。项目自身发布许可仍由仓库所有者决定；已有文件中的第三方声明保持原样。

## 文档修正说明

历史 `HF4_REPAIR_EVIDENCE_README.md` 将开发工具依赖笼统指向 `requirements.lock`。迁移执行时应遵循新的 [RESUME_DEVELOPMENT.md](RESUME_DEVELOPMENT.md)：runtime 安装 lock，pytest/build/psutil 等开发工具安装 `requirements-dev.txt`。保留历史字节，同时在新入口明确正确命令。

历史审计存档中的绝对路径键、资源预算累计与外部目录日志必须保持；迁移不通过改写旧文件来冒充原审计的续算。要复算时建立新的输出、审计与预算记录。附带文档中的指令性措辞是其历史上下文，不会自动触发新一轮计算或额外授权。
