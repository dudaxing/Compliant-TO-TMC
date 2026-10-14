# L-LINK1：选定保存态参考接入公共摘要 API

2026-10-15（Asia/Seoul）。准备基线 main `909f8acee95279e449e09961fd4fe68fed9d688f`，origin `https://github.com/dudaxing/Compliant-TO-TMC.git`。本卡源准备不等于直接授权、测试通过、默认安装或实际关联；只在新的直接人工批准后执行一次。

## 功能目标与依据

整体目标是 HF 独立读取 LF 普通几何，在同一明确任务下给出非线性／TMC 响应、固定工件弱式合力和实际保存变形，供外部研究层比较。HF 不优化、不调用 dmftd；MPM 尚未实现。

L-FWD1 已从零完成25目标0→1.20→0 mm及25保存态、3PNG／25帧GIF。L-REF1 已对 accepted13/loading1.20 和 accepted16/unloading1.05 完成4次HP80／120及原十五门，main909f8ac已推送和独立目录恢复核对。原参考、结果及资格均保持。

实际公共入口 `hf_repo/src/hf_eval/native_response.py::summarize_saved_native_result` 当前强制参考覆盖全部接受态，因而会把这个真实2／25参考记为 mismatch。仅附加旁路索引不能修复公共 API 的这个功能缺口。本卡只修订 `_reference` 的保存元数据匹配，保留公共签名、原所有物理响应函数与数值门。

## 具体工作与唯一顺序

1. 核当前授权、发布源、不可变输入、默认摘要源码旧字节和候选来源；新输出 `run_001` 必须不存在。
2. 对候选运行固定16个标准库 metadata-only unittest 方法，failfast。源码规划包含23次私有 `_reference` 调用（含不提供参考），这不是23个真实HF试验；不执行pytest、NumPy或旧真实路径测试。测试上限60秒且包含在总helper180秒内，实际计数／错误保存。
3. 测试全部通过后，对真实 L-FWD1 result、L-REF1 summary、原完整 view manifest 调用候选的公共摘要函数一次。核 `matched_partial`、`selected_reference_pass=true`、实际 indices13／16、覆盖2／25、`accepted_reference_pass=false` 和 `full_path_reference_pass=false`；原完整生产路径和原 producer flags 保持。完整参考的旧含义仍要求全部态通过。
4. 原公共 writer 一次写 `linked_response.json`，一次写 `light_index.json`。链接同result/model/task/geometry、两态参考、参考误差普通JSON、原3PNG／25帧GIF与原参考误差PNG，共五媒体；路径以恢复后的仓库根为基准，保原编号13／16而非0／1。
5. 只有上述测试、真实关联、写入和资源检查全部通过，才将已测试且实际调用的候选原字节复制一次至默认 `hf_repo/src/hf_eval/native_response.py`。只安装这一个元数据源码；不再次调用API，不修改力核、切线、组装、控制器、版本、几何、任务或原结果。失败保实际部分输出及已发生的安装，不自动回滚。

候选只改变参考匹配与显式覆盖字段：严格整数、唯一且在范围内的 index；按生产 `states[index]` 核相同 stateSHA、目标、原pass／2HP及汇总2M计数；若记录陈述选定indices／生产态数则须一致。原result/model输入绑定、参考source字节和全单元／DOF覆盖声明仍须匹配。只有覆盖全部25态才可取得原 accepted/full-path参考通过字段，子集不授完整路径资格。

## 输入与读取范围

- 生产：`../lf_forward_001/run_001/lf_fine_forward/result.json`、model/model.json、原response.json。
- 参考：`../lf_reference_001/run_001/reference/summary.json`、两份accepted_013／016普通摘要及原execution/lifecycle/protocol等必要普通来源。
- 视图：`../lf_forward_001/run_001/view/view.json`及lf_fine_forward/summary.json。
- 13／16 SHA分别为 `d23cdaee0a02e727726ef8789c902494f3f0ec09256fdeed74c0086cd3169e96`、`29910bc07e26bd7d7e5f7bb113c58094c2cff27ea544a71b2c523e1078265e14`。同result SHA `bfb711b5b948e188eb275f201f4a6dcca210687598a928d8772fa6359aa8888b`；全部精确路径和绑定以本stage的protocol为准。
- 普通JSON／声明源码可以读取、SHA核对；五份已保存媒体仅在本新窗口内读取原始字节／SHA以核身份。原 `_views` 本身会raw-hash四份生产媒体；外层／helper的前后输入核对也读绑定媒体，不声称五份只打开一次。
- 不读取NPZ／科学gzip／CSV的内容或头部，不解压／数组解码，不进行图片／GIF解码、像素检查或补画。源准备和闭窗交付只继承已封存媒体身份＋stat，不做新媒体hash。
- source_before_installation单独保默认旧SHA规则，不混入安装后仍须原字节不变的bindings。安装后的默认SHA必须等于本卡候选SHA；其余不可变输入保持。

## 核对、输出与可视化

16个方法覆盖无参考、原完整参考、生产未完成、真实13／16子集、空／缺失／错误计数、HP／状态、重复／bool／越界index、错误stateSHA／目标／result／model输入／source／覆盖声明及explicit selection/population。它们只验证摘要元数据匹配，不宣称物理或新独立参考通过；实际公共摘要一次另行核真实完整25态出处、物理数值和原flags。

新输出为测试记录／普通fixture、linked_response、light_index、封闭执行回执／stdout。原五份可视化通过路径索引提供人工检查：加载／卸载曲线、距离与力、峰值场、25帧实际变形、两态参考误差。没有新变形或新误差图。

峰值原输入反力0.24365768726879147 N、下半工件总Fy0.058511988483089014 N；卸载1.05 mm原反力0.1700172631705196 N、总Fy0.007747408704194823 N。只复制原普通结果，不重新计算；工件值是固定体弱式合力，含材料与Hu，不能当作连续压力或正式有效夹持力。

## 有界额度与停止

一次helper180秒／outer240秒，采样RSS8GiB；测试子阶段最多60秒且计入helper，总跨度包括输入核对、模块加载、测试、一次摘要、写入、安装、封存和回执。clock从程序入口计时，采样／合作停止不是OS硬上限，outer必须等同一child实际退出。

首个终端错误停止后续步骤，无外部重试、修复重跑、延期、force、回滚或删除。helper或outer结束后不继续读科学／媒体或补身份；保存真实partial和失败。原已关闭L-FWD1／L-REF1窗口不能作为本卡额度，剩余墙钟不授权新工作。

## 完成与范围

必须取得实际一次执行终态、16方法全通过／实际计数、一次真实summary及response／index各一次、两态身份与2／25明确覆盖、旧输入不变、仅一个默认源码原字节安装以及资源／封存通过。独立审阅区分源静态检查、测试实际执行和真实保存数据关联；推送与恢复另以实际回执支撑。

本卡不新增构模、F／T、HP、平衡求解、数学参考或正式标签，不升级全25态参考、所有切线列、压力、有效夹持、自由工件释放、稳定性、一般LF／HF5或MPM资格。原十五科学门由L-REF1证据承担，不放宽、不补算。本步完成后才根据实际结果决定下一项能力，后续粗路线仍为外部研究层消费、跨几何比较及必要物理验证。
