# L-CTIPFLOAD1 薄力控 API 候选

2026-10-23。仅候选编写与 AST 检查；本记录不表示已经运行、安装或通过力控验证。

候选：`D:/hfl1_001/candidate/hf_repo/src/hf_eval/native_guided_force.py`。正式仓库旧文件保持原字节。

`evaluate_native_guided_force` 保留准备卡的签名，直接复用原 `native_probe._admit` 准入与 `_plain` 转换。来源必须是完整成功 fixed_rigid/load_only 父的最后原目标峰；只迁移两份 split 字段与有符号 R，不读取旧力或矩阵冒充本次计算。API 只收有限、严格递增的绝对半模型 N 目标，不收预期 q；力设置类型与时限、输出新目录在求解前核查。

新低层 `solve_split_guided_force_path` 接收原 model/port/settings、显式 N 设置和原 body 合同。API 新鲜 NumPy 力与原非对称切线的 assembler 包装保留调用计数，full/chunk256 和 complete/mechanical 继承父绑定；本卡实际小模型只测 full，不因此给 chunk256 新资格。原父 `initial_guess` 作为 `parent_initial_guess` 保存，新控制器明确采用规格内的 `guided_reduced_tangent` 预测，不把其行为误写成原位移端口预测。首态 P0 是否与原非零预载平衡由新鲜 F/T 检查决定，API 不替换 P0 或修复原态。

每个接受态只保存其最后一次 F/T 缓存。保存前确认缓存状态身份、fresh 首态 split/R 位身份且检查 1、原刚体/零支撑 8e-11 mm 与全局 1e-6 门。保存 split、全局与局部 total/material/Hu 力、J/Hu/F、实际 positions，以及未知 q、P、g/尺度/绝对门、均值/free/global 门、原请求与二分分类。保存不再调用 F/T，原父结果不写。

账本显式列 `body_axial_load_N=[P,0]`、`body_y_guide_N`、排除 body 的 `zero_support_N`、去 body-x 的 `merged_prescribed_N`、`input_actuator_N`、`output_spring_N` 及闭合向量。没有旧 body-x 处方驱动力，body-y 与背景重叠仅计一次；不分配虚构节点 P，另存二维广义外载合量。ON-body 组件依旧等于负内部节点弱力合量。

结果 schema 为 `hf-native-guided-force-1.0`，包含父来源、独立 force_task、原设置/新 N 设置、全部低层 Newton/trial/linear/失败历史、缓存身份及调用计数。model 普通元数据和 accepted 实际坐标便于纯 JSON viewer 绘制实际 ×1 变形，不需要在 viewer 解码科学缓存。数值 partial 如实记录，不升格 HP、压力、有效夹持、释放、稳定性或 HF5 资格。

未改 native_response、CLI、默认固定工件入口、旧 probe 或原 kernel/tangent/SUP2。静审、唯一有界验证、显示及通过后两新模块安装由 root 统一冻结与控制。
