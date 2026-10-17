L-CLOCAL1 有限实际审阅

结论：pass_actual_finite_review / execution_status=pass，无阻断。终端692cec/session13652/exit0（stdout899c79）；outer7.6218445s/helper5.4077653s，树RSS147718144B，SUP2清理通过。7source/8普通inputSHA、3旧NPZ原S4sealstat、默认src0diff核对通过；3archives/8fields、四个原标量exact、6输出membership/stat完整，未开载荷、CSV或图。

J为Simpson样本：唯一最低e10394/q2(-1,1)，J=.08623624515762662，reference与actual位置均(73,31)，恰等于原最近工件witness。same_cell=false不表示空间远离；该单元只共享原工件edge一个端点，并非整条面对边。最近机构witness仍为(73.006119,30.903862)，unsigned距.096332mm，不因固定工件角点同坐标就宣称接触。

Hu是单元常值：唯一最高cell10368，maxabs=.4160725051/mm，两个有符号混合分量ties均负；actual中心代表点(59.883545,30.783402)，与最近工件角点不同。J排名10samples、Hu排名10cells/20个component行（仅JSON记录，未读CSV）；exactties/阈值样本未混为独立Hu GP。全局最大Hu的位置不能直接解释净工件Hu合力的来源。

可考虑另卡1.35→1.40的小+.05，原门/物理/settings/资源不变：这次定位已澄清强压缩与固定阶梯角点的关系，并未发现点序或mask错配；但minJ仍很低，不保证收敛、稳定或接触，不盲推+.10。保留全prefix/实际二分态/首终态失败闭卡；不新增自动HP或改材料。此处只建议，未执行。

补充场语义：J=det(I+grad u)是局部一阶梯度的面积变化；Hu是相对参考坐标的位移二阶Hessian，Q1在这里保留mixed导数。不同指标的极值不要求同位。固定阶梯角点的压缩和左侧另一邻域更强的非仿射位移变化可以同时存在，位置不同本身不是核或数据错误证据。由于本次筛选是free-medium，e10368应称“左侧机构转角邻域的非工件介质单元”，不能称机构实体内极值；topHu还含e10562等工件阶梯邻域次高簇。净body HuFy是所有相关单元节点弱式项散射后在固定工件节点上的有符号求和，不能从全局最大Hu或top排名判定其来源，更不能将其约80%比例归因该单元。此语义澄清没有增加阻断；保原条件另卡+.05至1.40可以考虑，仍不保证收敛/接触。
