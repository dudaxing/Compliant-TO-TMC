# F-SELECT1：批准范围与实际结果

2026-10-01，用户明确“批准 F-SELECT1”，并要求从物理与功能层面说明开发进度、提供可人工检查的可视化。批准依据为 [F-SELECT1 十项合同](F_STREAM1_READONLY_FOLLOWUP_20260930.md#最小候选卡-f-select1建议合同未执行)；该文中的“未执行”是提出时的历史状态。本页记录新卡，不回写旧冻结根或修改旧失败。

本卡只从已有 gzip 重建已接纳的四百万事件前缀并选择记录。严格解析 end=453,448,982；同一 reader 最多返回453,720,232 bytes，最后271,250 bytes只计数/哈希，不做 UTF8/JSON 解释。不求 EOF/CRC，不解 XPlane，不运行 profiler、力学、AD 或 HP，不扩大原执行名称规则。

停编作者为 [run_saved_trace_selection.py](../hf_repo/scripts/run_saved_trace_selection.py)，43,915 bytes，SHA256 `8b6eb180fab17cbb8813d6d5a64e24c491eca8ec389958fc9055c784f65b6666`。两路文本/AST静审通过，新根在启动前不存在，作者期未 import/运行新 helper 或控制。新16组27子例将在P0执行；静态小 fixture 字节记账37,614 bytes，不把静审写成运行通过。

原严格解析器128,256 bytes/SHA `1250415b2084cd4d52aaae2a0f996f3a905e513cbb8e1b6085ac15c143569174`及SUP1 15,838 bytes/SHA `9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32`保持。新helper直接复用原父监督/失败关账函数，配置新协议、阶段、来源和保存验收接口；实际core加载位置另记，父函数的driver定位变量不被当作解析器源。原82例仅继承未变解码/framing/count/capacity部分的既有证据；原前128采样明确替换为新选择接口，不能继承为新接口通过。原源码整数门实际为绝对十进制256位数字，旧卡“256位整数”文字不精确；执行沿用原严格源码，没有改变该门。

唯一运行根为 `hf4_c2_stable_f_validation/prefix_select_001`。一次连续300秒/4GiB，P0/P1/P3含清理15/240/15秒，活动9.75/234.75/9.75秒，shared30秒、封存前25秒、末绑定保留5秒；原SUP1清理预算及首错停止/无重试保持。

## 实际运行与效果

唯一窗口exit0，`prefix_selection_complete`，终端真实总钟151.7630085秒、shared2.0559593秒；P0/P1/P3为2.2809654/145.2653221/2.1607623秒，最大采样进程树RSS81,494,016 bytes（77.71875 MiB）。三个原SUP1阶段normal_exit/0、cleanup_verified=true，first_stop=null，无失败关闭、修复或重试。[执行回执](../hf4_c2_stable_f_validation/prefix_select_001/execution_receipt.json)是写时快照（151.4395867秒/shared1.7325375秒），终端总钟与该快照分别记录，不冒称同一时点。

[新控制](../hf4_c2_stable_f_validation/prefix_select_001/results/prepare/controls.json)实际16组27子例通过，fixture37,614 bytes；旧82例没有重新执行。[计数](../hf4_c2_stable_f_validation/prefix_select_001/results/stream/count.json)记录原gzip一次打开、一个直接reader、496次有界read、reader/raw各一次close。返回453,720,232 bytes的SHA及同流旧268,435,457-byte SHA均精确匹配；严格解析止于453,448,982，4,000,000完整事件端点通过，271,250 bytes未解释。第4,000,001个单元没有解码或接纳，也没有额外读取求EOF。

[选择件](../hf4_c2_stable_f_validation/prefix_select_001/results/stream/selection.json)保留70个必需唯一事件（56直接module、5标记、9metadata）与4个诊断事件，共74条、累计留存文本3,705 bytes。六个通用名称无条件桶只有`ThunkExecutor::Execute`为4，其余5个为0；四条均不带原规则所需的直接module字段，因此旧generic+direct仍为0。这里的sample_set_complete=true只指本前缀内这六个名称的四条诊断样本全保留，不表示四百万事件或全流均保留。

56条直接module记录实际是28种名称各两次：19种名称含`fusion`，其余为`wrapped_add*`、`wrapped_broadcast`与`copy.54/55`。每条保存`hlo_module=jit_reused`及相同文字的`hlo_op`，但这些名称均不在原执行区域allowlist。五标记保存了真实`graph/phase/protocol/run_id`。本轮解决的是“56条到底是谁、其他字段有无冲突”，不能把这些名称记录自动升级为有效执行区域、producer成本或完整候选force证据。

EOF、CRC/ISIZE、UTF8 final、完整JSON、全文大小/SHA均未获得；五科学/force/native/XPlane资格保持false，原44 producer/26 fusion observations保持null。旧F-TRACE2/F-STREAM1失败及门槛保持。原统计的十项字段交叉核对通过，来源pre/post与冻结件绑定以[最终绑定](../hf4_c2_stable_f_validation/prefix_select_001/receipt_binding.json)及[保存验收](../hf4_c2_stable_f_validation/prefix_select_001/diagnostic_verification.json)为准；关闭后只读复核另记下文。

物理/功能说明与历史保存态图另见 [开发进度](PHYSICS_AND_FUNCTION_PROGRESS_20261001.md)。该部分只是数组重绘，不混算为本卡或新增物理验证。诊断是辅助工作；接下来的最小功能闭环为新候选 NumPy 完整力输出、原门参考比较、一个C1保存态全局组装、切线与平衡控制，按实际结果逐步推进。

## 关闭后核对与交付

两路独立只读后审通过：29条绑定、38条payload实际bytes/SHA闭合，44文件与恰六排除一致；14来源为13复制件与1原gzip引用，总25,994,476 bytes，pre/post live与aux逐件核对通过。19项runtime与3项installed-only身份通过，仅作原声明范围身份，不推定完整DLL闭包。全根1,835,369 bytes，其中generated413,289 bytes、最大生成单件285,413 bytes；冻稿与原core/SUP1保持原SHA。后审未执行helper、控制、原gzip解压或新科学计算。

7个真实步骤、20个事件顺序闭合；三个阶段日志实际0 bytes。末次request/return均850,727，offset452,869,505至453,720,232，496次nonempty/0次empty，最大request1MiB。保存入口余量233.1678815秒≥20秒；不把该入口余量伪造为另一个首read精确时间戳。留存的74条typed字段一致、单元SHA格式与位置有效；未在关闭后再解压原件核单元原文。

ledger、receipt、binding前与终端总钟分别151.2746801、151.4395867、151.6006930、151.7630085秒；[resources](../hf4_c2_stable_f_validation/prefix_select_001/resources.json)仅preseal P0/P1，含清理的P3与总钟以最终回执/终端记录为准。原SUP1只授予其Job清理合同，不把它改称SUP2同实例句柄证明。[selection.svg](../hf4_c2_stable_f_validation/prefix_select_001/selection.svg)是诊断摘要，XML核对通过；实际物理图和动画已渲染查看，详见功能进度文档。

交付时真实遇到Windows Git拒绝`aux`保留名组件：`git add`及`hash-object`报告ENOENT，但普通/namespace标准库与Windows读取同175字符路径成功，`core.longpaths=true`，原冻件保持。为避免新机克隆要求关闭Git路径保护，沿用现有证据分层：31个非aux文件留在main；13个aux来源复制件由版本化资产恢复。完整44文件封入`hf4-fselect1-prefix-select-20261001-v1.zip`（216,915 bytes，SHA `917bb1f9056f2d85bf6056e0322b833c030a9422e998c6f920f441226e6d1fac`），索引仅追加新项、旧19项不变，包装成员逐件核对通过，见[包装回执](../handoff/f_select1_20261001/packaging_receipt.json)。发布与公开恢复结果以随后实际回执为准。

异机可直接阅读选择件和图。完整冻结来源使用`python tools/handoff.py fetch-evidence --asset hf4-fselect1-prefix-select-20261001-v1.zip`，会恢复索引声明的原来源依赖；仅阅读无需下载整个依赖链。重新绘图时按元数据中的相对来源与SHA恢复旧C1数组，不复制旧绝对路径。原大证据按[移交指南](RESUME_DEVELOPMENT.md)恢复。任何重跑须新身份/目录/资源合同，不删除已关闭根重置额度。

**公开交付已验证。** 代码/结果/图先以`273e6209e18ebaef2e9ce89d4a0836f44997f27d`推送main；[版本化资产](https://github.com/dudaxing/Compliant-TO-TMC/releases/tag/hf4-fselect1-evidence-20261001-v1)已公开、server digest与包SHA相同。首次发布URLError的[原回执](../handoff/f_select1_20261001/publication_receipt.json)保留；另一个[恢复发布回执](../handoff/f_select1_20261001/publication_receipt_002.json)记录成功，其最初untagged字段是draft实际观测，最终取published_url与正式tag。

原公开异目录克隆`D:/hf-restore-20260930`已ff至273e620，普通Git检出31件成功、轻量3881件身份通过。新资产从此前不存在的缓存项经无认证公开URL实际下载，未用作者ZIP；旧九项缓存是前轮公开下载原件。本次恢复/验证十资产依赖闭包4157成员，包括新44件及13个AUX来源，实际约63.1098秒，见[公开恢复回执](../handoff/f_select1_20261001/public_restore_receipt.json)。只验证该依赖闭包，不把它称为全部二十资产或新物理验收。最终关闭文档/回执再随main提交，原科学冻结根不变。
