# L-CTIPUNLOAD1结果驱动的下一步：L-CTIPUNLOAD2

当前首次回程执行PASS、原生产门PASS、五张新PNG各一次实际QA PASS；38份63649599B原窗口封存，可按实际记录闭卡。

建议下一阶段 L-CTIPUNLOAD2：复用既有ordered_cycle保存态延伸API，从本次成功1.05 mm末态仅继续卸载至1.00 mm，保持峰值1.06和完整前缀、原物理/设置/验收门；沿用已验证LAST显示并以既有普通JSON对照旧加载1.00标量。当前回程无具体数值矛盾需要例行新增HP，先推进这一项功能。该新目标和资源窗口须新明确授权，本轮未实施/执行，不自动展开后续卸载。

首次回程完成且原严格门、五图实际QA均通过；target6次Newton检查、5次线搜索全接受、无拒绝/失败/二分。tip/full-Q1距离由9.887525增至13.434645微米，全介质minJ由0.0009015839179744192增至0.0032268105739974096，下半工件Fy由0.01259251473277105降至0.01034490624034115 N。旧同输入1.05的13项标量差异很小，但SHA不同且未设相等门；这些是点对照，不是完整可逆性或滞回结论。已有原峰值1.06独立参考不转授新1.05态，不过目前没有具体错误要求增加一轮参考审计；继续小段实际卸载更符合功能目标。

1. **精确父态。** 使用本卡`run_001/wave_circle_tip_unload1/result.json` accepted1/global13/child1/unloading1.05 mm，SHA `64b9301899b2599203140b634ffc5340e5d0a7c31ce75d0931203a6b72d58d1d`、signedR=0.1917119776052677 N；使用真实scientific result，不能改用旧加载1.05的0cef态或显示/HP summary。保原绝对lift/fluctuation/R和完整nested parent_continuation。
2. **同kind最小延伸。** task继续ordered_cycle，完整14目标前缀不变，仅append1.00：`[0,.25,.5,.75,.90,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06,1.05,1.00]`。input.target峰值仍1.06，其余只改四说明身份字段。复用已安装`evaluate_native(saved_result=上述result,selected_state_index=1,extend_path=True,time_limit_seconds=1800)`，fresh F/T复核1.05原SHA/有符号R和平衡，再走child[1.05,1.00]，global13/14、child-original0/1、resume_origin/unloading。不得重放前缀或移植旧力/切线/矩阵；新的同kind段不重复制造first_unload转换，原五键转换保在真实parent历史中。峰值仍是任务/祖先事实，不要求新child重新经过1.06或产生new_peak标志。
3. **原物理/设置/门。** r9/c(80,40)、right92/Lr80、h.5及材料、固定工件、边界/端口、mechanical/chunk256/port_projection和全部非clock设置原样，仅新clock复位。residual1e-9、原native约束bound、globalbalance1e-6、fixedsplit8e-11和J>0不改。minimum_increment=.00625；本次幅值.05可按原二分得到.025/.0125/.00625，后续.003125低于原下限则停止，仍受原max_bisections4约束。原内部线搜索/二分允许；不新增恢复、单调、相等或小J门。
4. **单次窗口与有限输入。** controller1800秒、viewer/收敛/表页共享600秒、helper2700/outer2760秒（最多46分钟），采样64GiB、四库线程上限16、viewer原8GiB子限。准备只继承producer seal/stat/普通描述；运行前向只读原geometry四mask和选中state lift/fluctuation两个旧科学输入，不读旧force/tangent/CSC/HP gzip或媒体。先完成研究包装与有限静审，再唯一启动；首terminal错误停止后续科学/显示并保真实partial，仅原新窗口内封存。无外部重试、修复重跑、延期、force、测试、新HP、默认HF修改/安装、API关联、回滚或删除。
5. **沿用实际LAST显示。** 复用本卡已验证研究viewer与原convergence投影：comparison为anchor与实际LAST，field/right-medium静态图明确显示LAST，peak_index仅保原元数据语义。成功后5PNG/实际N帧GIF、状态表和人工页；N与原内部二分的所有接受态依实际记录，不能只保原目标。显示实际×1变形、R/q_out、signed bodyFx/Fy material/Hu/total、tip/full-Q1距离及几何标志、实体/介质J/Hu、完整480cells右介质及原Newton/trial/二分。新PNG最多各一次实际检查；不解码旧媒体/GIF、不闭窗修图、不加第六图或例行局部定位。
6. **仅普通标量的同输入对照。** 新1.00卸载global14与已存在STEP6 summary row0/global7/1.00作相同13项原标量和差值的记录/表对照。来源`lf_circle_tip_step_006/run_001/view/wave_circle_tip_step6/summary.json`，rawleg仍resume_origin、保其继承加载来源，不改原SHA或以数值相等去重历史。旧R=0.1784535445979535 N、q_out=0.9524284255775324 mm、bodyFy=0.0057942001574207685 N、tip距离0.04968854162278191 mm、mediumminJ=0.03880995688549589。只读普通JSON，无旧数组/媒体/新科学调用或额外图；不要求相同state，不设路径无关/可逆/滞回验收。实际结果再决定下一段或排查，不自动执行其它目标。

记录总体目标、原因、完成内容、实际效果和限制，分别保执行/视觉QA/阶段完成；普通main推送和同机异目录local Git恢复，origin保持既有仓库。固定工件上的输入回撤不等于自由工件释放；unsigned Q1距离与弱式工件力不授连续压力/有效夹持资格。当前1.05新态HP0，原1.06选定参考范围不扩展；完整前缀/全路径参考、全列切线、稳定性、网格/域宽及HF5资格保持未完成。

L-CTIPUNLOAD2目前只是具体待授权方案，尚未实施/执行，不能沿用已关闭UNLOAD1窗口。
