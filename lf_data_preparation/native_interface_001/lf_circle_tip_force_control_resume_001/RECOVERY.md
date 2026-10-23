# 恢复与交接

本交付恢复的是**力控保存态续载源码已安装、小模型验证PASS且科学窗口关闭**的状态。与父目录[准备阶段](../lf_circle_tip_force_control_resume_preparation_001/PREPARATION.md)相比，实现状态已推进，准备文档中“未实施”是历史记录。

## 先读什么

1. 仓库`README.md`/`docs/CURRENT_STATUS.md`顶部和本目录[RESULTS.md](RESULTS.md)：目标、为何补此功能、实际数值、当前资格。
2. [USAGE.md](USAGE.md)和[人工页](inspection.html)：显式接口和唯一实际图。
3. [NEXT_STEPS.md](NEXT_STEPS.md)：下一步仅准备正式父态一个小载荷增量。
4. [原执行卡](../lf_circle_tip_force_control_resume_preparation_001/L-CTIPFRESUME1_CARD.md)、原INTERFACE_SPEC/VALIDATION_PLAN：原授权/门/资源。交付`approved_card.md`是原字节副本，其中相对规格链接按原准备目录上下文理解，不替代本目录实际状态。

## 数据与源码分布

正式main生产源码在`hf_repo/src/hf_eval`，本轮仅修改`split_guided_force.py`和`native_guided_force.py`，新增`native_guided_force_resume.py`；已测试的58份候选源码在原证据ZIP的`candidate/hf_repo/`中完整保存，当前安装三SHA见安装回执，另外55源不变。

本目录单独提供完整普通`validation_summary.json`、轻量实际执行汇总、pytest原日志/XML、四层监督/成员记录、helper/执行/安装/封存/rootQA/renderer回执、一次PNG，以及有限测试和runtime包装/SUP2、候选静审/冻结/实际结果复核。原科学缓存和拒绝反例树仅在原ZIP中，不散铺重复两套。原stdout/start等辅助记录可从原ZIP恢复；原成员清单完整保留，不重新封存。

`execution_evidence.zip`原包226成员、1441228 B，SHA256 `3fddd73e0f5b0927a94f45b5180f38e37019c10186673cdf0c5f2bafb95d43bb`。解包前先核SHA和成员清单；当前发布/恢复仅逐字节核对，不执行解包、科学读取或重算。

未来经授权恢复时，可将原包解至独立目录，保留`run_001/artifacts/real16/`结构，含`fixed_parent`、`relocated_fixed`、`prefix`、`child`、`grandchild`和选定state/模型/几何。普通JSON内盘符为执行时来源记录，不要编辑它们。新进程显式用当前`prefix/child/result.json`位置，必要时用`fixed_parent_result`传同字节`fixed_parent/result.json`当前路径；新output在两父树外。不要把历史runtime包装中的原绝对路径当跨机立即执行脚本；这些文件保留原执行身份，其职责是审查与复现计划依据。

## 环境与原路径

原执行环境Python3.13.6，numpy2.4.6、scipy1.17.1、matplotlib3.10.9、jax/jaxlib0.11.0、pytest9.1.1、psutil7.2.2；本轮CPU、四库线程cap16、8GiB采样。无需因本轮改依赖。审阅普通结果不需要导入HF；将来运行需按仓库依赖准备环境，异机环境并未在本轮验证。

- 正式仓库：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`
- origin保持`https://github.com/dudaxing/Compliant-TO-TMC.git`
- 作者记录：`D:/hf-native-workpiece-api-author-20261023/L_CTIPFRESUME1_preparation_001`
- 唯一运行：`D:/hfrs1_001/run_001`；原包及总回执：`D:/hfrs1_001`
- 同机异目录核对：`D:/hf-restore-20260930`

这些绝对路径是来源，不是理解代码或下一步所必需的固定工作目录。仓库内相对材料、原包及来源身份共同提供恢复上下文。发布回执将记录普通main提交和两目录新变化文件逐字节一致；它不代表另一台机器已安装依赖、实际复算或重授资格。

## 闭卡边界

唯一运行12PASS、7真实路径、37有限调用、一次图像QA、四层清理、三份安装和一次封存均已完成。本卡已关闭；不得把恢复核对当作测试/求解/显示窗口续期。后续真实r9续载按新准备结果和资源卡开展，保留旧低J、Hu作用及所有失败历史，不改变原参考/压力/有效夹持/释放/稳定性/HF5资格。
