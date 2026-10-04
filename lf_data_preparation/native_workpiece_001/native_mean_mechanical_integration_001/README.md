# NumPy机械模式接入平均位移求解器

整体目标仍为独立HF真实加载、夹持与卸载。本新卡仅验证薄接口、原默认兼容、小型16单元连续加载卸载及缓存持久化。新response_mode=mechanical明确省略辅助material_energy，实际16字段和schema1.2；原complete默认、17字段、schema1.0/1.1和原控制器保持。没有NaN/0代填、捕错fallback或收敛门修改。

唯一unit窗口helper120秒/outer150秒/8GiB采样树内存；沿用已通过pytest计数hook与首错停止。原test_native_mean、test_native_cycle_observations和新focused测试各一次；小循环是临时16单元测试，不是3200单元工件平衡/HP资格。所有源码/测试绑定前后核对；辅助能量not_evaluated/qualified:false/field_present:false持久到结果与每接受态。保存不得重建模型或调用F/T。toy力学调用未单独计数，fullmodelHP与新物理工件路径均0。不安装依赖，不force、无同卡修复重试。

通过后才能开启另张coarse_square_cycle_004新0/.5/0连续真实工件路径卡，保原参数、门和预算，并同时捕首次F和T范围拒绝输入。F16已过不代表T25已解决；旧失败证据不改。完整目标、原因、实际效果、数值和图继续写既有NUMPY_FORCE_PROGRESS/CURRENT_STATUS及本卡RESULTS。
