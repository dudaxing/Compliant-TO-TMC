# L-BPREP1：普通 LF 来源清单到共同任务批量输入（待授权）

基线 main `8772efc36f682788c0f829f690403f3405706e4d`。本轮只读准备；L-TCOMP1 已关闭 PASS，不续用其窗口。来源、旧 seal／大小及成本见 [SOURCES.md](SOURCES.md)／[SOURCES.json](SOURCES.json)，拟用清单见 [source_manifest.example.json](source_manifest.example.json)。新代码和本卡执行尚未开始。

## 为什么做，以及本次完成什么

整体目标是读取独立 LF 的普通几何，在共同 HF 任务下计算可追溯的非线性响应，供外部研究层使用。当前三个设计已有保存态结果与可检查对照；现有单例 LF 准备和 native batch 评价各自存在，但缺少来源清单到批量输入的直接入口。

本卡只补这段功能：两个已验证的普通 LF v2 包→共同模板绑定→已有 `hf-native-batch-manifest-1.0`。输出准备状态表、来源和输出身份、可恢复清单，以及一张未变形双设计 PNG／人工检查页。成功意味着数据准备及现有 batch 元数据兼容，不表示模型兼容已重新计算、力学通过或 batch 已执行。

## 最小实现与接口合同

- 新增 `hf_repo/src/hf_eval/lf_native_batch_inputs.py` 的 `prepare_native_lf_batch_inputs(source_manifest_path, output_directory, *, repo_root=None)`，以及同名 CLI `hf_repo/scripts/prepare_native_lf_batch_inputs.py`（`--repo --manifest --output`）。新增一份 `hf_repo/tests/test_lf_native_batch_inputs.py`。只有三个全新文件，旧默认源码零修改，不复制控制器、力核或 batch 求解器。
- 来源 schema 为 `hf-native-lf-source-manifest-1.0`，共同 `task_template`、可选右补宽度、共享现有 `options`、有序 cases。每例非空唯一 label、source_descriptor，可选 expected_descriptor_sha256；路径相对显式 repo 根解析，不能依赖当前 cwd 或来源清单目录。输出内部文件用短数字目录，不用 label 拼路径。
- 首次准备前检查来源清单、标签、所有描述文件／可选 SHA、共同模板、共享 options 和新输出目录。复用原单例 `prepare_native_lf_inputs`，顺序各一次；不推断材料、工件、边界、载荷或网格，不优化、重采样、平滑、清理或补齐缺失来源。单例转换依其原合同校验同目录 design.npz。
- 首版新入口明确要求同一完整 grid 声明和物理几何声明；这是新准备入口的同网格合同，不改已有 batch 的能力或科学验收门。两例保 native h=0.5 mm／80×40 mm，仅明确右补4 mm／8列，分析域84×40 mm／shape_yx=[80,168]；不混入粗网格，也不自动升降采样。
- 共同任务只允许重绑 geometry 的两个身份字段；包括全部25目标、工件、材料、正则项和描述文本在内的其余模板字段逐值保持。options 仅复制原入口已支持的枚举；本次示例只声明 mechanical／chunk256／port_projection，不声明新求解时钟，也不授未来执行许可。
- 生成 `batch_manifest.json`，cases 使用原 batch 的 label／geometry／task／output 四字段，options 原样复制；准备路径、未来案例输出路径和未来 batch index 路径分别明确，未来评价目录必须仍不存在。仓库内路径写 repo 相对路径；仓库外保绝对路径并标注。调用现有 `native_batch._preflight` 一次作最终纯元数据兼容检查，绝不调用 `evaluate_native_batch` 或 `evaluate_native`。
- 准备 index 记录每例 not_run／preparing／success／not_pass、来源 LF 身份、实际输入与新输出 SHA、绑定 task、准备源码 epoch 和错误阶段；成功案例保持实际顺序。中途失败保已产生的目录与失败事实、剩余 not_run，不写可执行成功清单，不删除、不回滚或重试。顶层成功仅指 prepared，不继承旧力学或 HP 资格。

## 本次实际输入和允许读取

fine 使用 `lf_data_preparation/v2_adapter_001/inputs/gripper_native_fine/design.json` 及同目录 design.npz；wave 使用 `lf_data_preparation/native_interface_001/lf_third_input_001/run_001/sources/design.json` 及同目录 design.npz。两描述文件预期 SHA 分别为 `05aa71c6d3a77d4a221fe16453f06e7e19b45325a4aff824a951c95d4fd1a443`、`8d6629a966dab7411709c53c8c798cf6ee77c1a07446174aac9bca52162864f8`。

