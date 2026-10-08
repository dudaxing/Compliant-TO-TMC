# B-VIEW2：两例真实保存态图卡候选

本卡承接用户已授权的结果可视化。root 在两份新 V2 参考实际终态核验后签署、冻结一次独立图阶段。当前文件是外部 source-only 候选；未安装、冻结或运行，没有未来 PASS。

控制目录为 `lf_data_preparation/native_interface_001/batch_saved_view_v2_001`。输入是原 `batch_forward_001/run_001/{canonical,native_fine}/result.json` 与 `batch_reference_v2_001/run_001/audit/{canonical,native_fine}/qualified_summary.json`。两例必须各自原生产 PASS、四个真实接受态、V2 worker 和原 F3 outer launch 均 PASS、N4 的 2N=8 次新 HP 完整返回；原 raw summary 与 qualified summary SHA、所有输入绑定、35 份独立参考冻结源均一致。V1 失败卡不提供资格。

复制已经审过的 worker `14f761eaa8bc40a9daa75a6412a1d00f2320725b339a9ee7bd0384fb29dea5ad` 与 adapter `a9c1b5f0dd1b3e326b773d3af4efdb5a17cddbb509133428b1e567540f23a341`，保持原算法与透明适配证据。原 F3 `launch_pose.py` 原字节放在本 stage 根。同深度保持其仓库根路径解释正确。协议有显式 `reference_run`；每例生产、参考和图目录独立对应。

执行一次连续 view phase，whole-helper 120 秒、outer 150 秒、采样 RSS 8 GiB。计时包括导入、保存缓存读取、原图函数、CSV/metadata/manifest、保存态 response 导出和最终哈希；最终回执写出由 outer 覆盖。不借参考或旧图卡的时间窗口，不重试或 force。首次异常、输入/source 变化、时限或采样内存超限立即停止并保留已写产物。

每例 PNG 与 GIF 只使用四个实际保存的接受态。主图真实几何 ×1，位移补图明确标 ×40；GIF 四个实际帧，不插值。显示原缓存的输入反力、输出位移、J、收敛数据与实际力箭头；没有新 F/T、HP、求解、构模或几何内核。两原生网格属于不同设计，不据此授予网格收敛、HF5、接触、夹持、压力或排名资格。

输出保留在原生产 run：`view/{canonical,native_fine}`、`view/manifest.json`、`view_execution_receipt.json` 与两份新增 `qualified_response_{label}.json`。原 `result.json`、原 `response.json`、原 raw summary 和所有原生产/参考文件保持原 SHA。成功需要两例实际帧数/身份各自对账、manifest 与新 response 对应、资源范围满足，worker 与 outer 的实际终态均 PASS。

此候选不会自行调用 installer 或 launcher。root 待实际两参考终态证据齐全后启用本卡；无需向用户重复申请已有可视化授权。
