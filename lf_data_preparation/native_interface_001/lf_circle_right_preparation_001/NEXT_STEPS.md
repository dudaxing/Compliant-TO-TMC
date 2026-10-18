# L-CRIGHT1后的功能计划

当前未变形检查：PASS。Prepare a separately authorized zero-start load_only [0,.25,.5] mm pilot and circle-aware resident saved-state views; preserve r9/(74,40), all other physics, settings and original production gates.

1. 短行程若获授权，创建明确新task：load_only，[0,0.25,0.50]mm，input.target0.50，独立身份；仅这些路径/说明字段区别于本轮保存的原17目标任务，r9/(74,40)及其余物理条件保持。默认HF入口和圆形保存态显示已具备，优先复用，不安装新力核或切线。
2. 一次从零使用现有evaluate_native及原数值门。沿用原非clock设置：残差1e-9、平均约束1e-10、全局力平衡1e-6、固定位移8e-11mm；候选资源controller1800、显示600、helper2700/outer2760秒、采样64GiB、四库16，原viewer内部8GiB保留。内部原回溯/二分允许；首个终端错误停止，保真实partial，无外部重试/修复重跑/延期/force。此处是计划，没有打开新计算窗口。
3. 成功后一次保存态显示：实际×1变形/动画、输入反力与工件有符号总力和材料/Hu分量、最近及同tip距离、收敛图；显示新布置与未变形参考，检查右侧1mm介质条带和x84边界附近J/Hu。不得将工件节点反力或Hu主导总力直接认定为表面压力或有效夹持。
4. 依据实际变形、J、反力/方向、右侧介质和收敛，再决定继续到0.75、调整域宽或定位异常。不预设必须接触，不因短程未接触而放宽门或盲目加行程。此新布置需自己的保存态参考，旧圆心71的HP不转授；只在具体不确定性需要时安排HP。

本轮已完成记录与未变形可视化；尚未启动任何短行程、独立参考或力学求解。整体项目尚未完成压力、有效夹持、自由释放、稳定性或HF5资格。
