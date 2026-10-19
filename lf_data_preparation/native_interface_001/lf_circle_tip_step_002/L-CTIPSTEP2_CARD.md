# L-CTIPSTEP2：最右尖端对向圆形工件，保存态.75→.90 mm

用户已明确批准本卡实现并执行。整体目标是独立HF读取LF结构，逐步完成可恢复的大变形/TMC接近、接触后作用力和卸载功能。本轮只延伸一个加载目标，观察更强介质压缩下尖端接近、反力与收敛。

来源为L-CTIPSTEP1成功末态accepted1/global3，d=.75 mm、state SHA998ebca7375050a870e4466139732524206b151c0e7b16418f90ecc0a8d856a4、signed R=.13029373126695096 N。原parent是合法suffix[.50,.75]，完整task为[0,.25,.50,.75]；原parent/祖先continuation与成功/失败历史保持。新task仅append.90、input.target改.90并更新四项说明身份。现有evaluate_native(saved_result=parent,selected_state_index=1,extend_path=True)复核fresh F/T锚并执行suffix[.75,.90]；实际接受态N随原内部二分全部保存，不硬锁N=2、不重放旧前缀。

r9 mm、圆心(80,40) mm固定ux/uy，右域界92、Lr80，92×40mm下半域/h.5/厚20，E1MPa/nu.3/plane strain/gamma1e-6/alpha5e-7及所有支撑、端口、对称保持。顶部uy到92；右ux及非顶uy自由。原mechanical/chunk256/port_projection、非clock设置、residual1e-9、原平均约束系数1e-10及scale、global balance1e-6、fixed split8e-11mm、正J，maxchecks25/backtracks12/bisections4/mininc.00625保持。

唯一controller1800s，显示/收敛/表页共享600s，helper2700/outer2760s（最多46min），采样64GiB、四库线程配置上限16，pure viewer原8GiB子限。配置不等于实测16核使用；CPU后端不改。唯一旧科学输入为parent snapshot source_geometry/geometry.npz四掩码和accepted/001/state.npz的lift/fluctuation；执行前仅producer seal/stat，唯一helper内才hash/decode，不读旧model/force/tangent/matrix数组或媒体。无新tests/HP/default修改/安装。

成功后一次干净pure viewer读取新model27字段及每态split2/forces16，1+2N归档、27+18N字段；输出4PNG和实际N帧GIF，原收敛投影另1PNG，共5PNG，根Agent每新PNG最多一次像素检查，GIF不额外解码。显示实际×1变形（完整结构仅视觉镜像、力不加倍）、R/qout、下半工件material/Hu/total有符号Fx/Fy、tip及完整Q1最近距离/见证/交叉/重叠、分区J/Hu、right reference x89..92的480cells J/Green/Hu/位置及split位移与收敛。tip按唯一reference(80,30)找节点，右条带动态选resident原参考ID，外角位移与tip距离分列。

独立静审通过、最终字节冻结后唯一启动，首终端错误停止后续科学/显示并保真实partial；仅原窗口开放时允许部分seal。无外部重试、修复重跑、延期、force、回滚、删除。原内部回溯/二分允许。含目的/实现/理由/实际效果/取舍/恢复说明、main普通推送及异路径local Git恢复核对；origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

保留suffix语义，task_target_executed/full_original/full_extended均不升级，new_peak/segment仅本段。无当前布局独参、连续压力、有效夹持、完整卸载/自由释放、稳定性、网格/域宽收敛或HF5资格。根据实际结果再计划，本卡不授后续更大行程。
