# L-CTIPSTEP1：最右尖端对向圆形工件，保存态.50→.75 mm

用户已明确批准实现并执行本卡。整体目标是独立HF读取LF结构，逐步完成大变形第三介质接触的加载/卸载分析与可用接口；本轮只延伸一个加载目标，以观察尖端接近、反力及右侧介质，不重做旧加载前缀。

源为L-CTIPPILOT1成功末态accepted2/global2，d=.50mm、state SHA c8f41107026000f09d395eb7a091ce6501b532b0a8d69210b22a94d55e8c8392、signed R=.08602790333542189N。新task保完整[0,.25,.50]前缀并仅追加.75，input.target改.75，四个说明metadata据实更新；现有evaluate_native(saved_result=parent, selected_state_index=2, extend_path=True)复核fresh F/T锚并执行suffix[.50,.75]。实际接受态N随原内部二分，全部保存，不硬锁N=2。

r9mm、圆心(80,40)mm固定ux/uy，92×40mm下半域、h.5、厚20mm；E1MPa、nu.3、plane strain、gamma1e-6、alpha5e-7、Lr80mm及全部支撑/端口/对称不变。顶部uy到92，右ux及非顶uy自由。仅原parent source_geometry NPZ四掩码及accepted/002/state.npz的lift/fluctuation为旧科学输入；执行前只继承producer seal/stat，唯一helper内才hash/decode，不读取旧model/force/tangent/matrix数组或媒体。

保持原mechanical/chunk256/port_projection、全部非clock设置与门：relative residual1e-9，平均约束系数1e-10及原scale，global balance1e-6，固定split求和8e-11mm、正J；maxchecks25/backtracks12/bisections4/mininc.00625。controller1800s、全部显示共享600s、helper2700/outer2760s，采样64GiB、四库线程上限16、原viewer内部8GiB；不更改CPU后端，不承诺实用16核或性能加速。

成功后一次干净pure viewer读取新model27fields及每态split2/forces16，1+2N归档、27+18N字段，生成4PNG及实际N帧GIF；一次原收敛投影另生成1PNG，共5PNG。根Agent各新PNG最多一次像素检查，GIF不额外解码。显示实际×1、R/qout、lower-half material/Hu/total有符号工件弱力、tip和整体无符号Q1最近距离及见证/交叉/重叠记录、分区J/Hu、right reference x89..92共480cell的J/Green/Hu与split位移及收敛。tip按唯一reference(80,30)找节点；条带从resident模型动态选，不硬码节点ID。镜像仅用于整体结构显示，力不自动翻倍；底右外角位移与tip距离分列。

独立全源静审通过、字节冻结后唯一启动；首终端错误停止后续科学/显示，保真实partial，仅原窗口开放时允许部分seal。无外部重试、修复重跑、延期、force、回滚、删除、新tests/HP或默认HF源码修改/安装。原内部回溯/二分允许。含实现/理由/实际效果/取舍/恢复记录、main普通推送与恢复核对。

必须保留suffix语义：parent success不改，task_target_executed及full_original/full_extended完成不升级，按原API报告new_peak/segment等。无新布局独参、压力、有效夹持、完整循环/自由释放、稳定性、网格/域宽收敛或HF5资格。根据实际结果再建议下一步，本卡不自动推进更大行程。
