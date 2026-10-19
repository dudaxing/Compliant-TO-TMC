# L-CTIPSTEP7：保存态1.02→1.03 mm（用户已批准，尚未执行）

直接授权：用户已回复“批准按L-CTIPSTEP7计划实施并执行”，对应main 2891b5a中STEP6/NEXT_STEPS的具体计划和本次批准问题。新阶段独立窗口，不沿用已关闭的STEP6授权。

整体目标是独立HF读取普通LF结构数据，在一致任务下计算可恢复的大变形/TMC响应，供外部研究层比较；HF不优化、不调用dmftd、不引入MPM。本轮只追加一个加载目标，以0.01 mm增量分辨接近区的实际变形、作用力与介质压缩，不修改默认HF力学代码。

来源为L-CTIPSTEP6成功末态accepted1/global8、d=1.02 mm，state SHA b96e0475af5e5e83b2ef8d1ca97436ff6be8468581068748c91606b8b646c5f2、signed R=0.1831436048338394 N。全部嵌套parent_continuation及原历史保持。完整task保[0,.25,.50,.75,.90,.95,.98,1.00,1.02]前缀，只append1.03、input.target改1.03并更新四项说明身份；既有evaluate_native(saved_result=parent,selected_state_index=1,extend_path=True)先fresh F/T复核SHA/R和平衡，再执行suffix[1.02,1.03]。预期global8/9、child0/1，不重放旧前缀、不移植旧力/切线/矩阵。

r9 mm、圆心(80,40) mm固定ux/uy、右域界92 mm、Lr80 mm保持；92×40 mm下半域、h.5、厚20，E1 MPa、nu.3、plane strain、gamma1e-6、alpha5e-7、原支撑/端口/对称不变。顶部uy延至92，右ux及非顶uy自由。mechanical/chunk256/port_projection与全部非clock设置不变；原residual1e-9、平均约束系数1e-10及原scale、global balance1e-6、fixed split8e-11 mm、正J，maxchecks25/backtracks12/bisections4/mininc.00625保持，不新增J/Hu/位移单调门。

原minimum_increment=0.00625 mm保持。0.01 mm首次尝试允许；若该尝试失败，半分0.005 mm低于原限值，将按原控制器规则终端停止，不能依赖内部二分兜底，不降低最小增量或另开外部重试。

唯一controller1800s、全部显示/收敛/表页共享600s、helper2700/outer2760s（最多46min），采样64 GiB、四库线程配置上限16，pure viewer原8 GiB子限；不把配置当作实测16核利用率。旧科学输入只限parent source_geometry/geometry.npz四掩码和accepted/001/state.npz的lift/fluctuation；执行前仅继承producer seal/stat，唯一helper内才hash/decode，不读旧model/force/tangent/matrix数组或媒体。无新tests、HP或默认HF修改/安装。

成功后一次干净pure viewer读取新model27字段及每态split2/forces16，1+2N归档、27+18N字段；输出4PNG和实际N帧GIF，原收敛投影另1PNG，共5PNG。root每新PNG最多一次像素检查，不额外解码GIF。显示实际×1变形、R/qout、下半工件material/Hu/total有符号Fx/Fy、tip及完整Q1最近距离/见证/交叉/重叠、实体/介质J/Hu、右侧固定参考x89..92全部480cells的J/Green/Hu与位置/split位移、原收敛记录。tip按唯一reference(80,30)查节点；镜像仅供完整结构显示、力不加倍；右条带位移极值节点逐态保留，不硬套旧位置。统计覆盖80行，空间图上部裁剪另注明。

最终源码/批准/输入独立静审通过并字节冻结后唯一启动。首终端错误停后续科学/显示并保真实partial；仅原窗口开放时允许部分seal；无外部重试、修复重跑、延期、force、回滚或删除。原回溯和二分的限制保持。包含整体目标、实现/理由/实际效果、取舍及恢复说明、main普通推送与异路径local Git恢复核对，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

task_target_executed/full_original/full_extended不升级，new_peak/segment只指本段；保原父成功和失败历史。正距离及包含Hu的工件弱力不单独构成接触证明；无当前布局独立HP、连续压力、有效夹持、完整卸载/自由释放、稳定性、网格/域宽收敛或HF5资格。依据真实结果决定下一目标或局部诊断，本卡不自动开放后续窗口。
