# L-CTIPFREAL1：恢复与审查入口

本交付记录正式r9／mean.50 mm／P0→P1力控任务的实际PASS，整体项目与历史限制见[结果说明](RESULTS.md)和仓库[当前状态](../../../docs/CURRENT_STATUS.md)。不用原工作目录也可先看[人工页](inspection.html)、[轻摘要](result_summary.json)、[比较](comparison.json)、[接口用法](USAGE.md)及[下一步](NEXT_STEPS.md)。

|资料|位置与用途|
|---|---|
|本轮实际数值原件|`execution/execution_evidence.zip`：唯一窗口封存的59成员、13984762B原包，完整新force/result、两态split／field缓存、运行记录及原wrapper；不是发布时重封。|
|原包身份|`execution/EVIDENCE_MANIFEST.json`列59个原成员SHA；`execution/seal_receipt.json`给包SHA／封存时点／资源。解压前先核13984762B和SHA7452459b…cc81158。完整64位SHA以该JSON为准。|
|便于浏览的原字节副本|`view/`五PNG、两帧GIF、geometry_metrics／renderer receipt；`comparison.json`、`execution/`普通回执／日志／监督，与原包相应成员保持字节同一。发布没有再打开图像或科学缓存。|
|实际源代码|`wrapper/`六份执行源码，含未改SUP2；`protocol.json`绑定75份当时文件；`source_binding.json`、`observer_binding.json`保原来源／字段和固定观察ID。|
|授权与过程|`approved_card.md`保准备版原字节，实际用户批准见`authorization.json`；`author/`保存冻结、静审、闭卡及物理审阅。预启动false声明代表当时事实，不能误读为最终未执行。|
|已有父／参考科学依赖|本次直接只读`D:/hlo1_001/run_001/parent_fixed`与`probe_low`树。其已发布原始证据位于[LOW1交付目录](../lf_circle_tip_low_probe_001/RESULTS.md)的`execution_evidence.zip`及成员清单；本次原包有意不重复旧科学包。|

换机若只审查结果，不需要运行Python或解压科学档。若后续需要复算／延伸，需在新任务中核LOW1原包身份、选择性恢复完整父模型的source_geometry、model和selected accepted002 split，以及对照probe接受态，按源清单保留目录关系；再恢复本轮原包。原包中的科学结果路径与协议绝对D盘路径是**当时来源记录**，不是任意机器上开箱即运行的承诺。新位置应通过明确的新准备包重绑定，不能直接修改封存协议或覆盖旧结果。

Windows3.13.6环境中使用本机`.venv-handoff`，NumPy2.4.6／SciPy1.17.1／JAX-JAXlib0.11.0／matplotlib3.10.9／psutil7.2.2／Pillow12.3.0；生产代码位于仓库`hf_repo/src/hf_eval`，正式origin始终为`https://github.com/dudaxing/Compliant-TO-TMC.git`，后续开发在main。此清单是已使用环境记录，不是依赖升级建议。

旧wrapper含唯一启动和已存在目录的停止约束；本卡窗口已经关闭，**不要通过复制旧launcher或删除旧输出来重开**。后续新执行应使用新目录／来源绑定／资源窗口，保留历史PASS和失败。当前force API尚不支持以force结果为父续算或卸载，不能用固定父resume入口冒接新schema。

本次发布恢复检查仅为同一计算机的`D:/hf-restore-20260930`异目录：核main远端HEAD、工作树干净、Git索引／仓库清单一致及本轮变化文件原字节相等。它不等于已做异机环境验证、重新解压科学包、数值复算或新HP。原大包与旧科学payload在发布核对中不解码。
