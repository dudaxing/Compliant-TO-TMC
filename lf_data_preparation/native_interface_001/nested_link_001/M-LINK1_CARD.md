# M-LINK1：同身份参考／图件关联摘要与轻交付索引

**来源已准备；本卡尚未获执行授权、尚未执行。** 基线是已推送并恢复验收的 main `d092532d2789b70d440edc29688b6351efce7f34`；本阶段只准备可审阅来源。独立最终静审、来源发布与恢复通过后，才可请求一次新的执行资源授权。

整体目标仍是独立 HF 有限变形／TMC 前向评估。当前细网格完整加载／卸载的 24 保存态已求解，M-REF2 的 48／48 HP 已通过，M-VIEW1 图件已产生。这一步把已有结果与证据连到一份新增关联摘要／轻索引，让用户与另一台计算机直接检查数值、结构变形及后续开发依据，不重复计算或绘图。

## 最小功能与输出

直接复用 `hf_eval.native_response.summarize_saved_native_result` 和 `write_native_response`。输入为同一 M-CYCLE1 `result.json`、M-REF2 完整 `summary.json`、M-VIEW1 原 `view.json`。现有 API 核对全部 24 态、已有 48 HP 记录、result／model／task 身份及 12 条参考 Python 来源 SHA；薄层只要求最终 reference 和 views 均 matched，full_path_reference_pass 成立，不镜像其逐态检查。

只新增：

- `run_001/linked_response.json`：沿用现有保存摘要 schema，记录本次同身份参考与图件关联。
- `run_001/delivery_index.json`：用 repo-relative 路径及 SHA 关联新增 response、原 result／response、当前 reference、原 raw view／phase、4 PNG／24 帧 GIF 和原四份表。
- `run_001/execution_receipt.json`：实际一次调用／写入、输入绑定及采样资源记录。

原 raw view 提供 3 PNG＋GIF；第四张粗细网格 PNG 来自原 `phase_view.json` 的 `comparison.image`。索引核对原 phase SHA，不复制、改写或补写关闭的 view／phase 目录。四份原表是 `fixed_square/states.csv`、`fixed_square/nodes.csv`、`mesh_comparison.csv`、`mesh_comparison.json`。全部索引文件引用相对仓库根，换目录恢复后可解析。不会读取或扫描大型 HP 档案与 NPZ。

## 固定输入和资格边界

协议绑定 31 份既有元数据／来源／图件／表、3 份本卡来源以及 1 份已关闭的 M-REF2 发布／恢复收据，共 35 份原字节。原 result、model、task、response、raw view、phase 和图件都保持不变。原 `response.json` 的 reference／views not_provided 和 producer false flags 保持历史事实；新增关联不会回填原生产资格。

M-REF2 的独立解析切线资格仍限原 5 节点 PORT 方向（固定 lift、deltaR=0）；完整 CSC 组装身份不等于所有切线列的独立 HP 资格。已有图件为保存态诊断及两网格敏感性。本卡不增加压力、有效夹持、网格／域收敛、全列切线、HF5 或新应力／能量资格。现有 Piola P 只含材料项；节点弱式力含 Hu，不能直接称压力或总表面力。后续再定义材料＋Hu 在物理表面、对称切面与角点上的表面力。

## 一次资源与停止合同

授权后只执行一次：helper 180 秒、outer 240 秒、采样 RSS 8 GiB；原通用 launcher 保持字节一致。新输出目录必须不存在。首个错误即关闭，禁止重试、修复重跑、延期或 force。停止为协作检查，RSS 为采样值，非 OS 硬内存上限；本卡没有成本探测。最后 checkpoint 在最终输入 SHA 复查后、成功收据构造前；异常由原 try／except 写 not_pass，实际 outer 终态另确认退出与停止事实。

新增保存摘要调用为 1、response 写入为 1、索引写入为 1。新增求解／模型／F／T／HP／JIT／LF／observer／render 为 0，这是固定调用路径依据，非动态 hooks 监控。验收直接用既有 API matched 合同、35 份输入前后 SHA、原 phase 图件 SHA 和唯一执行终态，不增加镜像科学测试。

## 授权后的唯一启动命令

工作目录为仓库根；以下命令在本卡获得单独授权前不得执行：

```powershell
& 'D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe' -X utf8 -B lf_data_preparation/native_interface_001/nested_link_001/launch_link.py link --protocol lf_data_preparation/native_interface_001/nested_link_001/protocol.json
```

准备依据及三份预审／两次修正原字节位于 `author/`。预审通过是来源准备依据，不替代本次正式最终静审或执行授权。
