# L-CTIPSTEP10：从1.05 mm保存态推进到1.06 mm

本轮用户明确批准“批准按 L-CTIPSTEP10 计划实施并执行”，依据main c3c8bb1的STEP9后续计划。整体目标是独立、可恢复的TMC大变形分析，逐步观察LF夹持器接近工件、结构变形和作用力；本卡只执行一个新加载目标。

起点为STEP9真实result.json，accepted1/global11/d1.05 mm、SHA 0cef15db4eb7d5537ce1047b1a8625013ab131edcaa3a88c15a7dfacbdf9bbe8、signed R=0.1917119776052685 N。使用既有evaluate_native(saved_result=..., selected_state_index=1, extend_path=True)，fresh锚F/T复核平衡与原SHA/有符号R；不读取旧力/切线/矩阵或把显示JSON当保存态。

完整前缀[0,.25,.5,.75,.9,.95,.98,1.00,1.02,1.03,1.04,1.05]仅append1.06、input.target改1.06与四项说明身份，其余task字段保持。child仅[1.05,1.06]、global11/12；完整parent_continuation保留，不重放旧前缀。

保持r9 mm、圆心(80,40) mm、工件ux/uy固定、right92 mm、Lr80 mm；下半域92×40 mm、h.5、厚20、E1 MPa、nu.3、plane strain、gamma1e-6、alpha5e-7与原支撑/端口/对称。mechanical/chunk256/port_projection、全部非clock设置及原残差/约束/平衡/固定位移/正J门保持。minimum_increment=.00625 mm；直接.01首次尝试允许，失败后半步.005低于原限值，按原控制器终端停止，不降低限值。

唯一启动：controller1800秒、viewer/收敛/表页共享600秒、helper2700/outer2760秒，采样64GiB、四库线程上限16，原viewer内部8GiB保持。首终端错误停止后续科学/显示，保真实partial，仅原窗口内封存；无外部重试、修复重跑、延期、force、回滚、删除、新HP、测试、力核修复、默认HF修改或安装。

成功后原pure viewer与收敛投影各一次，输出5PNG、实际N帧GIF、状态表与人工页。涵盖实际×1变形、R/qout、tip/完整Q1距离及几何标志、下半工件material/Hu/total有符号力、实体/介质J/Hu、右480cells见证与极值、原收敛/线搜索/二分。N以实际接受态为准；每张新PNG最多检查一次，不解码GIF或旧媒体。不追加每微步局部定位，不将旧1.04 mm全介质极值位置转授新态。

数值执行与像素QA分别记录，阶段完成以实际结果决定。记录目标、原因、完成内容、效果和限制；main普通推送及同机异目录local Git恢复核对，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。发布阶段科学/媒体/CSV身份只继承原窗口producer seal并核大小，不在窗口外重新读取/hash。

不升级全路径、当前布局独立参考、连续压力、有效夹持、卸载/自由释放、稳定性、网格/域宽或HF5资格；LOCAL1原视觉失败、LOCAL2修复及全部历史保留。本卡完成后再按真实结果决定下一步，不自动增加其它目标。
