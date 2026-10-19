# L-CTIPSTEP3：0.90→0.95 mm保存态延伸（候选，待授权）

整体目标是独立HF只读取LF结构数据，在一致物理任务下计算可恢复的大变形/TMC响应，供外部研究层比较；HF不做优化、不调用dmftd、不引入MPM。本轮只准备下一步可审查候选，不修改默认HF实现，不启动求解、HP、测试、冻结、提交或推送。

上一轮L-CTIPSTEP2已PASS并发布main bdadd1a：0.90 mm接受态最近距离0.138866582 mm，非工件介质minJ=0.129744609，介质maxabsHu=0.269497244/mm；右条带minJ=0.271604490，Hu较0.75 mm增长约2.89倍。原门、约束和平衡无矛盾。把下一请求增量缩至0.05 mm，是为了逐步观察更强压缩区间，不是增加新验收阈值；当前没有必须例行追加HP的证据。

来源为step002/run_001/wave_circle_tip_step2/result.json accepted1/global4、d=.90 mm，state SHA7dde449c7c36ed3963c2ee97616d706f08dff553426565b0c91007f4f4410ccf、signed R=.1580782308108174 N。保全部嵌套parent_continuation。完整task保[0,.25,.50,.75,.90]前缀，只append.95、更新input.target及四项说明身份；既有evaluate_native(saved_result=parent,selected_state_index=1,extend_path=True)先fresh F/T复核SHA/R和平衡，再执行suffix[.90,.95]。预期global4/5、child0/1，实际N随原内部二分全部保存；不重放旧前缀、不移植旧力/切线/矩阵。

r9 mm、圆心(80,40) mm固定ux/uy、右域界92 mm、Lr80 mm保持；92×40 mm下半域、h.5、厚20，E1 MPa、nu.3、plane strain、gamma1e-6、alpha5e-7、原支撑/端口/对称不变。顶部uy延至92，右ux及非顶uy自由。mechanical/chunk256/port_projection及全部非clock设置不变；原residual1e-9、平均约束系数1e-10及原scale、global balance1e-6、fixed split8e-11 mm、正J，maxchecks25/backtracks12/bisections4/mininc.00625保持。

拟唯一controller1800s、全部显示/收敛/表页共享600s、helper2700/outer2760s（最多46min），采样64 GiB、四库线程配置上限16，pure viewer原8 GiB子限。旧科学输入只限parent source_geometry/geometry.npz四掩码和accepted/001/state.npz的lift/fluctuation；执行前仅继承producer seal/stat，获批后唯一helper内才hash/decode，不读旧model/force/tangent/matrix数组或媒体。无新tests、HP或默认HF修改/安装。

成功后一次干净pure viewer读取新model27字段及每态split2/forces16，1+2N归档、27+18N字段；输出4PNG和实际N帧GIF，原收敛投影另1PNG，共5PNG。root每新PNG最多一次像素检查，不额外解码GIF。显示实际×1变形、R/qout、下半工件material/Hu/total有符号Fx/Fy、tip及完整Q1最近距离/见证/交叉/重叠、实体/介质J/Hu、右侧固定参考x89..92全部480cells J/Green/Hu及位置/split位移、原收敛记录。tip按唯一reference(80,30)查节点；完整镜像只用于显示，力不加倍；外角位移不当作tip间隙。右场统计覆盖80行，空间图上部裁剪另注明。

获批后绑定真实批准消息，重核最终授权记录和受影响SHA，再冻结并唯一启动。首终端错误停后续科学/显示并保真实partial；仅原窗口开放时允许部分seal；无外部重试、修复重跑、延期、force、回滚、删除。原内部回溯/二分允许。执行阶段拟包含结果/理由/实际效果/取舍与恢复记录、main普通推送和异路径local Git恢复核对，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

task_target_executed/full_original/full_extended不升级，new_peak/segment只指本段；保原父成功与失败历史。正距离及包含Hu的工件弱力不单独构成接触证明。无当前布局独立HP、连续压力、有效夹持、完整卸载/自由释放、稳定性、网格/域宽收敛或HF5资格。实际结果产生后才决定下一个目标或局部诊断。
