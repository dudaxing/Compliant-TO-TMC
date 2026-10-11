# M-INTEGRATE1：保存态续算进入默认入口与有限兼容回归

## 目标、依据与当前状态

整体目标是独立 HF 有限变形／TMC 前向评价：读取 LF 普通几何，在明确任务下计算实际变形、反力和可解释工件作用，供外部研究层比较。HF 不做优化，不调用 dmftd；MPM 暂不实现。main 与既定 origin 保持，science 0.5.0、原数值门和历史资格保持。

M-RESUME1 已按直接授权唯一执行并实际 PASS，发布 d45f6ee92d8a0d6ca740772a1762abdc691489fa。原 alpha=5e−7 的保存峰值013复核通过，首次下降 1.20→1.15 mm 通过；两个接受端点、3 PNG／一份2帧GIF已保存。原 M-ALPHA1 NOT_PASS 不改，两端点不代表连续卸载曲线或完整原路径通过。默认 hf_repo 尚未安装候选。

最近一步把已验证的续算合同变成默认 Mean/API/CLI 功能，并验证原零起点入口仍可用。此卡只准备；未安装、未 collect、未运行新测试／NPZ 解码／力学／HP／绘图。当前静审和实际运行严格分开，批准后才执行下面范围。

## 具体改变

唯一安装共11份逐字节绑定文件：7份生产源码（5个 hf_eval 模块、2个 CLI）和4份测试文件。其中6个现有文件修改、5个新文件；候选、原6份源码快照、目标映射及所有 SHA 在 protocol.json。正式源快照基线为 d45f6ee；本卡发布提交另由实际 source_publication_receipt 绑定。

续算生产源码继承 M-RESUME1。新差异仅 native_evaluate 在读取 saved defaults 前检查 settings 类型，用已有 TMCError/invalid_settings 保存 typed input error；两个 CLI 修正 saved 模式帮助／既有错误文字。有效输入的力核、NumPy切线、组装、Newton、Armijo、LU、回滚和原门不修改。零起点 None 选项仍 complete/full/tangent；saved 模式继承原父选项、原设置（新clock除外）和原绝对目标后缀，初始 K=None 必须复核锚点。此处不扩展为任意递归续算或 batch 保存态入口。

旧参考绑定当前源码身份。安装后 right2col/right4col 的旧参考重总结会按原门显示 source mismatch；已保存的 result/reference/qualified response 原字节保持，旧 HP 数值证据不改。这是来源身份迁移，不能写成旧 HP 数值失败。新测试明确覆盖 right4col 原正参考的当前源码不匹配，不修改旧 pins 或放宽门。M-REF2 的另一组 reference_sources 是否交集见独立来源审阅，不笼统否定全部历史参考。

## 唯一执行及资源

使用 HF 专用现有 Python 3.13 环境，依赖不升级。按以下顺序一次启动：

1. 核对直接人类批准、已发布／恢复 proof、协议、不可变来源和安装前6旧文件身份；5新文件必须不存在，run_001 必须不存在。
2. 将11个候选逐字节安装到默认 hf_repo，保存每一步实际完成记录，并核对完整默认运行包身份。旧6份源码已另存原字节和 Git 历史。
3. 默认已安装源码只运行 protocol.json 的25个精确 pytest 参数实例，-x 首错停止；实际收集的路径／item.name 顺序必须完全一致。禁止扩大到整套测试或历史 worker。
4. 保存 stdout、XML、pytest cache、临时小模型文件、收集列表、实际 HF 导入路径、原门结果及资源回执。终端后只读审阅、记录、普通提交／推送与独立恢复，不继续计算。

25项由19既有实例和6新实例组成：5 saved 合同、零起点 Mean/缓存、mechanical/chunk256、小 split、mock batch、8 API/旧JSON/CLI/显示链接；新增 settings dict/object 两例、CLI接线三例、旧参考来源迁移一例。具体选择和每项理由见 TEST_SCOPE_FINAL.md 与协议。

真实力学仅临时16单元／25节点／50DOF模型；单单元8DOF部分采用合成代数响应。旧原模型只读取普通JSON／已存在显示文件，不读取旧NPZ，不重建或求解原13440单元夹持器。小模型可以产生和读回新NPZ；NativeMean NumPy force/tangent aliases 分测试记录实际 started/completed，不宣称全部内核调用被监测，也不把 mock 次数当真实力学次数。

一次 tests180秒／helper300秒／outer360秒（最多约6分钟）、采样8GiB。历史约6秒的两组局部证据只作为预算依据，并非本次耗时保证。资源采用检查点与采样RSS，非OS硬内存限制；检测超限即写stop并等待已绑定检查点退出，清理实际时间如实记录，不通过force制造成功。

## 通过与停止

通过必须同时满足：一次11份安装完整、默认包身份一致、HF导入全部来自默认 hf_repo/src、25精确收集和25个call全部passed、无failed/error/skipped、所有原测试门保留、不可变原文件保持、各预算内且终端exit0/stopNone。新settings返回typed input error；来源迁移保持生产success但独立参考mismatch及资格false，旧qualified响应字节不变。

首个终端非成功／来源错配／资源触发即停，无重试、修复重跑、延期、force或自动回滚。安装／测试失败保留当时实际已安装字节和部分记录，明确 NOT_PASS；不得悄悄还原再说未执行。后续修复根据失败实证另行计划。这里的失败持有默认源码是本卡明确行为，原字节快照和 d45f6ee 可恢复，不自动删除新文件。

不新增原夹持路径、HP、JIT、图、物理定义、压力／有效夹持／稳定性／HF5资格；不改变原生产结果与父失败。代码功能通过只支持本卡默认集成和有限兼容范围，不代表整个项目完成。

## 可视化与后续

本步是入口集成，不生成额外物理图。人工核查复用 M-RESUME1 的实际 comparison.png、distances_forces.png、peak_fields.png 和2态GIF；数值及作用解释见其 RESULTS.md。峰／下降 R=0.37865427196005513／0.3470376815403639 N，下半工件 total Fy=0.12492121630032427／0.10671287553103108 N，均为原实际记录；工件弱式合力不升级为压力或合格夹持力。

成功后根据集成结果准备父子保存态的明确关联和同alpha参考需要；完整任务、可解释接触作用和一般LF输入仍按能力依赖逐步推进。不预先排一串计算卡、不重复长加载或扫alpha。若失败先只处理该实证问题。
