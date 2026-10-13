LFBRIDGE：现有输入／任务与最近功能缺口（源码只读）

结论：LF v2转换器和前向API已经实现，最近不应再造它们。当前真正缺的是一份公共、可追溯的data-only准备入口，把普通LF包及显式物理profile转换为几何绑定task／case清单，供现有evaluate_native或同任务batch使用。HF5=false不是代码不存在的证据。

已存在：lf_v2.py:54–166验证dmftd.hf_export.v2的四bool数组、80×40mm原native网格、下半/t20、两类固定端口和区间语义，无重采样/阈值/cleanup，保源JSON/NPZ和LF→HF身份映射。native_map.py:58–105读取其hf-geometry-1.0，build_native_project:189–283接显式绑定task；native_evaluate.py:23–121完成一次求解／保存／摘要，native_batch.py:93–151、154–214已有同任务顺序运输和首非成功停止。当前没有native_geometry.py/native_task.py，真实几何入口是native_map，task验证在native_project:30–139。

可复用的派生：analysis_domain.py:15–87已显式增加右passive_void列；nested_geometry.py:12–60已有2×2整数细分。它们不优化、不给资格，产生新几何身份并记录parent。新增bridge不自动依据LF analysis_mesh做细分，不自动padding；native意味着所提供HF几何网格，不必意味着原LF网格。当前84×40mm任务的4mm右域须作为明确派生记录，端口仍在原物理x80，不能移到新边界x84。

最小新入口建议：复用convert_lf_v2，按显式域政策复用right-padding（首版无需加入细分），仅将选定profile的task_id与geometry_id/descriptor_sha绑定到新HF descriptor，保存source→converted→derived→task及eval options/paths清单。task schema不塞新的bridge字段，额外 provenance留在case/index。准备动作不调用evaluate、不构造求解模型、不优化或import/install/call dmftd。已经转换的HF包仍可走原API，无需改变默认solver/reader。

沿用目前探索性gripper policy即可作为首个明确profile：native网格、下半、E1/nu.3/plane_strain/t20、gamma1e-6、alpha5e-7/Lr80、固定square(71,40)/side18、free output/noauxspring、原平均输入25目标至1.20再回零、显式top背景与4mm右域；这只是任务模板，不把旧保存态或参考资格迁到新设计。1mm与0.5mm LF各保原网格；源solid已二值，不再生成阈值。若是灰度rho或其它LF schema应明确拒绝或由上游导出已定义binary包，不能silent材料SIMP映射。

须明确并记录的政策：LF native_mesh/cell_mm而非analysis_mesh；无snap的轴向grid-node端口和reference trapezoid平均；support/entity symmetry只solid_incident，LF背景只provenance、applied背景仅由task决定；工件只能existing fixed square/circle native阶梯且落sourcepassive_void、不碰原机制/支撑/端口；材料参数来自task，alpha与gamma分开且Lr物理长度不随格改；mechanical/chunk256/port_projection作为当前使用过的显式options，避免零起点默认complete/full/tangent被暗中采用。同batch不能混inverter/gripper或不同物理profile，现batch只比较声明，不授同设计网格收敛或排名。

现docs/HF5计划顶部第13行已经说明v2适配等功能已实施；历史第43行标题、H2/H3待确认文字不是当前全局功能状态。当前仍缺一般输入边界/任意形状、自由体/摩擦、连续压力／有效夹持与广泛设计独立验证；已有circle构造不等于完整circle路径/参考资格。

下一步只需冻结这个小data bridge源码和单一profile/源包范围，之后分别验收准备输出与调用现API的最小真实前向例。转换NPZ、测试或前向数值动作均是新阶段，不能借已关闭M-PREF1窗口；本审没有指定新的资源额度、运行预算或资格门。

本次仅普通PY/MD/任务JSON读、SHA及AST；未读任何科学数组/媒体/gzip/CSV、未导入模块或运行测试/HP/solve/plot/dmftd，未修改正式代码。原15参考门和历史无需重审。