共同模板为 fine 既有准备 task.json：`lf_data_preparation/native_interface_001/lf_input_preparation_001/run_001/cases/gripper_native_fine/task.json`，2355B，raw SHA `49f04cc5184cefc9a33fc92faeb529e9d53bf7da7f7c3e57f5872cd27f0eb8b1`。两个既有准备任务去除 geometry 后精确相同；完整 grid／物理几何声明相同，已只读核对。

执行允许读这两份原 LF NPZ、本次生成的来源副本和 native／derived geometry NPZ，以及必要的普通模板／清单／新旧准备 JSON。旧准备 geometry NPZ、科学 gzip、ZIP、旧响应数组及旧媒体不读取；旧 seal 只作声明／身份对照。转换、右补和检查的实际数组读取次数据实记录，不把文件个数冒充读取次数。不依赖 Downloads、LF Python 环境或 dmftd 导入。原准备／任务校验可能导入和注册 JAX，不能称零 JAX 导入；没有构模、F／T／HP 或平衡计算调用。

## 唯一执行顺序、检查和显示

批准后可实现和作有限静态审阅，唯一启动前修正普通包装并冻结最终源码／协议字节。正式输出根为 `lf_data_preparation/native_interface_001/lf_batch_input_preparation_001/run_001`，测试使用专用短新目录；不触碰既有冻结结果。

1. 一次安装三个全新文件到默认 hf_repo；旧文件不覆盖。安装失败保真实部分安装。随后唯一运行六个有限 unittest 方法：①清单／空或重复标签无准备即拒绝；②任一来源 pin 错误在首次准备前拒绝；③既有输出拒绝并保 sentinel；④共享任务／options／路径原样进入成功 batch；⑤第二例准备异常保首例和 partial、第三例 not_run；⑥混合完整 grid 拒绝且不产生 ready 清单。反例用临时 JSON 与 mock 单例准备，不额外转换真实两包、不运行原全套测试或求解。
2. 测试全过才从无关 cwd 显式 repo／manifest／output，单次运行新 CLI，对两包各作一次真实准备。任何终端错误即停止后续准备、检查和绘图；常规期望反例由测试捕获，不计业务错误重试。
3. 两例均成功才核：新来源副本原字节保留；四个新 native masks 与两份原 LF masks 逐格对应（design 对 design_domain）；derived 原160列逐格保留，右8列仅 passive_void=1、其他三场为0。原生 geometry_id／右补 geometry_id 对照旧声明，task 除 geometry 逐值不变，全 grid 相同，现有 batch 元数据预检 PASS，未来求解目录未创建。旧 descriptor raw SHA 中含历史路径可变化，只绑定新的实际字节，不要求跨目录 descriptor raw SHA 相等。
4. 生成一张双面板 `prepared_inputs.png`：本次实际 derived solid masks、mm 坐标、端口／支撑／对称声明、固定方形工件的半域轮廓，区分原80 mm与新增4 mm介质域。标题明确“未变形输入声明，未构模／未施加载荷”；不画虚构变形或反力。输出 `REVIEW.md`，嵌入新图、两例状态和来源／task／batch 链接；最多一次对该新 PNG 作像素检查，不另重绘。
5. 原窗口内绑定输入／旧源码保持、新源码、全部新数据和图的实际 SHA／大小，生成检查记录与执行收据。失败仅在原窗口仍开放时允许一次实际 partial 封存，不继续功能步骤，不修复重跑。

完成门是六项有限测试全部通过、两例新准备成功、掩码精确保持、同网格／共同任务／现有 batch preflight 通过、未来评价目录不存在、图／页面可检查及实际证据封存。科学十五门不改、不重算。机械／独参／压力／有效夹持／释放／稳定性／正式标签／排名／HF5 均不升级。

## 资源、停止和交付

唯一 helper180秒／outer240秒、采样1GiB（1073741824B）。测试、安装、CLI、检查、绘图、封存均含 helper 总窗口；采用既有 supervisor 清理合同，无 force、延期或第二次启动。原 L-PREP1 实测 helper7.94s／outer21.48s／树峰166240256B，L-THIRD1 实测17.13s／18.72s／198811648B；本卡规模有限，1GiB有依据，但采样不是OS硬限，旧成本不是本次保证。

批准覆盖本卡最小实现／静态审阅、三个全新文件安装、唯一有限测试／两包真实准备／单图及页面、执行后普通 JSON 源审阅、结果记录、沿现有六个恢复入口更新、普通 main 提交推送与增量封存／异地恢复核对。安装后失败保实际字节，无自动回滚；不得以额外审计再跑准备、测试、预检或重画。发布只核新数据原窗口 seal／stat及普通源码／JSON，不在关闭窗口后重读旧或新科学数组／媒体。

下一步只由本卡结果决定：若准备通过，再规划有限的真实 batch 消费验证及其资源；若失败，先报告最小功能缺口。任何后续求解都须新范围和预算，不能把本卡清单视为求解许可。整体 HF 目标保持未完成。
